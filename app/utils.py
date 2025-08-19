from typing import List, Dict


def truncate_for_x(text: str, url: str, max_len: int = 280) -> str:
    # Reserve space for space + url
    reserve = len(url) + 1
    core_max = max_len - reserve
    core = text.strip()
    if len(core) > core_max:
        core = core[: max(0, core_max - 3)] + "..."
    return f"{core} {url}".strip()


def pick_top_items(items: List[Dict], max_items: int = 2) -> List[Dict]:
    # Items are expected to be pre-sorted by score/recency
    unique_urls = set()
    picked: List[Dict] = []
    for it in items:
        url = it.get("url")
        if not url or url in unique_urls:
            continue
        unique_urls.add(url)
        picked.append(it)
        if len(picked) >= max_items:
            break
    return picked
