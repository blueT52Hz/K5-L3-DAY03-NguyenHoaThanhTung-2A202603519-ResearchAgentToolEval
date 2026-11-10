"""TODO(student): Tool Unit Test Challenge.

Each test below is a stub. Replace `pytest.skip(...)` with a real test.
Patterns to copy are in test_tools_examples.py. Fixtures are in conftest.py.

Rules:
- Offline only: mock HTTP with `fake_http`, set fake keys with `monkeypatch.setenv`.
- One behaviour per test. Name the test after the behaviour, not the function.
- Done = `pytest tests/ -v` shows 0 skipped, 0 failed.
"""
from __future__ import annotations

import pytest

from conftest import FakeResponse  # noqa: F401  (you will need it)
from tools import TOOL_FUNCTIONS  # noqa: F401

TODO = "TODO(student): implement this test"


# ---------------- clarify ----------------

clarify_tool = TOOL_FUNCTIONS["clarify"]
format_tool = TOOL_FUNCTIONS["format"]
send_tool = TOOL_FUNCTIONS["send"]
lookup_tool = TOOL_FUNCTIONS["lookup"]
fetch_tool = TOOL_FUNCTIONS["fetch"]
timeline_tool = TOOL_FUNCTIONS["timeline"]
social_search_tool = TOOL_FUNCTIONS["social_search"]
policy_tool = TOOL_FUNCTIONS["policy"]


def test_clarify_choice_returns_options_and_awaits_user() -> None:
    result = clarify_tool(question="Chọn nguồn?", response_type="choice", options=["Web", "Twitter"])
    assert result["options"] == ["Web", "Twitter"]
    assert result["response_type"] == "choice"
    assert result["awaiting_user"] is True


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    items = [{"title": "a1", "section": "A"}, {"title": "b1", "section": "B"}, {"title": "a2", "section": "A"}]
    md = format_tool(items=items, template="sections")["markdown"]
    assert md.count("## A") == 1
    assert md.count("## B") == 1
    assert md.index("a2") < md.index("## B")  # a2 grouped under A, not after B


def test_format_thread_numbers_items() -> None:
    md = format_tool(items=[{"title": "one"}, {"title": "two"}], template="thread")["markdown"]
    lines = [line for line in md.split("\n") if line]
    assert lines[0].startswith("1/ one")
    assert lines[1].startswith("2/ two")


@pytest.mark.parametrize("items", [None, []])
def test_format_empty_items_does_not_crash(items) -> None:
    result = format_tool(items=items, template="sections")
    assert result["item_count"] == 0
    assert result["markdown"] == ""


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100999")
    calls = fake_http(FakeResponse({"ok": True}))

    result = send_tool(text="Bản tin AI", confirmed=True)

    assert len(calls) == 1
    assert calls[0]["method"] == "POST"
    assert calls[0]["url"] == "https://api.telegram.org/bot123:abc/sendMessage"
    assert calls[0]["json"]["chat_id"] == "-100999"
    assert calls[0]["json"]["text"] == "Bản tin AI"
    assert result["status"] == "sent"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))
    result = send_tool(text="x", confirmed=True)
    assert result["error"] == "RuntimeError"
    assert "TELEGRAM_BOT_TOKEN" in result["message"]
    assert calls == []


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "k")
    calls = fake_http(FakeResponse({"results": []}))
    lookup_tool(query="AI", timeframe=None)
    assert "time_range" not in calls[0]["json"]


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-key")
    calls = fake_http(FakeResponse({"data": {
        "markdown": "# Hello\nbody", "metadata": {"title": "T", "sourceURL": "https://www.anthropic.com/news/x"},
    }}))

    result = fetch_tool(url="https://www.anthropic.com/news/x")

    assert calls[0]["url"] == "https://api.firecrawl.dev/v1/scrape"
    assert calls[0]["json"] == {"url": "https://www.anthropic.com/news/x", "formats": ["markdown"]}
    assert calls[0]["headers"]["Authorization"] == "Bearer fc-key"
    assert result["items"][0] == {
        "title": "T", "url": "https://www.anthropic.com/news/x", "source": "anthropic.com", "summary": "# Hello\nbody",
    }


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-key")
    fake_http(FakeResponse({"data": {"markdown": "y" * 9000, "metadata": {}}}))
    item = fetch_tool(url="https://example.com")["items"][0]
    assert len(item["summary"]) == 4000
    assert item["title"] == "https://example.com"  # no metadata title -> falls back to url


