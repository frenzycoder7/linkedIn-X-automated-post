import os
import base64
import hashlib
import secrets
import urllib.parse
from typing import Dict, Tuple, Optional

import requests

AUTH_URL = "https://twitter.com/i/oauth2/authorize"
TOKEN_URL = "https://api.twitter.com/2/oauth2/token"

RECOMMENDED_SCOPES = [
    "tweet.read",
    "tweet.write",
    "users.read",
    "offline.access",
]


def _b64url(input_bytes: bytes) -> str:
    return base64.urlsafe_b64encode(input_bytes).decode("utf-8").rstrip("=")


def generate_pkce_pair() -> Tuple[str, str]:
    verifier = _b64url(secrets.token_bytes(32))
    sha = hashlib.sha256(verifier.encode("utf-8")).digest()
    challenge = _b64url(sha)
    return verifier, challenge


def build_authorize_url(
    *,
    client_id: str,
    redirect_uri: str,
    scopes: Optional[str] = None,
    state: Optional[str] = None,
) -> Tuple[str, str]:
    verifier, challenge = generate_pkce_pair()
    scope_str = scopes or " ".join(RECOMMENDED_SCOPES)
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope_str,
        "state": state or _b64url(secrets.token_bytes(8)),
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return url, verifier


def exchange_code_for_token(
    *,
    client_id: str,
    client_secret: Optional[str],
    redirect_uri: str,
    code: str,
    code_verifier: str,
) -> Dict:
    data = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "code": code,
        "code_verifier": code_verifier,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    auth = None
    if client_secret:
        # Confidential client: use Basic auth
        auth = (client_id, client_secret)

    resp = requests.post(TOKEN_URL, data=data, headers=headers, auth=auth, timeout=30)
    resp.raise_for_status()
    return resp.json()


def refresh_access_token(
    *,
    client_id: str,
    client_secret: Optional[str],
    refresh_token: str,
) -> Dict:
    data = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "refresh_token": refresh_token,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    auth = None
    if client_secret:
        auth = (client_id, client_secret)

    resp = requests.post(TOKEN_URL, data=data, headers=headers, auth=auth, timeout=30)
    resp.raise_for_status()
    return resp.json()
