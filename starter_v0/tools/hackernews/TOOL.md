---
name: hackernews
track: bonus
kind: live_api
provider: Hacker News Algolia API (no key)
requires_env: []
inputs: [query, sort, limit]
outputs: [items]
side_effect: false
---
# hackernews

Gets Hacker News stories through `https://hn.algolia.com/api/v1`.

- `sort=top` + no query: today's front page. `sort=top` + query: most relevant stories.
- `sort=latest`: newest stories (`search_by_date`), optionally filtered by query.
- `limit` is clamped to 1..20; strings like `"5"` are accepted.
- Ask HN / Show HN posts without an external link use the HN discussion URL.
- Errors return an error dict, never raise.