# ---------------- timeline / social_search ----------------

def _raw_tweets(n: int) -> list[dict]:
    return [{"tweet_id": str(i), "screen_name": "karpathy", "text": f"tweet {i}"} for i in range(n)]


def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "rk")
    calls = fake_http(FakeResponse({"timeline": [{"text": "no id"}, *_raw_tweets(6)]}))

    result = timeline_tool(screenname="karpathy", limit=3)

    assert calls[0]["params"] == {"screenname": "karpathy"}
    assert calls[0]["headers"]["x-rapidapi-key"] == "rk"
    assert len(result["items"]) == 3
    assert [i["url"] for i in result["items"]] == [f"https://x.com/karpathy/status/{n}" for n in range(3)]


@pytest.mark.parametrize("bad_limit, expected", [(-1, 1), (-3, 1), ("2", 2)])
def test_timeline_negative_limit_does_not_slice_from_end(monkeypatch, fake_http, bad_limit, expected) -> None:
    # Regression: items[: int(limit)] with limit=-1 returned 5 of 6 tweets (silently dropped the LAST one).
    monkeypatch.setenv("RAPIDAPI_KEY", "rk")
    fake_http(FakeResponse({"timeline": _raw_tweets(6)}))
    assert len(timeline_tool(screenname="karpathy", limit=bad_limit)["items"]) == expected


def test_social_search_negative_limit_does_not_slice_from_end(monkeypatch, fake_http) -> None:
    # Same regression as timeline (the helper is duplicated in social_search/tool.py).
    monkeypatch.setenv("RAPIDAPI_KEY", "rk")
    fake_http(FakeResponse({"timeline": _raw_tweets(6)}))
    assert len(social_search_tool(query="AI", limit=-1)["items"]) == 1


@pytest.mark.parametrize("search_type", ["Top", "Latest"])
def test_social_search_passes_search_type(monkeypatch, fake_http, search_type) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "rk")
    calls = fake_http(FakeResponse({"timeline": _raw_tweets(2)}))
    result = social_search_tool(query="OpenAI", search_type=search_type)
    assert calls[0]["url"].endswith("/search.php")
    assert calls[0]["params"] == {"query": "OpenAI", "search_type": search_type}
    assert result["search_type"] == search_type


# ---------------- policy (local knowledge + trust boundary) ----------------

