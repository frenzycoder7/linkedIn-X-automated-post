import json
from typing import Dict, List, Optional
from openai import OpenAI


DEFAULT_MODEL = "gpt-4o"


def _build_prompt(items: List[Dict]) -> str:
    instructions = (
        "You are a professional social media editor for the tech industry. You are given a list of article items, each with a title and URL.\n\n"
        "Your task is to carefully evaluate the list and identify the ONE most valuable and timely articles for software engineers, engineering leaders, or technology decision-makers.\n"
        "Choose only items that are actionable, insightful, or highly relevant to current challenges or trends in software, AI, DevOps, cloud, or engineering productivity.\n"
        "Ignore articles that are clickbait, overly generic, outdated, or low-value.\n\n"
        "For each of the selected item, generate:\n\n"
        "1. A LinkedIn post:\n"
        "   - Use a professional, informative tone.\n"
        "   - Write 4–7 clear, concise sentences.\n"
        "   - Explain why the topic is important and how it impacts the tech community.\n"
        "   - Include a clear takeaway or call to action.\n"
        "   - Add the source link on its own line prefixed with 'Source:'.\n"
        "   - Then, on a new line, include 4–7 relevant hashtags (space-separated).\n"
        "   - Avoid hype, buzzwords, and fluff. Focus on clarity and substance.\n\n"
        "2. A post for X (formerly Twitter):\n"
        "   - Max 280 characters.\n"
        "   - Use a concise, punchy tone that emphasizes value.\n"
        "   - Clearly state why the content matters to developers or tech leaders.\n"
        "   - End with the article URL.\n"
        "   - Then, on a new line, include 2–4 space-separated hashtags.\n\n"
        "Return a strict JSON object with an array named 'results', containing exactly one object with this structure:\n"
        "{ 'title': string, 'url': string, 'linkedin': string, 'x': string }\n"
    )

    lines = [instructions, "Items:"]
    for idx, it in enumerate(items, start=1):
        title = (it.get("title") or "").strip()
        url = (it.get("url") or "").strip()
        source = (it.get("source") or "").strip()
        lines.append(f"{idx}. [{source}] {title} ({url})")
    return "\n".join(lines)


def generate_posts(
    *,
    api_key: str,
    items: List[Dict],
    model: Optional[str] = None,
) -> List[Dict]:
    if not items:
        return []

    try:
        client = OpenAI(api_key=api_key)
        prompt = _build_prompt(items)
        resp = client.chat.completions.create(
            model=model or DEFAULT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content or "{}"
        data = json.loads(content)
        results = data.get("results", [])
        output: List[Dict] = []
        for gen in results[:1]:
            output.append(
                {
                    "source": gen.get("source") or "",
                    "title": (gen.get("title") or "").strip(),
                    "url": (gen.get("url") or "").strip(),
                    "linkedin": (gen.get("linkedin") or "").strip(),
                    "x": (gen.get("x") or "").strip(),
                }
            )
        if output:
            return output
    except Exception:
        pass

    # Fallback: choose first input and template
    first = items[0]
    title = (first.get("title") or "").strip()
    url = (first.get("url") or "").strip()
    linkedin = (
        f"{title}\n\nWhy it matters: Practical impact for engineers and teams.\n"
        f"Source: {url}\n\n#AI #Tech #Software #DevOps #Cloud"
    )
    xtweet_core = f"{title} — why it matters for builders."
    if len(xtweet_core) > 220:
        xtweet_core = xtweet_core[:217] + "..."
    xtweet = f"{xtweet_core} {url}\n#AI #Tech"
    return [
        {
            "source": first.get("source") or "",
            "title": title,
            "url": url,
            "linkedin": linkedin,
            "x": xtweet,
        }
    ]
