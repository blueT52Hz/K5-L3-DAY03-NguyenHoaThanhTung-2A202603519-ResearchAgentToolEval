"""Streamlit demo UI for the Research Agent.

Run from starter_v0/:
    streamlit run app.py            # -> http://localhost:8501

Reuses the exact same agent loop as chat.py (run_model_tool_loop), so behaviour in
the UI == behaviour in the CLI, and every turn is logged to transcripts/*.transcript.json.
"""
from __future__ import annotations

import csv
import glob
import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from chat import (
    ARTIFACTS_DIR,
    ROOT,
    now_iso,
    run_model_tool_loop,
    safe_slug,
    trim_history,
    write_transcript,
)
from confirmation_guard import is_affirmative
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

PROVIDERS = ["openrouter", "openai", "anthropic", "gemini", "ollama"]
TRANSCRIPTS_DIR = ROOT / "transcripts"

SAMPLE_QUESTIONS = [
    "Tweet mới nhất của Sam Altman là gì?",
    "Mọi người đang bàn gì về GPT-5 trên Twitter?",
    "Tin tức AI hôm nay có gì nổi bật?",
    "Tóm tắt bài này giúp mình: https://www.anthropic.com/research",
    "Tìm paper arXiv mới về AI agent evaluation.",
    "Theo policy công ty, tweet viral có được coi là fact đã xác nhận không?",
    "Tóm tắt 5 tweet mới nhất giúp mình",
    "Đăng bản tin này lên Telegram giúp mình",
]

st.set_page_config(page_title="Research Agent", layout="centered")