@pytest.mark.parametrize("query", ["", "   ", "là gì của"])  # stopwords only -> no terms
def test_policy_empty_query_returns_no_results(query) -> None:
    assert policy_tool(query=query)["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    results = policy_tool(query="API key dữ liệu khách hàng prompt", policy_area="data_privacy", top_k=10)["results"]
    assert results
    assert {r["policy_area"] for r in results} == {"data_privacy"}


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    marker = "viral tweet as verified fact"
    results = policy_tool(query="viral tweet verified fact citation", policy_area="source_citation", top_k=10)["results"]
    flagged = [line for r in results for line in r["untrusted_text"] if marker in line]
    assert flagged, "the planted instruction-like line must be returned as untrusted_text"
    assert all(marker not in r["facts"] for r in results)


# ---------------- YOUR NEW TOOL(S) ----------------
# Write at least 3 tests per tool your team adds:
#   1. happy path (mocked if it calls an API)
#   2. bad / missing input from the model (empty string, wrong type, out-of-enum value)
#   3. failure path (missing key, HTTP error, timeout) -> returns error dict, does not raise

import requests  # noqa: E402
from datetime import datetime, timezone as dt_timezone  # noqa: E402

wiki_tool = TOOL_FUNCTIONS["wiki"]
hn_tool = TOOL_FUNCTIONS["hackernews"]
now_tool = TOOL_FUNCTIONS["now"]
save_note_tool = TOOL_FUNCTIONS["save_note"]


# ---- wiki ----

def test_wiki_requests_summary_endpoint_and_maps_fields(fake_http) -> None:
    calls = fake_http(FakeResponse({
        "type": "standard", "title": "Andrej Karpathy", "description": "nhà khoa học máy tính",
        "extract": "Andrej Karpathy là ...",
        "content_urls": {"desktop": {"page": "https://vi.wikipedia.org/wiki/Andrej_Karpathy"}},
    }))
    result = wiki_tool(title="Andrej Karpathy", lang="vi")

    assert calls[0]["method"] == "GET"
    assert calls[0]["url"] == "https://vi.wikipedia.org/api/rest_v1/page/summary/Andrej_Karpathy"
    assert "ResearchAgentLab" in calls[0]["headers"]["User-Agent"]
    assert result == {
        "tool": "wiki", "found": True, "lang": "vi", "title": "Andrej Karpathy",
        "description": "nhà khoa học máy tính", "summary": "Andrej Karpathy là ...",
        "url": "https://vi.wikipedia.org/wiki/Andrej_Karpathy", "is_disambiguation": False,
    }


def test_wiki_empty_title_returns_error_without_request(fake_http) -> None:
    calls = fake_http(FakeResponse({}))
    result = wiki_tool(title="   ")
    assert result["error"] == "ValueError"
    assert calls == []


def test_wiki_out_of_enum_lang_falls_back_to_vi_and_escapes_title(fake_http) -> None:
    calls = fake_http(FakeResponse({"title": "AC/DC"}))
    wiki_tool(title="AC/DC", lang="fr")
    assert calls[0]["url"] == "https://vi.wikipedia.org/api/rest_v1/page/summary/AC%2FDC"


def test_wiki_404_is_not_found_not_error(fake_http) -> None:
    fake_http(FakeResponse(status_code=404))
    result = wiki_tool(title="Khong ton tai xyz")
    assert result["found"] is False
    assert "error" not in result


def test_wiki_http_500_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=500))
    assert wiki_tool(title="AI")["error"] == "HTTPError"


# ---- hackernews ----

HN_HITS = {"hits": [
    {"objectID": "1", "title": "Show HN: my LLM", "url": "https://www.example.com/llm", "points": 120,
     "num_comments": 30, "author": "pg", "created_at": "2026-11-10T01:00:00Z"},
    {"objectID": "2", "title": "Ask HN: Rust?", "url": None, "points": 50, "num_comments": 80,
     "author": "dang", "created_at": "2026-11-10T02:00:00Z"},
]}


def test_hackernews_front_page_request_and_mapping(fake_http) -> None:
    calls = fake_http(FakeResponse(HN_HITS))
    result = hn_tool()

    assert calls[0]["url"] == "https://hn.algolia.com/api/v1/search"
    assert calls[0]["params"] == {"tags": "front_page", "hitsPerPage": 5}
    assert result["items"][0]["source"] == "example.com"
    assert result["items"][0]["points"] == 120
    # Ask HN has no external url -> falls back to the HN discussion page
    assert result["items"][1]["url"] == "https://news.ycombinator.com/item?id=2"


def test_hackernews_latest_with_query_uses_search_by_date(fake_http) -> None:
    calls = fake_http(FakeResponse(HN_HITS))
    hn_tool(query="LLM", sort="latest", limit=2)
    assert calls[0]["url"] == "https://hn.algolia.com/api/v1/search_by_date"
    assert calls[0]["params"] == {"tags": "story", "hitsPerPage": 2, "query": "LLM"}


