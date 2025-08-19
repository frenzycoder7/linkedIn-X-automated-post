from typing import Optional, Tuple
import base64
import json
import requests

LINKEDIN_ME_ENDPOINT = "https://api.linkedin.com/v2/me"
LINKEDIN_USERINFO_ENDPOINTS = [
    "https://api.linkedin.com/v2/userinfo",
    "https://www.linkedin.com/oauth/v2/userinfo",
]


def _b64url_decode(segment: str) -> bytes:
    rem = len(segment) % 4
    if rem:
        segment += "=" * (4 - rem)
    return base64.urlsafe_b64decode(segment.encode("utf-8"))


def get_person_urn_from_id_token(id_token: str) -> Tuple[Optional[str], Optional[str]]:
    if not id_token or "." not in id_token:
        return None, "invalid id token"
    try:
        parts = id_token.split(".")
        if len(parts) < 2:
            return None, "invalid id token format"
        payload_bytes = _b64url_decode(parts[1])
        payload = json.loads(payload_bytes.decode("utf-8"))
        sub = payload.get("sub")
        if not sub:
            return None, "no sub in id token"
        return f"urn:li:person:{sub}", None
    except Exception as exc:
        return None, str(exc)


def get_person_urn(access_token: str) -> Tuple[Optional[str], Optional[str]]:
    if not access_token:
        return None, "missing access token"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    try:
        resp = requests.get(LINKEDIN_ME_ENDPOINT, headers=headers, timeout=20)
        if 200 <= resp.status_code < 300:
            data = resp.json()
            user_id = data.get("id")
            if not user_id:
                return None, "no id in response"
            return f"urn:li:person:{user_id}", None
        return None, f"LinkedIn /me error: {resp.status_code} {resp.text[:500]}"
    except Exception as exc:
        return None, str(exc)


def get_person_urn_from_userinfo(access_token: str) -> Tuple[Optional[str], Optional[str]]:
    if not access_token:
        return None, "missing access token"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    last_err: Optional[str] = None
    for url in LINKEDIN_USERINFO_ENDPOINTS:
        try:
            resp = requests.get(url, headers=headers, timeout=20)
            if 200 <= resp.status_code < 300:
                data = resp.json()
                sub = data.get("sub")
                if not sub:
                    last_err = "no sub in response"
                    continue
                return f"urn:li:person:{sub}", None
            last_err = f"LinkedIn userinfo error: {resp.status_code} {resp.text[:400]}"
        except Exception as exc:
            last_err = str(exc)
    return None, last_err or "userinfo request failed"


def resolve_person_urn(*, access_token: Optional[str], id_token: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    # 1) Try ID token (OIDC) to construct URN directly
    if id_token:
        urn, err = get_person_urn_from_id_token(id_token)
        if urn:
            return urn, None
        last_err = err
    else:
        last_err = None

    # 2) Try /v2/me
    if access_token:
        urn, err = get_person_urn(access_token)
        if urn:
            return urn, None
        last_err = err

        # 3) Fallback to userinfo
        urn, err = get_person_urn_from_userinfo(access_token)
        if urn:
            return urn, None
        last_err = err

    return None, last_err or "unable to resolve LinkedIn person URN"
