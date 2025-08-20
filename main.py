import argparse
from datetime import datetime
from typing import List, Dict, Optional

from app.config import read_config
from app.db_mongo import (
    initialize_database,
    has_been_posted,
    record_post,
    exists_record,
)
from app.fetch_reddit import fetch_reddit_items
from app.fetch_x import fetch_x_items
from app.generate import  PostGenerator
from app.post_linkedin import post_linkedin
from app.post_x import post_x
from app.utils import truncate_for_x



def run_once(*, override_items: Optional[List[Dict]] = None) -> None:
    cfg = read_config()
    initialize_database()

    # Collect items from sources with rate-limit-aware fallback
    items: List[Dict] = []
    if override_items is not None:
        items = list(override_items)
    else:
        x_rate_limited = False
        if cfg.x_bearer_token:
            x_items, x_rate_limited = fetch_x_items(bearer_token=cfg.x_bearer_token, keywords=cfg.keywords, max_results=3)
            items += x_items
        if cfg.reddit_client_id and cfg.reddit_client_secret and cfg.reddit_user_agent:
            # If X was rate-limited or returned nothing, try Reddit
            if x_rate_limited or not items:
                r_items, r_rate_limited = fetch_reddit_items(
                    client_id=cfg.reddit_client_id,
                    client_secret=cfg.reddit_client_secret,
                    user_agent=cfg.reddit_user_agent,
                    keywords=cfg.keywords,
                    limit_per_subreddit=20,
                )
                items += r_items

    if not items:
        print("No items fetched.")
        return

    # Generate posts from all items; model will pick top one
    
    if cfg.gemini_api_key:
        provider = "gemini"
        api_key = cfg.gemini_api_key
        model = cfg.gemini_model
    elif cfg.openai_api_key:
        provider = "openai"
        api_key = cfg.openai_api_key
        model = cfg.openai_model
    else:
        raise ValueError("No API key found for Gemini or OpenAI")

    generator = PostGenerator(api_key=api_key, provider=provider, model=model)
    posts = generator.generate(items=items)

    # Post and log
    for gen in posts:
        url = gen.get("url") or ""
        title = gen.get("title") or ""

        # LinkedIn
        if cfg.linkedin_access_token:
            if not has_been_posted("linkedin", url):
                text = gen.get("linkedin") or f"{title}\n\n{url}"
                success, error = post_linkedin(
                    access_token=cfg.linkedin_access_token, 
                    text=text, 
                    url=url, 
                    title=title
                )
                record_post(
                    platform="linkedin",
                    source=gen.get("source") or "",
                    source_url=url,
                    title=title,
                    linkedin_text=text,
                    x_text=None,
                    success=success,
                    error=error,
                    posted_at=datetime.utcnow() if success else None,
                )
        else:
            # Queue as pending if not already recorded
            text = gen.get("linkedin") or f"{title}\n\n{url}"
            if not exists_record(platform="linkedin", source_url=url):
                record_post(
                    platform="linkedin",
                    source=gen.get("source") or "",
                    source_url=url,
                    title=title,
                    linkedin_text=text,
                    x_text=None,
                    success=False,
                    error="pending: missing LinkedIn credentials",
                    posted_at=None,
                )

        # X
        has_oauth1 = bool(cfg.x_api_key and cfg.x_api_secret and cfg.x_access_token and cfg.x_access_token_secret)
        has_oauth2 = bool(cfg.x_oauth2_access_token)
        if has_oauth1 or has_oauth2:
            if not has_been_posted("x", url):
                x_text = gen.get("x") or truncate_for_x(title, url)
                success, error = post_x(
                    text=x_text,
                    api_key=cfg.x_api_key,
                    api_secret=cfg.x_api_secret,
                    access_token=cfg.x_access_token,
                    access_token_secret=cfg.x_access_token_secret,
                    oauth2_access_token=cfg.x_oauth2_access_token,
                )
                record_post(
                    platform="x",
                    source=gen.get("source") or "",
                    source_url=url,
                    title=title,
                    linkedin_text=None,
                    x_text=x_text,
                    success=success,
                    error=error,
                    posted_at=datetime.utcnow() if success else None,
                )
        else:
            # Queue as pending if not already recorded
            x_text = gen.get("x") or truncate_for_x(title, url)
            if not exists_record(platform="x", source_url=url):
                record_post(
                    platform="x",
                    source=gen.get("source") or "",
                    source_url=url,
                    title=title,
                    linkedin_text=None,
                    x_text=x_text,
                    success=False,
                    error="pending: missing X credentials",
                    posted_at=None,
                )


if __name__ == "__main__":
    run_once()