@pytest.mark.parametrize("bad_limit, expected", [("3", 3), (0, 1), (-5, 1), (999, 20), ("abc", 5), (None, 5)])
def test_hackernews_clamps_bad_limit_from_model(fake_http, bad_limit, expected) -> None:
    calls = fake_http(FakeResponse({"hits": []}))
    hn_tool(limit=bad_limit, sort="weird")
    assert calls[0]["params"]["hitsPerPage"] == expected
    assert calls[0]["url"].endswith("/search")  # out-of-enum sort -> top


def test_hackernews_timeout_returns_error_dict(fake_http) -> None:
    fake_http(requests.Timeout("slow"))
    assert hn_tool()["error"] == "Timeout"


# ---- now ----

FIXED_UTC = datetime(2026, 11, 10, 20, 30, tzinfo=dt_timezone.utc)  # = 11/11 03:30 at UTC+7


def test_now_converts_to_vietnam_time_and_weekday() -> None:
    result = now_tool(_now=FIXED_UTC)
    assert result["timezone"] == "Asia/Ho_Chi_Minh"
    assert result["now_iso"] == "2026-11-11T03:30:00+07:00"
    assert result["date"] == "2026-11-11"
    assert result["weekday_vi"] == "Thứ Tư"


def test_now_offset_days_gives_relative_date() -> None:
    result = now_tool(timezone="UTC", offset_days=-1, _now=FIXED_UTC)
    assert result["date"] == "2026-11-10"
    assert result["target_date"] == "2026-11-09"
    assert result["target_weekday_vi"] == "Thứ Hai"


def test_now_accepts_offset_as_string_from_model() -> None:
    assert now_tool(timezone="UTC", offset_days="2", _now=FIXED_UTC)["target_date"] == "2026-11-12"


@pytest.mark.parametrize("kwargs", [{"timezone": "Mars/Base"}, {"offset_days": "hôm qua"}, {"offset_days": 99999}])
def test_now_bad_input_returns_error_dict(kwargs) -> None:
    result = now_tool(_now=FIXED_UTC, **kwargs)
    assert "error" in result


# ---- save_note ----

@pytest.fixture
def notes_dir(tmp_path, monkeypatch):
    import tools.save_note.tool as save_note_module
    monkeypatch.setattr(save_note_module, "NOTES_DIR", tmp_path / "notes")
    return tmp_path / "notes"


def test_save_note_writes_markdown_with_slug_filename(notes_dir) -> None:
    result = save_note_tool(title="Tin AI hôm nay: Đặc biệt!", content="- item 1\n- item 2")

    assert result["status"] == "saved"
    assert result["path"] == "notes/tin-ai-hom-nay-dac-biet.md"
    text = (notes_dir / "tin-ai-hom-nay-dac-biet.md").read_text(encoding="utf-8")
    assert text.startswith("# Tin AI hôm nay: Đặc biệt!")
    assert "- item 1\n- item 2" in text


def test_save_note_does_not_overwrite_existing_note(notes_dir) -> None:
    save_note_tool(title="digest", content="v1")
    second = save_note_tool(title="digest", content="v2")

    assert second["path"] == "notes/digest-2.md"
    assert "v1" in (notes_dir / "digest.md").read_text(encoding="utf-8")


def test_save_note_path_traversal_title_stays_inside_notes(notes_dir) -> None:
    result = save_note_tool(title="../../evil", content="x")
    assert result["path"] == "notes/evil.md"
    assert (notes_dir / "evil.md").exists()
    assert not (notes_dir.parent.parent / "evil.md").exists()


@pytest.mark.parametrize("title, content", [("", "x"), ("t", "   "), ("t", "x" * 50_001)], ids=["empty_title", "spaces", "too_long"])
def test_save_note_bad_input_returns_error_and_writes_nothing(notes_dir, title, content) -> None:
    result = save_note_tool(title=title, content=content)
    assert result["error"] == "ValueError"
    assert not notes_dir.exists() or not any(notes_dir.iterdir())
