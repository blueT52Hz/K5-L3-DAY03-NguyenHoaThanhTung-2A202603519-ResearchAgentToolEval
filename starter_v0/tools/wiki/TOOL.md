---
name: wiki
track: bonus
kind: live_api
provider: Wikipedia REST API (no key)
requires_env: []
inputs: [title, lang]
outputs: [found, title, description, summary, url, is_disambiguation]
side_effect: false
---
# wiki

Returns the lead summary of one Wikipedia article via
`https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}`.

- Use for stable background knowledge: what a concept is ("Transformer là gì"),
  who a person/company is. Not for news (use `lookup`).
- `lang`: `vi` (default) or `en`; any other value falls back to `vi`.
- 404 is not an error: returns `found=false` so the model can retry or use `lookup`.
- Errors (HTTP 5xx, timeout) return an error dict, never raise.
