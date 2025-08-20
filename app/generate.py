import json
from typing import Dict, List, Optional
from openai import OpenAI
import google.generativeai as genai


class PostGenerator:
    def __init__(self, api_key: str, provider: str = "openai", model: Optional[str] = None):
        """
        provider: "openai" or "gemini"
        model: optional override for model (defaults set internally)
        """
        self.api_key = api_key
        self.provider = provider.lower()
        self.model = model or ("gpt-4o" if self.provider == "openai" else "gemini-2.5-pro")

        print(f"[INFO] Using provider: {provider}, model: {model}")

        if self.provider == "gemini":
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model)
        elif self.provider == "openai":
            self.client = OpenAI(api_key=self.api_key)
        else:
            raise ValueError("Provider must be 'openai' or 'gemini'")

    def _build_prompt(self, items: List[Dict]) -> str:
        instructions = (
            "You are a professional social media content editor for the technology industry.\n\n"

            "You will receive as input a list of article items. Each article item will have at least two fields: "
            "a title (the headline of the article) and a URL (the link to the article).\n\n"

            "Your job is to carefully review the list of articles and select ONLY ONE article that is the most valuable, "
            "most relevant, and most timely for professionals in the technology field. "
            "The audience includes software engineers, engineering leaders, CTOs, and technology decision-makers.\n\n"

            "When selecting the article, use the following rules:\n"
            "- Choose an article that is actionable, insightful, or directly relevant to current challenges or trends.\n"
            "- Prioritize topics related to software engineering, AI/ML, DevOps, cloud computing, developer productivity, "
            "or engineering leadership.\n"
            "- Do NOT choose articles that are clickbait, overly generic, outdated, or low-value.\n"
            "- Always ensure that the selected article provides useful takeaways for a professional tech audience.\n\n"

            "Once you have selected the single best article, your task is to generate TWO types of social media posts:\n\n"

            "1. A LinkedIn post:\n"
            "- Tone: professional, clear, informative (not hype or clickbait).\n"
            "- Length: 4 to 7 sentences.\n"
            "- Content:\n"
            "   * Summarize the article’s topic and explain why it is important for the tech community.\n"
            "   * Highlight the key takeaway or insight that engineers or leaders can apply.\n"
            "   * End with a clear takeaway, recommendation, or call to action.\n"
            "   * At the end of the post, include the source link on its own line, formatted as: Source: <url>\n"
            "   * On the next line, include 4 to 7 relevant hashtags (separated by spaces).\n"
            "- Avoid vague statements, filler, or overpromising. Focus on clarity and value.\n\n"

            "2. A post for X (formerly Twitter):\n"
            "- Length: maximum of 280 characters.\n"
            "- Tone: concise, punchy, and professional.\n"
            "- Content:\n"
            "   * Clearly explain why the article matters to developers or tech leaders.\n"
            "   * Be direct and value-driven (no hype or fluff).\n"
            "   * End with the article URL.\n"
            "   * On the next line, include 2 to 4 relevant hashtags.\n\n"

            "IMPORTANT:\n"
            "- You must output ONLY ONE result, not multiple.\n"
            "- You must return ONLY a valid JSON object (not an array, not plain text, not explanations).\n"
            "- The JSON object must have EXACTLY this structure:\n\n"

            "{\n"
            "  'source': string,   (always set this to the string 'linkedin_and_x_editor')\n"
            "  'title': string,    (the title of the chosen article)\n"
            "  'url': string,      (the URL of the chosen article)\n"
            "  'linkedin': string, (the LinkedIn post text you generated)\n"
            "  'x': string         (the X/Twitter post text you generated)\n"
            "}\n\n"

            "DO NOT return an array.\n" 
            "DO NOT return explanations.\n"
            "DO NOT add extra text outside the JSON object.\n"
            "DO NOT wrap the JSON object in code fences (``` or ```json)."
            "Return ONLY this single JSON object as the final output."
        )


        lines = [instructions, "Items:"]
        for idx, it in enumerate(items, start=1):
            title = (it.get("title") or "").strip()
            url = (it.get("url") or "").strip()
            source = (it.get("source") or "").strip()
            lines.append(f"{idx}. [{source}] {title} ({url})")
        return "\n".join(lines)

    def generate(self, items: List[Dict]) -> List[Dict]:
        if not items:
            return []

        if self.provider == "openai":
            return self._generate_openai(items)
        elif self.provider == "gemini":
            return self._generate_gemini(items)
        else:
            raise ValueError("Unsupported provider")
        
    def validate_generated_post(data: str):
        print(data)
        """
        Validate the generated post output.
        
        The output must strictly follow this structure:
        {
        'source': string,   (always set to 'linkedin_and_x_editor')
        'title': string,    (the title of the chosen article)
        'url': string,      (the URL of the chosen article)
        'linkedin': string, (the LinkedIn post text)
        'x': string         (the X/Twitter post text)
        }
        """

        required_fields = ["source", "title", "url", "linkedin", "x"]

        try:
            parsed = json.loads(data)

            # Check it is a dictionary (not array or text)
            if not isinstance(parsed, dict):
                return False, "Output must be a single JSON object, not an array or other type."

            # Check all required fields exist
            for field in required_fields:
                if field not in parsed:
                    return False, f"Missing required field: {field}"
                if not isinstance(parsed[field], str):
                    return False, f"Field '{field}' must be a string."

            # Validate fixed "source"
            if parsed["source"] != "linkedin_and_x_editor":
                return False, "Field 'source' must be exactly 'linkedin_and_x_editor'."

            return True, parsed

        except json.JSONDecodeError as e:
            return False, f"Invalid JSON format: {str(e)}"


    def _generate_openai(self, items: List[Dict]) -> List[Dict]:
        try:
            prompt = self._build_prompt(items)
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                response_format={"type": "json_object"},
            )
            content = resp.choices[0].message.content or "{}"

            # ✅ Validate JSON
            ok, result = PostGenerator.validate_generated_post(content)
            if not ok:
                print("⚠️ Validation failed (OpenAI):", result)
                return self._fallback(items)

            return [result]

        except Exception as e:
            print("⚠️ OpenAI error:", e)
            return self._fallback(items)

    def _generate_gemini(self, items: List[Dict]) -> List[Dict]:
        try:
            prompt = self._build_prompt(items)

            # ✅ Add generation config
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "max_output_tokens": 1024,
                "response_mime_type": "application/json"
            }

            resp = self.client.generate_content(
                prompt,
                generation_config=generation_config
            )

            # Extract text safely
            content = None
            if resp.candidates:
                for cand in resp.candidates:
                    if cand.content and cand.content.parts:
                        for part in cand.content.parts:
                            if hasattr(part, "text") and part.text:
                                content = part.text.strip()
                                break
                    if content:
                        break

            if not content:
                print("⚠️ No text content returned. Safety filters may have blocked the response.")
                return self._fallback(items)

            # ✅ Validate JSON
            ok, result = PostGenerator.validate_generated_post(content)
            if not ok:
                print("⚠️ Validation failed (Gemini):", result)
                return self._fallback(items)

            return [result]

        except Exception as e:
            print("⚠️ Gemini error:", e)
            return self._fallback(items)


    def _extract_results(self, data: Dict, items: List[Dict]) -> List[Dict]:
        results = data.get("results", [])
        output = []
        for gen in results[:1]:
            output.append({
                "source": gen.get("source", "").strip(),
                "title": gen.get("title", "").strip(),
                "url": gen.get("url", "").strip(),
                "linkedin": gen.get("linkedin", "").strip(),
                "x": gen.get("x", "").strip(),
            })
        return output

    def _fallback(self, items: List[Dict]) -> List[Dict]:
        """Fallback if API fails"""
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
