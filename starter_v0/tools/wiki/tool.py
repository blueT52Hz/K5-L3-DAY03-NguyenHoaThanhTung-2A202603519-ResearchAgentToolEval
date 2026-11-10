from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests

from tools._shared import TIMEOUT, err

# Wikipedia asks API clients to send a descriptive User-Agent.
USER_AGENT = "ResearchAgentLab/1.0 (educational lab; python-requests)"
LANGS = {"vi", "en"}


def wiki_summary(title: str = "", lang: str = "vi") -> dict[str, Any]:
    """Return the lead summary of one Wikipedia article (concept, person, company...)."""
    try:
        title = (title or "").strip()
        if not title:
            return {"tool": "wiki", "error": "ValueError", "message": "title must be a non-empty string"}
        lang = lang if lang in LANGS else "vi"  # out-of-enum value from the model -> safe default
        url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{quote(title.replace(' ', '_'), safe='')}"
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, params={"redirect": "true"}, timeout=TIMEOUT)
        if response.status_code == 404:
            return {"tool": "wiki", "title": title, "lang": lang, "found": False,
                    "message": "No Wikipedia article with this title. Try another title/language or use lookup."}
        response.raise_for_status()
        data = response.json()
        return {
            "tool": "wiki",
            "found": True,
            "lang": lang,
            "title": data.get("title", title),
            "description": data.get("description", ""),
            "summary": data.get("extract", ""),
            "url": (data.get("content_urls") or {}).get("desktop", {}).get("page", ""),
            "is_disambiguation": data.get("type") == "disambiguation",
        }
    except Exception as exc:
        return err("wiki", exc)