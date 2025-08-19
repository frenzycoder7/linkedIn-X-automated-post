from typing import List, Dict, Tuple

try:
    import tweepy
    from tweepy.errors import TooManyRequests as TweepyTooManyRequests  # type: ignore
except Exception:  # pragma: no cover
    tweepy = None  # type: ignore
    TweepyTooManyRequests = None  # type: ignore


MAX_QUERY_LEN = 256
MIN_KEYWORDS = 3
FALLBACK_KEYWORDS = ["ai", "openai", "nvidia", "microsoft", "google"]


def dedupe_preserve_order(items: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for x in items:
        xl = x.strip().lower()
        if not xl or xl in seen:
            continue
        seen.add(xl)
        out.append(x)
    return out


def build_search_query(keywords: List[str]) -> str:
    # Combine with OR, restrict to English, exclude retweets
    ors = " OR ".join(f"\"{k}\"" if " " in k else k for k in keywords)
    return f"({ors}) lang:en -is:retweet"


def trim_keywords_for_limit(keywords: List[str]) -> List[str]:
    if not keywords:
        return keywords
    low = 1
    high = len(keywords)
    best = 1
    while low <= high:
        mid = (low + high) // 2
        q = build_search_query(keywords[:mid])
        if len(q) <= MAX_QUERY_LEN:
            best = mid
            low = mid + 1
        else:
            high = mid - 1
    best = max(best, MIN_KEYWORDS)
    return keywords[:best]


def _search(client, query: str, max_results: int):
    return client.search_recent_tweets(
        query=query,
        max_results=min(max_results, 100),
        tweet_fields=["created_at", "public_metrics", "lang"],
    )


def fetch_x_items(*, bearer_token: str, keywords: List[str], max_results: int = 3) -> Tuple[List[Dict], bool]:
    if tweepy is None:
        print("[X] Tweepy not available; skipping X fetch")
        return [], False

    try:
        client = tweepy.Client(bearer_token=bearer_token, wait_on_rate_limit=False)
        base_keywords = dedupe_preserve_order(keywords)
        # Progressive attempts: trimmed, half, minimal fallback
        attempts: List[List[str]] = []
        trimmed = trim_keywords_for_limit(base_keywords)
        attempts.append(trimmed)
        if len(trimmed) > MIN_KEYWORDS:
            attempts.append(trimmed[: max(MIN_KEYWORDS, len(trimmed) // 2)])
        attempts.append(FALLBACK_KEYWORDS)

        last_error = None
        for kws in attempts:
            if not kws:
                continue
            query = build_search_query(kws)
            try:
                resp = _search(client, query, max_results)
                items: List[Dict] = []
                for tweet in resp.data or []:
                    text = tweet.text or ""
                    metrics = tweet.public_metrics or {}
                    items.append(
                        {
                            "source": "x",
                            "title": text,
                            "url": f"https://twitter.com/i/web/status/{tweet.id}",
                            "created_at": str(getattr(tweet, "created_at", "")),
                            "score": int(metrics.get("like_count", 0)) + int(metrics.get("retweet_count", 0)),
                        }
                    )
                items.sort(key=lambda d: d.get("created_at", ""), reverse=True)
                if items:
                    return items[:3], False
                else:
                    last_error = "empty"
            except Exception as sub_exc:
                msg = str(sub_exc)
                last_error = msg
                if TweepyTooManyRequests is not None and isinstance(sub_exc, TweepyTooManyRequests):
                    print("[X] Rate limited by X API; will fallback to Reddit")
                    return [], True
                if "403" in msg or "Forbidden" in msg:
                    print("[X] Forbidden: your app may lack search permissions or access level")
                    break
                if "401" in msg or "Unauthorized" in msg:
                    print("[X] Unauthorized: check X_BEARER_TOKEN")
                    break
                if "400" in msg or "Bad Request" in msg:
                    print("[X] Bad request: trimming keywords and retrying")
                    continue
                print(f"[X] Error: {msg}")
                continue
        if last_error == "empty":
            print("[X] search returned no results for provided keywords")
        return [], False
    except Exception as exc:
        msg = str(exc)
        if TweepyTooManyRequests is not None and isinstance(exc, TweepyTooManyRequests):
            print("[X] Rate limited by X API; will fallback to Reddit")
            return [], True
        print(f"[X] Error fetching tweets: {msg}")
        return [], False
