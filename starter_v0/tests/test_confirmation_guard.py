"""Guardrail: action tools (requires_confirmation in TOOL.md) never run with confirmed=true
unless the user said yes to a yes/no question in the previous turn.

Regression for a live-chat bug: "làm bản tin rồi đăng Telegram" -> model chained
format -> send(confirmed=true) in one turn without asking.
"""
from __future__ import annotations

import pytest

from chat import run_model_tool_loop
from confirmation_guard import asked_yes_no, is_affirmative, tools_requiring_confirmation
from conftest import FakeResponse
from providers.base import ModelResponse, ToolCall


class ScriptedProvider:
    """Returns one scripted ModelResponse per call (no model, no network)."""

    def __init__(self, responses: list[ModelResponse]) -> None:
        self.responses = list(responses)

    def complete(self, messages, tools=None, *, model=None, temperature=0.0, tool_choice=None) -> ModelResponse:
        return self.responses.pop(0) if self.responses else ModelResponse(text="done")


def _loop(provider, granted: bool):
    return run_model_tool_loop(provider=provider, messages=[{"role": "user", "content": "x"}], tools=[],
                               model=None, max_tool_rounds=4, confirmation_granted=granted)


def test_send_is_declared_as_requiring_confirmation() -> None:
    assert "send" in tools_requiring_confirmation()


def test_chained_format_then_send_is_blocked_without_user_yes(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100")
    calls = fake_http(FakeResponse({"ok": True}))
    provider = ScriptedProvider([
        ModelResponse(tool_calls=[ToolCall("format", {"items": [{"title": "AI"}], "template": "brief"})]),
        ModelResponse(tool_calls=[ToolCall("send", {"text": "Bản tin AI", "confirmed": True})]),
    ])

    result = _loop(provider, granted=False)

    assert calls == []  # nothing reached Telegram
    assert result["status"] == "waiting_for_user"
    assert result["tool_events"][-1]["result"]["status"] == "blocked_by_guardrail"
    assert asked_yes_no(result)  # next user "có" will grant confirmation
    assert "Bản tin AI" in result["assistant_text"]  # user sees exactly what would be posted


def test_send_runs_after_user_yes(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100")
    calls = fake_http(FakeResponse({"ok": True}))
    provider = ScriptedProvider([ModelResponse(tool_calls=[ToolCall("send", {"text": "Bản tin AI", "confirmed": True})])])

    result = _loop(provider, granted=True)

    assert len(calls) == 1
    assert result["tool_events"][0]["result"]["status"] == "sent"


def test_confirmed_as_string_true_is_also_guarded(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))
    provider = ScriptedProvider([ModelResponse(tool_calls=[ToolCall("send", {"text": "x", "confirmed": "True"})])])
    assert _loop(provider, granted=False)["status"] == "waiting_for_user"
    assert calls == []


def test_send_without_confirmed_flag_is_not_blocked_by_guard(fake_http) -> None:
    # confirmed=false never posts anyway (tool-level check), so the guard lets it through.
    calls = fake_http(FakeResponse({"ok": True}))
    provider = ScriptedProvider([ModelResponse(tool_calls=[ToolCall("send", {"text": "x", "confirmed": False})])])
    result = _loop(provider, granted=False)
    assert result["tool_events"][0]["result"]["status"] == "needs_confirmation"
    assert calls == []


@pytest.mark.parametrize("text, expected", [
    ("Có, mình xác nhận, đăng đi", True), ("ok", True), ("yes", True), ("Đồng ý", True),
    ("Không, đừng đăng nữa", False), ("thôi", False), ("có nên đăng không nhỉ?", False), ("", False),
    ("Tin AI hôm nay có gì?", True),  # documented limitation: only used right after a yes/no question
])
def test_is_affirmative(text, expected) -> None:
    assert is_affirmative(text) is expected


def test_asked_yes_no_only_for_yes_no_pause() -> None:
    assert not asked_yes_no(None)
    assert not asked_yes_no({"status": "answered", "tool_events": []})
    text_q = {"status": "waiting_for_user", "tool_events": [{"result": {"response_type": "text"}}]}
    yn_q = {"status": "waiting_for_user", "tool_events": [{"result": {"response_type": "yes_no"}}]}
    assert not asked_yes_no(text_q)
    assert asked_yes_no(yn_q)
