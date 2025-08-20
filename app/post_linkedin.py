from typing import Optional, Tuple
import os
import requests
from app.linkedin_api import resolve_person_urn

LINKEDIN_UGC_ENDPOINT = "https://api.linkedin.com/v2/ugcPosts"


def post_linkedin(
    *,
    access_token: str,
    text: str,
    author_urn: Optional[str] = None,
    url: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    visibility: str = "PUBLIC",
) -> Tuple[bool, Optional[str]]:
    print(f"Posting on linkedIn")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    }

    # Resolve author_urn if not provided
    resolved_urn = author_urn

    if not resolved_urn:
        id_token = os.getenv("LINKEDIN_ID_TOKEN")
        resolved_urn, err = resolve_person_urn(access_token=access_token, id_token=id_token)
        if not resolved_urn:
            return False, err or "unable to resolve LinkedIn person URN"

    share_content = {
        "shareCommentary": {"text": text},
        "shareMediaCategory": "NONE",
    }

    if url:
        media_entry = {"status": "READY", "originalUrl": url}
        if title:
            media_entry["title"] = {"text": title}
        if description:
            media_entry["description"] = {"text": description}
        share_content["shareMediaCategory"] = "ARTICLE"
        share_content["media"] = [media_entry]

    body = {
        "author": resolved_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": share_content
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": visibility},
    }

    print(body)

    try:
        resp = requests.post(LINKEDIN_UGC_ENDPOINT, headers=headers, json=body, timeout=20)
        if 200 <= resp.status_code < 300:
            return True, None
        return False, f"LinkedIn error: {resp.status_code} {resp.text[:500]}"
    except Exception as exc:
        print(exc);
        return False, str(exc)
