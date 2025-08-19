from typing import Optional, Tuple

try:
    import tweepy
except Exception:  # pragma: no cover
    tweepy = None  # type: ignore

import requests


def post_x_oauth1(
    *,
    api_key: str,
    api_secret: str,
    access_token: str,
    access_token_secret: str,
    text: str,
) -> Tuple[bool, Optional[str]]:
    if tweepy is None:
        return False, "tweepy not available"

    try:
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            wait_on_rate_limit=True,
        )
        resp = client.create_tweet(text=text)
        if getattr(resp, "errors", None):
            return False, str(resp.errors)
        return True, None
    except Exception as exc:
        return False, str(exc)


def post_x_oauth2(
    *,
    access_token: str,
    text: str,
) -> Tuple[bool, Optional[str]]:
    # Twitter v2 create tweet with OAuth2 user context token (requires tweet.write scope)
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        body = {"text": text}
        resp = requests.post("https://api.twitter.com/2/tweets", headers=headers, json=body, timeout=20)
        if 200 <= resp.status_code < 300:
            return True, None
        return False, f"X error: {resp.status_code} {resp.text[:500]}"
    except Exception as exc:
        return False, str(exc)


def post_x(
    *,
    text: str,
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None,
    access_token: Optional[str] = None,
    access_token_secret: Optional[str] = None,
    oauth2_access_token: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    # Prefer OAuth1 if fully configured, else fallback to OAuth2 user token
    if api_key and api_secret and access_token and access_token_secret:
        return post_x_oauth1(
            api_key=api_key,
            api_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            text=text,
        )
    if oauth2_access_token:
        return post_x_oauth2(access_token=oauth2_access_token, text=text)
    return False, "no valid X credentials found (need OAuth1 keys or OAuth2 user access token)"
