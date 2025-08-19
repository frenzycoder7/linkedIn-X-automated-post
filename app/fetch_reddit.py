from typing import Iterable, List, Dict, Optional, Tuple
import os
import time

try:
    import praw
    from prawcore.exceptions import TooManyRequests as PrawTooManyRequests  # type: ignore
except Exception:  # pragma: no cover
    praw = None  # type: ignore
    PrawTooManyRequests = None  # type: ignore


DEFAULT_SUBREDDITS = [
    "technology",
    "MachineLearning",
    "OpenAI",
    "programming",
    "Futurology",
    "ArtificialIntelligence",
    "learnmachinelearning",
    "programmerhumor",
    "dataengineering",
    "devops",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "googlecloud",
    "cpp",
    "golang",
    "rust",
    "python",
    "javascript",
    "ai",
    "ai agents",
    "ai agent",
    "ai agentic",
    "ai agentic systems",
    "ai agentic systems engineering",
    "ai agentic systems engineering",
    "go",
    "golang",
    "rust",
    "python",
    "javascript",
    "typescript",
    "node.js",
    "react",
    "next.js",
    "vue",
    "svelte",
    "go",
    "golang",
    "rust",
    "python",
    "javascript",
    "typescript",
    "node.js",
    "react",
]


def _keyword_in_text(text: str, keywords: List[str]) -> bool:
    lowered = text.lower()
    return any(k.lower() in lowered for k in keywords)


def fetch_reddit_items(
    *,
    client_id: str,
    client_secret: str,
    user_agent: str,
    keywords: List[str],
    limit_per_subreddit: int = 20,
    subreddits: Optional[List[str]] = None,
) -> Tuple[List[Dict], bool]:
    if praw is None:
        return [], False

    subs = subreddits or DEFAULT_SUBREDDITS

    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )

        items: List[Dict] = []
        for sub in subs:
            try:
                subreddit = reddit.subreddit(sub)
                for submission in subreddit.hot(limit=limit_per_subreddit):
                    title = submission.title or ""
                    url = submission.url or ""
                    selftext = submission.selftext or ""
                    fulltext = f"{title}\n\n{selftext}"
                    if not _keyword_in_text(fulltext, keywords):
                        continue
                    items.append(
                        {
                            "source": "reddit",
                            "subreddit": sub,
                            "title": title,
                            "url": url or f"https://www.reddit.com{submission.permalink}",
                            "created_utc": getattr(submission, "created_utc", time.time()),
                            "score": getattr(submission, "score", 0),
                        }
                    )
            except Exception:
                continue

        # sort by score then recency
        items.sort(key=lambda d: (d.get("score", 0), d.get("created_utc", 0)), reverse=True)
        return items, False
    except Exception as exc:
        msg = str(exc)
        if PrawTooManyRequests is not None and isinstance(exc, PrawTooManyRequests):
            return [], True
        if "429" in msg or "Too Many Requests" in msg or "rate limit" in msg.lower():
            return [], True
        return [], False
