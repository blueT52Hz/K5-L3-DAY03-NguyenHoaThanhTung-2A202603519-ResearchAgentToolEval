from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, domain, err

# Algolia's public Hacker News API: no key, one request per call.
BASE_URL = "https://hn.algolia.com/api/v1"


def _limit(value: Any, default: int = 5) -> int:
    """Clamp model-provided limit (may arrive as str/0/negative) into 1..20."""
    try:
        return max(1, min(20, int(value)))
    except (TypeError, ValueError):
        return default


def hn_stories(query: str = "", sort: str = "top", limit: int = 5) -> dict[str, Any]:
    """Get Hacker News stories: front page (sort=top) or newest (sort=latest), optionally filtered by query."""
    try:
        sort = sort if sort in {"top", "latest"} else "top"
        n = _limit(limit)
        query = (query or "").strip()
        if sort == "latest":
            endpoint, tags = "search_by_date", "story"
        else:
            # No query -> today's front page; with query -> most relevant/popular stories.
            endpoint, tags = "search", ("story" if query else "front_page")
        params: dict[str, Any] = {"tags": tags, "hitsPerPage": n}
        if query:
            params["query"] = query
        response = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=TIMEOUT)
        response.raise_for_status()
        items = []
        for hit in response.json().get("hits", [])[:n]:
            hn_url = f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
            url = hit.get("url") or hn_url  # Ask HN / Show HN posts have no external url
            items.append({
                "title": hit.get("title"),
                "url": url,
                "source": domain(url),
                "points": hit.get("points"),
                "comments": hit.get("num_comments"),
                "author": hit.get("author"),
                "created_at": hit.get("created_at"),
                "hn_url": hn_url,
            })
        return {"tool": "hackernews", "query": query, "sort": sort, "items": items}
    except Exception as exc:
        return err("hackernews", exc)
