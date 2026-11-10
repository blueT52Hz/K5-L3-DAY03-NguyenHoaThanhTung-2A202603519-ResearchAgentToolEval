"""Code-level guardrail for irreversible action tools (e.g. `send` to Telegram).

Why: live chat showed the model chaining `format` -> `send(confirmed=true)` in ONE turn,
i.e. it set confirmed=true by itself without asking the user. Prompt rules alone are not
enough for irreversible actions, so the agent loop enforces this rule in code:

    A tool whose TOOL.md has `requires_confirmation: true` may run with confirmed=true ONLY
    if, in the previous turn, the agent asked a yes/no question and the user answered yes.

Otherwise the call is NOT executed and the loop pauses with a yes/no confirmation question.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

TOOLS_DIR = Path(__file__).parent / "tools"

# Vietnamese + English yes/no. Negation wins ("không, đừng đăng" is a no).
_AFFIRM = re.compile(r"\b(có|co|yes|ok|okay|oke|đồng ý|dong y|xác nhận|xac nhan|chắc chắn|đăng đi|gửi đi|đăng luôn|gửi luôn)\b", re.I)
_NEGATE = re.compile(r"\b(không|khong|đừng|dung|thôi|thoi|no|hủy|huỷ|huy|khoan)\b", re.I)


def tools_requiring_confirmation(tools_dir: Path = TOOLS_DIR) -> set[str]:
    """Tool names whose TOOL.md frontmatter declares `requires_confirmation: true` (rename-proof)."""
    names: set[str] = set()
    for md in tools_dir.glob("*/TOOL.md"):
        raw = md.read_text(encoding="utf-8")
        if not raw.startswith("---"):
            continue
        try:
            meta = yaml.safe_load(raw.split("---", 2)[1]) or {}
        except yaml.YAMLError:
            continue
        if meta.get("requires_confirmation") is True and meta.get("name"):
            names.add(str(meta["name"]))
    return names


def is_affirmative(text: str) -> bool:
    text = (text or "").strip()
    return bool(_AFFIRM.search(text)) and not _NEGATE.search(text)


def asked_yes_no(loop_result: dict[str, Any] | None) -> bool:
    """True if a run_model_tool_loop result paused on a yes/no question (clarify or guardrail)."""
    if not loop_result or loop_result.get("status") != "waiting_for_user":
        return False
    events = loop_result.get("tool_events") or []
    last = events[-1].get("result", {}) if events else {}
    return isinstance(last, dict) and last.get("response_type") == "yes_no"


def wants_confirmed_action(call_name: str, args: dict[str, Any], guarded: set[str]) -> bool:
    """True if this call would perform a guarded action (confirmed=true, also as string 'true')."""
    return call_name in guarded and str(args.get("confirmed", "")).strip().lower() in {"true", "1", "yes"}


def blocked_event(call_name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Event returned instead of executing: pauses the loop with a yes/no question (awaiting_user)."""
    preview = str(args.get("text", ""))[:600]
    question = (
        "Mình sẽ đăng nội dung sau lên Telegram:\n\n"
        f"{preview}\n\n"
        "Bạn có xác nhận đăng không? (có / không)"
    )
    return {
        "tool": call_name,
        "args": args,
        "result": {
            "status": "blocked_by_guardrail",
            "reason": "confirmed=true without an explicit user yes in the previous turn",
            "question": question,
            "response_type": "yes_no",
            "awaiting_user": True,
        },
    }
