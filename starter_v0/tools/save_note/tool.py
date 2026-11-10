from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from tools._shared import ROOT, err, fold_text

# All notes live in this folder. Tests monkeypatch it to a tmp dir.
NOTES_DIR = ROOT / "notes"
MAX_CHARS = 50_000


def _slug(title: str) -> str:
    """Vietnamese-safe filename: fold accents, keep [a-z0-9-]. Blocks '../' path traversal by construction."""
    slug = re.sub(r"[^a-z0-9]+", "-", fold_text(title).replace("đ", "d")).strip("-")
    return slug[:60] or "note"


def save_markdown_note(title: str = "", content: str = "", overwrite: bool = False) -> dict[str, Any]:
    """Save research results as notes/<slug>.md. Never overwrites unless overwrite=true."""
    try:
        title, content = (title or "").strip(), content or ""
        if not title or not content.strip():
            return {"tool": "save_note", "error": "ValueError", "message": "title and content must be non-empty"}
        if len(content) > MAX_CHARS:
            return {"tool": "save_note", "error": "ValueError", "message": f"content longer than {MAX_CHARS} chars"}
        NOTES_DIR.mkdir(parents=True, exist_ok=True)
        base = _slug(title)
        path = NOTES_DIR / f"{base}.md"
        if not overwrite:
            i = 2
            while path.exists():  # keep old note, write note-2.md, note-3.md...
                path = NOTES_DIR / f"{base}-{i}.md"
                i += 1
        # Defence in depth: the resolved path must stay inside NOTES_DIR.
        if NOTES_DIR.resolve() not in path.resolve().parents:
            raise PermissionError("Refusing to write outside notes/")
        stamp = datetime.now().isoformat(timespec="seconds")
        path.write_text(f"# {title}\n\n_Saved: {stamp}_\n\n{content.strip()}\n", encoding="utf-8")
        return {"tool": "save_note", "status": "saved", "path": path.relative_to(NOTES_DIR.parent).as_posix(),
                "chars": len(content)}
    except Exception as exc:
        return err("save_note", exc)