# ---------------------------------------------------------------- chatbot-style CSS
# User messages: right-aligned bubble, no avatar. Assistant messages: left, plain.
# A hidden marker <span class="msg-user"> inside each user message lets CSS target it.
st.markdown(
    """
<style>
[data-testid="stMainBlockContainer"], .block-container { max-width: 820px; padding-top: 2rem; padding-bottom: 7rem; }

/* hide the marker's own element container */
[data-testid="stElementContainer"]:has(.msg-user),
.element-container:has(.msg-user) { display: none; }

/* every chat row: transparent, a bit of spacing */
[data-testid="stChatMessage"] { background: transparent; padding: 0.35rem 0; gap: 0.75rem; }

/* USER row -> right side bubble, avatar hidden */
[data-testid="stChatMessage"]:has(.msg-user) { flex-direction: row-reverse; }
[data-testid="stChatMessage"]:has(.msg-user) [data-testid^="stChatMessageAvatar"] { display: none; }
[data-testid="stChatMessage"]:has(.msg-user) [data-testid="stChatMessageContent"] {
    flex: 0 1 auto; max-width: 78%; margin-left: auto;
    background: rgba(128, 128, 128, 0.14);
    border-radius: 20px 20px 4px 20px;
    padding: 0.6rem 1rem;
}
[data-testid="stChatMessage"]:has(.msg-user) [data-testid="stChatMessageContent"] p { margin-bottom: 0; }

/* ASSISTANT row -> left, plain text like ChatGPT */
[data-testid="stChatMessage"]:not(:has(.msg-user)) [data-testid="stChatMessageContent"] { padding-top: 0.15rem; }

/* clarify badge */
.clarify-badge { display: inline-block; font-size: 0.78rem; font-weight: 600; padding: 2px 10px;
    border-radius: 999px; margin-bottom: 0.4rem; background: rgba(255, 181, 71, 0.16); color: #d98a00; }

/* welcome screen */
.welcome { text-align: center; margin: 8vh 0 1.5rem; }
.welcome h1 { font-size: 2.1rem; margin-bottom: 0.3rem; }
.welcome p { opacity: 0.7; margin: 0 auto; max-width: 560px; }

/* suggestion buttons look like chips/cards */
div[data-testid="stButton"] button[kind="secondary"] { text-align: left; border-radius: 14px; }
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------- helpers
def prompt_options() -> dict[str, Path]:
    options = {"artifacts/system_prompt.md (hiện tại)": ARTIFACTS_DIR / "system_prompt.md"}
    for path in sorted((ARTIFACTS_DIR / "versions").glob("system_prompt*.md")):
        options[f"artifacts/versions/{path.name}"] = path
    return options


def tools_options() -> dict[str, Path]:
    options = {"artifacts/tools.yaml (hiện tại)": ARTIFACTS_DIR / "tools.yaml"}
    for path in sorted((ARTIFACTS_DIR / "versions").glob("tools*.yaml")):
        options[f"artifacts/versions/{path.name}"] = path
    return options


@st.cache_resource(show_spinner=False)
def get_provider(name: str) -> Any:
    return make_provider(name)


def new_transcript(provider: str, model: str | None, version: str, prompt_path: Path, tools_path: Path) -> dict[str, Any]:
    av = build_artifact_version(version, prompt_path, tools_path)
    tid = "_".join([safe_slug(version), "ui", safe_slug(provider), datetime.now().strftime("%Y%m%dT%H%M%S%f")])
    return {
        "transcript_id": tid,
        **artifact_version_dict(av),
        "provider": provider,
        "model": model,
        "system_prompt": str(prompt_path.relative_to(ROOT)),
        "tools": str(tools_path.relative_to(ROOT)),
        "source": "streamlit_app",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }


def reset_chat() -> None:
    for key in ("messages", "history", "transcript", "pending", "queued"):
        st.session_state.pop(key, None)


def render_tool_events(rounds: list[dict[str, Any]]) -> None:
    calls = [(r["round"], ev) for r in rounds for ev in r.get("tool_results", [])]
    if not calls:
        return
    names = ", ".join(dict.fromkeys(ev.get("tool", "?") for _, ev in calls))
    with st.expander(f"Đã dùng {len(calls)} tool: {names}", expanded=False):
        for round_index, ev in calls:
            args = json.dumps(ev.get("args", {}), ensure_ascii=False)
            st.markdown(f"**Round {round_index} · `{ev.get('tool')}`** `{args}`")
            result = ev.get("result", {})
            if isinstance(result, dict) and result.get("error"):
                st.error(f"{result.get('error')}: {result.get('message', '')}")
            st.json(result, expanded=False)


def render_user(text: str) -> None:
    with st.chat_message("user"):
        st.markdown('<span class="msg-user"></span>', unsafe_allow_html=True)
        st.markdown(html.escape(text).replace("\n", "  \n"))


def render_message(msg: dict[str, Any]) -> None:
    if msg["role"] == "user":
        render_user(msg["content"])
        return
    with st.chat_message("assistant"):
        if msg.get("status") == "waiting_for_user":
            st.markdown('<span class="clarify-badge">Cần bạn bổ sung / xác nhận</span>', unsafe_allow_html=True)
        st.markdown(msg["content"])
        if msg.get("rounds"):
            render_tool_events(msg["rounds"])


# ---------------------------------------------------------------- sidebar
with st.sidebar:
    page = st.radio("Trang", ["Chat", "Tools & Prompt", "Eval & Versions"], label_visibility="collapsed")
    if st.button("Cuộc trò chuyện mới", width="stretch", type="primary"):
        reset_chat()
        st.rerun()
    st.divider()

    with st.expander("Cấu hình agent", expanded=False):
        provider_name = st.selectbox("Provider", PROVIDERS, index=0, on_change=reset_chat)
        model_input = st.text_input("Model (trống = mặc định)", value="", on_change=reset_chat)
        version_label = st.text_input("Version label", value="v3", on_change=reset_chat)
        p_opts, t_opts = prompt_options(), tools_options()
        prompt_key = st.selectbox("System prompt", list(p_opts), on_change=reset_chat)
        tools_key = st.selectbox("Tools", list(t_opts), on_change=reset_chat)
        history_window = st.slider("History window (cặp lượt)", 0, 10, 5)
        max_rounds = st.slider("Max tool rounds", 1, 6, 4)

    prompt_path, tools_path = p_opts[prompt_key], t_opts[tools_key]
    av = build_artifact_version(version_label or "ui", prompt_path, tools_path)
    st.caption("Artifact version")
    st.code(av.artifact_version, language=None)
    if "transcript" in st.session_state:
        st.caption("Transcript")
        st.code(f"transcripts/{st.session_state.transcript['transcript_id']}.transcript.json", language=None)

system_prompt = prompt_path.read_text(encoding="utf-8")
declarations = load_tool_declarations(tools_path)
openai_tools = to_openai_tools(declarations)

st.session_state.setdefault("messages", [])
st.session_state.setdefault("history", [])
st.session_state.setdefault("pending", None)


# ---------------------------------------------------------------- agent turn
def run_turn(user_text: str) -> None:
    provider = get_provider(provider_name)
    model = model_input.strip() or None
    if "transcript" not in st.session_state:
        st.session_state.transcript = new_transcript(
            provider_name, model or getattr(provider, "default_model", None), version_label or "ui", prompt_path, tools_path
        )
    transcript = st.session_state.transcript

    st.session_state.messages.append({"role": "user", "content": user_text})
    messages = [
        {"role": "system", "content": system_prompt},
        *trim_history(st.session_state.history, history_window),
        {"role": "user", "content": user_text},
    ]
    turn: dict[str, Any] = {
        "turn_index": len(transcript["turns"]) + 1,
        "started_at": now_iso(),
        "user": user_text,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }
    # Guardrail (confirmation_guard.py): action tools run with confirmed=true only right after
    # the agent asked yes/no and the user answered yes.
    prev = st.session_state.get("pending") or {}
    granted = prev.get("response_type") == "yes_no" and is_affirmative(user_text)
    turn["confirmation_granted"] = granted
    try:
        result = run_model_tool_loop(
            provider=provider, messages=messages, tools=openai_tools, model=model, max_tool_rounds=max_rounds,
            confirmation_granted=granted,
        )
        turn.update(result)
        answer = result["assistant_text"] or "_(không có nội dung trả lời)_"
        st.session_state.history += [
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": answer},
        ]
        # If the agent paused on clarify, remember the expected answer type for quick-reply buttons.
        pending = None
        if result["status"] == "waiting_for_user":
            last = result["tool_events"][-1].get("result", {}) if result["tool_events"] else {}
            pending = {"response_type": last.get("response_type", "text"), "options": last.get("options", [])}
        st.session_state.pending = pending
        st.session_state.messages.append(
            {"role": "assistant", "content": answer, "status": result["status"], "rounds": result["rounds"]}
        )
    except Exception as exc:  # provider/network errors are shown, not raised
        turn.update({"status": "provider_error", "error": f"{type(exc).__name__}: {exc}"})
        st.session_state.messages.append({"role": "assistant", "content": f"**Lỗi provider:** `{turn['error']}`"})
        st.session_state.pending = None
    turn["ended_at"] = now_iso()
    transcript["turns"].append(turn)
    write_transcript(TRANSCRIPTS_DIR / f"{transcript['transcript_id']}.transcript.json", transcript)


# ---------------------------------------------------------------- chat page
def chat_page() -> None:
    # Top-level chat_input is pinned to the bottom of the page, like a normal chatbot.
    typed = st.chat_input("Nhắn cho Research Agent…")
    user_text = typed or st.session_state.pop("queued", None)

    if not st.session_state.messages and not user_text:
        st.markdown(
            '<div class="welcome"><h1>Research Agent</h1>'
            "<p>Đọc tweet, tìm web &amp; tin tức, đọc URL, tìm paper arXiv, tra policy công ty và soạn bản tin. "
            "Thiếu thông tin thì mình hỏi lại; gửi Telegram thì mình xin xác nhận trước.</p></div>",
            unsafe_allow_html=True,
        )
        cols = st.columns(2)
        for i, q in enumerate(SAMPLE_QUESTIONS):
            if cols[i % 2].button(q, key=f"sample_{i}", width="stretch"):
                st.session_state.queued = q
                st.rerun()
        return

    for msg in st.session_state.messages:
        render_message(msg)

    if user_text:
        # Show the user's bubble immediately, then a "thinking" assistant row while the agent runs.
        render_user(user_text)
        with st.chat_message("assistant"):
            with st.spinner("Đang suy nghĩ và gọi tool…"):
                run_turn(user_text)
        st.rerun()

    pending = st.session_state.pending
    if pending and pending["response_type"] == "yes_no":
        c1, c2, _ = st.columns([1, 1, 3])
        if c1.button("Có, gửi đi", width="stretch"):
            st.session_state.queued = "Có, mình xác nhận."
            st.rerun()
        if c2.button("Không", width="stretch"):
            st.session_state.queued = "Không, đừng gửi."
            st.rerun()
    elif pending and pending["response_type"] == "choice" and pending["options"]:
        cols = st.columns(min(len(pending["options"]), 4))
        for i, opt in enumerate(pending["options"]):
            if cols[i % len(cols)].button(opt, key=f"opt_{i}", width="stretch"):
                st.session_state.queued = opt
                st.rerun()


# ---------------------------------------------------------------- tools page
def tools_page() -> None:
    st.header(f"Tools đang khai báo ({len(declarations)})")
    for decl in declarations:
        params = decl.get("parameters", {}).get("properties", {})
        required = set(decl.get("parameters", {}).get("required", []))
        with st.expander(f"`{decl['name']}` - " + " ".join(decl.get("description", "").split())[:90] + "…"):
            st.markdown(decl.get("description", ""))
            rows = [
                {
                    "param": name,
                    "type": spec.get("type", ""),
                    "required": "yes" if name in required else "",
                    "enum": ", ".join(map(str, spec.get("enum", []))),
                    "default": json.dumps(spec.get("default"), ensure_ascii=False),
                    "description": spec.get("description", ""),
                }
                for name, spec in params.items()
            ]
            st.dataframe(rows, width="stretch", hide_index=True)
    st.header("System prompt")
    st.code(system_prompt, language="markdown")


# ---------------------------------------------------------------- eval page
def eval_page() -> None:
    st.header("Version log")
    log_path = ARTIFACTS_DIR / "version_log.csv"
    if log_path.exists():
        with log_path.open(encoding="utf-8") as fh:
            log_rows = list(csv.DictReader(fh))
        st.dataframe(
            [{k: r.get(k, "") for k in ("version", "changed_artifact", "hypothesis", "metric_before", "metric_after")} for r in log_rows],
            width="stretch",
            hide_index=True,
        )

    st.header("Run files")
    run_rows = []
    for f in sorted(glob.glob(str(ROOT / "runs" / "*.json"))):
        try:
            d = json.loads(Path(f).read_text(encoding="utf-8"))
        except Exception:
            continue
        s = d.get("summary", {})
        run_rows.append({
            "file": Path(f).name,
            "version": d.get("artifact_version", "").split("+")[0],
            "suite": "extension" if "_extension_" in f else ("group" if "_group_" in f else "base"),
            "case_acc": s.get("case_accuracy"),
            "routing_acc": s.get("tool_routing_accuracy"),
            "args_acc": s.get("argument_accuracy"),
            "multiturn_acc": s.get("multiturn_accuracy"),
            "provider_errors": s.get("provider_error_cases"),
        })
    if not run_rows:
        st.info("Chưa có run nào trong runs/.")
        return
    st.dataframe(run_rows, width="stretch", hide_index=True)
    base = [r for r in run_rows if r["suite"] == "base" and not r["provider_errors"]]
    if base:
        st.markdown("**Base eval theo run (case accuracy)**")
        chart = [{"run": r["file"].split("_B_")[0] + " · " + r["file"].rsplit("T", 1)[-1][:6], "case_acc": r["case_acc"]} for r in base]
        st.bar_chart(chart, x="run", y="case_acc")


if page == "Chat":
    chat_page()
elif page == "Tools & Prompt":
    tools_page()
else:
    eval_page()
