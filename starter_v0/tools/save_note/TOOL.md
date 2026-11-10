---
name: save_note
track: bonus
kind: action
provider: none (local filesystem)
requires_env: []
inputs: [title, content, overwrite]
outputs: [status, path, chars]
side_effect: local_file_write
---
# save_note

Saves markdown content (a digest, a summary) to `notes/<slug>.md` inside `starter_v0/`.

- Filename is a slug of the title (accents folded, only `a-z0-9-`), so `../` or
  absolute paths cannot escape `notes/`; the resolved path is checked again before writing.
- Never overwrites by default: an existing note is kept and `<slug>-2.md` is written.
- Local-only side effect (no external publish), so no confirmation step; external
  publishing still goes through `send` + confirmation.
- Empty title/content or content > 50k chars returns an error dict, never raises.