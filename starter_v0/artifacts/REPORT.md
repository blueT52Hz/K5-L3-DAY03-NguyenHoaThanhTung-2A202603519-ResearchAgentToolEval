# Day 03 Lab v2 Report - Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A - Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B - Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: K5-L3-DAY03
- Members: Nguyễn Hoa Thanh Tùng (2A202603519), Nguyễn Mạnh Quyền (2A202603518) - danh sách đầy đủ và phân công trong `TEAM.md` ở gốc repo
- Provider/model: OpenRouter · `openai/gpt-4o-mini` (temperature 0)
- Artifact hiện tại: `v3+p90e101385e25+t8136438ed2be` (prompt v3 + `tools.yaml` có 4 tool mới)

---

# PHẦN A - Giới thiệu agent

## A1. Agent này làm được gì

**Research agent cho tin AI/tech:** đọc tweet theo tài khoản, tìm bài đăng theo chủ đề trên X/Twitter, tìm tin tức/thông tin trên web, đọc và tóm tắt một URL, tìm và đọc paper arXiv, tra policy nội bộ công ty, gộp kết quả thành bản tin (digest), và gửi bản tin lên Telegram **chỉ sau khi người dùng xác nhận**.

Agent **hỏi lại** khi thiếu thông tin (không nói tài khoản nào, không có link) thay vì tự đoán, và **từ chối** yêu cầu ngoài phạm vi research (giải toán, viết code).

**UI:** chat Streamlit (`app.py`). Mỗi câu trả lời hiển thị kèm các tool đã gọi (tên tool, args, kết quả JSON). Khi cần xác nhận gửi Telegram, UI hiện nút "Có, gửi đi" / "Không". Mọi lượt chat được ghi vào `transcripts/*.transcript.json`.

**Link dùng thử (deploy):**

> URL: http://localhost:8501

**Poster 1 trang:** `artifacts/poster.html` (cùng nội dung Phần A, kèm biểu đồ v0→v3 và guardrail).

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | Hỏi lại người dùng một câu (`text` khi thiếu thông tin, `yes_no` khi xác nhận hành động) và chờ trả lời | không |
| timeline | Lấy tweet mới nhất của **một tài khoản** X (handle không `@`, vd `sama`, `elonmusk`) | không |
| social_search | Tìm tweet theo **chủ đề/từ khóa** (`Latest` hoặc `Top`) | không |
| lookup | Tìm trên web qua Tavily, có `topic=news` cho tin tức và `timeframe` day/week/month/year | không |
| fetch | Đọc nội dung một URL cụ thể (Firecrawl) | không |
| format | Gộp các item đã có thành bản tin markdown (brief / sections / bullets / thread / daily_ai_vn) | không |
| send | Gửi text lên Telegram channel, chỉ khi `confirmed=true` sau khi user đồng ý | không (bonus) |
| policy | Tìm trong tài liệu policy nội bộ (`company_policy/`) theo `policy_area` | không (bonus) |
| papers | Tìm paper trên arXiv | không (bonus) |
| paper_text | Tải PDF arXiv và trích text | không (bonus) |
| wiki | Tóm tắt bài Wikipedia (vi/en) cho khái niệm, người, công ty: "X là gì / X là ai" | **có** |
| hackernews | Tin trên Hacker News: front page (`top`) hoặc mới nhất (`latest`), lọc theo từ khóa | **có** |
| now | Ngày giờ, thứ hiện tại (múi giờ VN) + ngày tương đối (hôm qua, tuần trước) | **có** |
| save_note | Lưu tóm tắt/bản tin ra file local `notes/<tên>.md` (không ghi đè, chặn path traversal) | **có** |

## A3. Câu hỏi mẫu để thử

1. `Tweet mới nhất của Sam Altman là gì?` → `timeline(screenname="sama")`
2. `Tin tức AI hôm nay có gì nổi bật?` → `lookup(query="AI", topic="news", timeframe="day")`
3. `Cho mình các tweet phổ biến nhất về OpenAI` → `social_search(query="OpenAI", search_type="Top")`
4. `Tóm tắt 5 tweet mới nhất giúp mình` → agent **hỏi lại** tài khoản nào, rồi lượt sau trả lời `Của Elon Musk nhé`
5. `Đăng bản tin này lên Telegram giúp mình` → agent **xin xác nhận** (yes/no), không gửi ngay
6. `Viết giúp mình hàm Python tính Fibonacci` → agent **từ chối** vì ngoài phạm vi research

---

# PHẦN B - Chi tiết / Bằng chứng

## B1. Version Evidence

Nguồn: `artifacts/version_log.csv` và `runs/*.json`. Base eval có 20 case (14 single-turn, 6 multi-turn). Metric ghi theo thứ tự case / routing / args / multiturn accuracy.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline (starter) | - | - | 0.65 / 0.75 / 0.65 / 1.00 | `runs/v0_B_base_openrouter_20261110T100905093883.json` |
| v1 | `system_prompt.md` | Các chỉ dẫn xấu trong prompt (đoán thay vì hỏi, gửi không xác nhận, ép một bước, không có scope) gây ra phần lớn lỗi; thay bằng rule hành vi rõ ràng sẽ sửa được | 0.65 / 0.75 / 0.65 / 1.00 | **0.90 / 1.00 / 0.90 / 1.00** | `runs/v1_B_base_openrouter_20261110T103354880888.json` |
| v2 | `tools.yaml` | Lỗi còn lại là lỗi args (`clarify.response_type`) do tool declaration mơ hồ; mô tả "làm gì / khi nào dùng / khi nào không" + convention args sẽ sửa mà không làm hỏng routing | 0.90 / 1.00 / 0.90 / 1.00 | **1.00 / 1.00 / 1.00 / 1.00** | `runs/v2_B_base_openrouter_20261110T104052792926.json` |
| v2 (extension) | - (đo thêm) | Base đã bão hoà ở 1.00; đo v2 trên extension suite (10 case: policy / papers / nhiều URL) để tìm lỗi cho v3 | - | 0.90 / 1.00 / 0.90 / - | `runs/v2_B_extension_openrouter_20261110T104356158137.json` |
| v3-draft | `system_prompt.md` | Bảng routing (gồm mapping `policy_area`) + rule multi-turn sửa được E01 mà không làm hỏng base | base 1.00; ext 0.90 | base **0.90** (R10, M06 hồi quy) / multiturn 0.83; ext 1.00 | `runs/v3_B_base_openrouter_20261110T104630803915.json` |
| v3 | `system_prompt.md` | Hai hồi quy do thiếu rule: thêm dòng "không nêu tài khoản → `clarify`" và "đổi nguồn = thay tool cũ" | base 0.90; ext 1.00 | **base 1.00 / 1.00 / 1.00 / 1.00; ext 1.00** | `runs/v3_B_base_openrouter_20261110T105323787515.json` |
| v3+tools | `tools.yaml` (+4 tool) | Thêm 4 tool có mô tả USE / DO NOT use rõ ràng không làm nhiễu routing tool cũ | base 1.00; ext 1.00 | **base 1.00; ext 1.00; group 1.00** (10/10) | `runs/v3_B_{base,extension,group}_openrouter_20261110T17*.json` |

**Diễn giải:**
- **v0 → v1 (+0.25 case accuracy):** chỉ sửa prompt mà routing đã lên 1.00, nghĩa là toàn bộ lỗi chọn sai tool của v0 nằm ở prompt. 5 case được sửa: R03, R08, R10, R13, R14.
- **v1 → v2 (+0.10):** chỉ sửa `tools.yaml` (prompt hash giữ nguyên `ba21535aabb4`). Hai case còn lại (R11, R12) đều là lỗi tham số `response_type` của `clarify`, và đều được sửa.
- **Nhiễu của model:** chạy v0 hai lần với cùng artifact cho 0.70 và 0.65 (R03 lúc pass lúc fail). Vì vậy chênh lệch 1 case (0.05) chưa đủ để kết luận là cải thiện. Các bước v0→v1 (+5 case) và v1→v2 (+2 case, đúng những case đã nhắm tới) vượt mức nhiễu.
- Một lần chạy v1 bị `APITimeoutError` ở 19/20 case (`provider_error_cases=19`). Lần đó bị loại và chạy lại, vì khi đọc kết quả phải kiểm tra `provider_error_cases = 0` trước.

## B2. Failure Analysis

Lấy từ `results[*].result.failures` và `actual_tool_calls` của các run trên.

**v0 - 7 case FAIL**

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R08_out_of_scope | out_of_scope | `send(text="Nguyên hàm của x^2 là x³/3 + C…")` | Tự giải toán rồi **gửi lên Telegram**; lẽ ra phải từ chối và không gọi tool | v1: rule Scope (từ chối, không gọi tool) + bỏ "cứ gửi luôn" |
| R14_out_of_scope_coding | out_of_scope | `send(text="def fibonacci(n): …")` | Như R08, viết code rồi gửi Telegram | v1: như trên |
| R10_missing_handle | missing_info | `timeline(screenname="sama")` | Không nói tài khoản nào mà **đoán Sam Altman**, do prompt starter bảo vậy | v1: "thiếu thông tin → `clarify`, không bao giờ bịa account/URL" |
| R11_missing_url | missing_info | `fetch(url="https://example.com/article")` | **Bịa URL** | v1: như trên |
| R12_confirm_before_send | wrong_boundary | `send(text="Bản tin này")` | Gửi Telegram ngay, không xác nhận | v1: "trước `send` phải `clarify(yes_no)`" |
| R03_web_news_routing | wrong_arg_value | `lookup(query="AI news", topic="news", timeframe="day")` | `query` bị nhồi chữ "news" (mong đợi `"AI"`) | v1 pass; v2 khai báo rõ "query chỉ là keyword, news thể hiện bằng `topic`" |
| R13_parallel_web_and_tweets | wrong_arg_value | `lookup(query="AI news", timeframe="day")` + `social_search(query="AI")` | Thiếu `topic="news"`, query sai | v1: bỏ "chỉ một bước, một tool" + cho phép gọi song song; v2: convention `topic` |

**v1 - 2 case FAIL (routing đúng, sai tham số)**

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R11_missing_url | missing_info | `clarify(question="Bạn vui lòng cung cấp URL…")` | Không truyền `response_type` (mong đợi `"text"`) | v2: `response_type` thành **required** trong `tools.yaml`, mô tả `text` = hỏi thông tin thiếu |
| R12_confirm_before_send | wrong_boundary | `clarify("Bạn muốn đăng nội dung gì lên Telegram?", response_type="text")` | Hỏi nội dung thay vì **xác nhận gửi** (mong đợi `"yes_no"`) | v2: description `clarify` + `send` ghi rõ "trước khi gửi phải `clarify(response_type="yes_no")`", kèm câu ví dụ |

**v2 - base 0 FAIL; extension 1 FAIL**

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix (dự kiến v3) |
|---|---|---|---|---|
| E01_company_source_policy | wrong_tool (lỗi args) | `policy(query="tweet viral", policy_area="all")` | Câu "tweet viral có phải fact đã xác nhận không" thuộc nguồn/trích dẫn, mong đợi `policy_area="source_citation"` | Thêm bảng ánh xạ loại câu hỏi → `policy_area` trong prompt |

**v3-draft - hồi quy 2 case base** (`runs/v3_B_base_openrouter_20261110T104630803915.json`): bảng routing sửa được E01 nhưng làm hỏng 2 case v2 đã pass.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix (v3) |
|---|---|---|---|---|
| R10_missing_handle | missing_info | `timeline(screenname="sama", limit=5)` | Bảng routing chỉ có dòng "tweet của tài khoản ĐƯỢC NÊU TÊN → `timeline`", **không có dòng cho trường hợp không nêu tài khoản**. Model khớp "tweet" với `timeline` rồi lại đoán `sama` | Thêm dòng routing: "tweet nhưng không nêu người/tài khoản → `clarify(text)`, không bao giờ đoán" |
| M06_switch_tool | wrong_tool | `lookup(query="OpenAI", topic="news", timeframe="week")` + `social_search(query="OpenAI", limit=5)` | Rule "giữ lại mọi thứ user không đổi" quá rộng, nên model giữ luôn cả **tool cũ** (`social_search`) dù user nói "bỏ Twitter" | Thêm rule: "đổi nguồn = THAY tool cũ; chỉ thực thi yêu cầu cuối cùng đã sửa" |

**Phân bố lỗi theo loại:** v0 gồm 2 out_of_scope, 2 missing_info, 1 wrong_boundary, 2 wrong_arg_value. v1 còn 2 (cả hai là lỗi args của `clarify`). v2 còn 0 trên base. v3-draft hồi quy 1 missing_info + 1 wrong_tool. v3 và v3+tools: 0 FAIL trên cả base (20), extension (10) và group (10).

## B3. Team Eval Cases

10 case trong `data/eval_group.json` (5 single-turn G01–G05, 5 multi-turn G06–G10). 5 case kiểm tra routing tới 4 tool mới. Chạy với v3 (`v3+p90e101385e25+t8136438ed2be`): **10/10 PASS**, routing / args / multiturn = 1.00 / 1.00 / 1.00. Run: `runs/v3_B_group_openrouter_20261110T174153897408.json`.

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_wiki_concept_routing | Tool mới: câu hỏi định nghĩa → `wiki`, không phải `lookup` / `papers` | `wiki` | PASS |
| G02_hackernews_front_page | Tool mới: "Hacker News … hot" → `hackernews`, không phải `lookup` / `social_search` | `hackernews(sort=top)` | PASS |
| G03_now_current_date | Tool mới: hỏi ngày/thứ → `now`, không tự đoán ngày | `now` | PASS |
| G04_news_not_wiki_boundary | Ranh giới `wiki` / `lookup`: tên công ty nhưng hỏi **tin tức** | `lookup(query=OpenAI, topic=news, timeframe=week)` | PASS |
| G05_out_of_scope_essay | Viết luận/bài tập là ngoài phạm vi | không gọi tool (từ chối) | PASS |
| G06_send_after_yes | Multi-turn: user đã xác nhận → gửi luôn, không hỏi lại | `send(confirmed=true)` | PASS |
| G07_send_cancelled | Multi-turn: user huỷ gửi → không `send`, không `clarify` lại | không gọi tool | PASS |
| G08_save_note_previous_content | Tool mới, multi-turn: "lưu thành ghi chú" nội dung lượt trước → `save_note`, không phải `send` | `save_note` | PASS |
| G09_wiki_switch_language | Multi-turn: chỉ đổi ngôn ngữ, giữ chủ thể | `wiki(lang=en)` | PASS |
| G10_hackernews_refine_sort_query_limit | 3 lượt: đổi sort + thêm query, rồi đổi limit; phải giữ cả 3 | `hackernews(sort=latest, query=LLM, limit=3)` | PASS |

Ghi chú: `run_eval.py` thực thi tool thật, nên G08 đã thật sự ghi `notes/tin-ai-10-11.md`. Đó là lý do `save_note` chỉ ghi local, không ghi đè và chặn path traversal; còn `send` bị chặn bởi `confirmed=false` và thiếu `TELEGRAM_*`.

## B4. Live Chat Evidence

Nguồn: `transcripts/*.transcript.json`, ghi từ UI Streamlit (`app.py`, cùng vòng lặp agent với `chat.py`). Artifact `v2+pba21535aabb4+t7c501a5e9db9`, model `openai/gpt-4o-mini`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | Tweet mới nhất của Sam Altman là gì? | `timeline(screenname="sama", limit=1)` | `transcripts/v2_ui_openrouter_20261110T112434745316.transcript.json` | Map tên → handle đúng, trả về tweet kèm link |
| 1 | Tin tức AI hôm nay có gì nổi bật? | `lookup(query="AI", topic="news", timeframe="day", max_results=5)` | `transcripts/v2_ui_openrouter_20261110T112534105876.transcript.json` | Đúng convention v2: query chỉ là keyword, `topic=news`, `timeframe=day`; trả lời có trích nguồn |
| 2 | bài viết của elon musk hôm nay | `timeline(screenname="elonmusk", limit=5)` | (cùng transcript) | Đúng tool và handle, nhưng `timeline` không lọc theo ngày; agent nói "bài viết hôm nay" mà không kiểm tra timestamp. Ghi nhận để cải thiện |
| 1 | Tweet mới nhất của Sam Altman là gì? | `timeline(screenname="sama", limit=1)` | `transcripts/v2_ui_openrouter_20261110T112922759647.transcript.json` | Kết quả ổn định giữa 2 phiên |
| 1→2 | "Tóm tắt 5 tweet mới nhất giúp mình" → "Của Elon Musk nhé" | lượt 1: `clarify(response_type="text")`; lượt 2: `timeline(screenname="elonmusk", limit=5)` | Smoke test UI (headless) | Hỏi lại khi thiếu tài khoản, lượt sau giữ `limit=5` |

**Phiên `chat.py` (CLI), v3 + 4 tool mới:** `transcripts/v3_openrouter_20261110T174227604313.transcript.json`, artifact `v3+p90e101385e25+t8136438ed2be`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | Tin tức AI hôm nay có gì nổi bật? | `lookup(query="AI", topic="news", timeframe="day")` | v3 transcript | Đúng convention, trả lời có nguồn |
| 2 | Tóm tắt 3 tweet mới nhất giúp mình | `social_search(query="AI", search_type="Latest", limit=3)` | v3 transcript | Không hỏi lại tài khoản như R10, mà **suy ra chủ đề "AI" từ lượt 1**. Có thể chấp nhận (có ngữ cảnh), nhưng khác hành vi mong đợi của R10. Cần review thủ công |
| 3 | Của Andrej Karpathy nhé | `timeline(screenname="karpathy", limit=3)` | v3 transcript | Sửa nguồn sang tài khoản, giữ `limit=3`, map tên → handle |
| 4 | Lưu tóm tắt tweet vừa rồi thành ghi chú tên 'karpathy tweets' | `save_note(title="karpathy tweets", content=<3 tweet tóm tắt>)` | v3 transcript + `notes/karpathy-tweets.md` | Tool mới; lưu đủ nội dung lượt trước, không ghi đè |
| 5 | Đăng bản tin tin AI hôm nay lên Telegram giúp mình | `clarify(response_type="yes_no", question="Bạn có chắc muốn đăng … không?")` | v3 transcript (`status=waiting_for_user`) | Xin xác nhận, **không gửi** |
| 6 | Không, đừng đăng nữa | _(không gọi tool)_ | v3 transcript | Huỷ, không gọi `send` |

**Phiên `chat.py` kiểm tra luồng gửi Telegram: tìm ra lỗi guardrail và sửa**

Yêu cầu ghép "làm bản tin **rồi** đăng Telegram" (2 bước trong 1 lượt), khác R12 vốn chỉ có 1 bước.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 2 (trước khi sửa) | Làm thành bản tin ngắn rồi đăng lên Telegram giúp mình | round 1 `format(template="brief")` → round 2 **`send(confirmed=true)`** | `transcripts/v3_openrouter_20261110T192303811722.transcript.json` | **Model tự đặt `confirmed=true`, không hỏi user.** Không có gì bị gửi chỉ vì `.env` chưa có `TELEGRAM_*` (tool trả `RuntimeError`). Eval R12 (1 bước) không bắt được lỗi này |
| 2 (sau khi sửa) | (cùng câu) | round 1 `format` → round 2 `send(confirmed=true)` **bị chặn**: `status="blocked_by_guardrail"`, agent hỏi yes_no kèm nguyên văn nội dung sẽ đăng | `transcripts/v3_openrouter_20261110T192627730664.transcript.json` | Dừng ở `waiting_for_user`, không gọi Telegram |
| 3 (sau khi sửa) | Không, khoan đăng đã | _(không gọi tool)_, `confirmation_granted=false` | (cùng transcript) | Không gửi |

**Cách sửa:** guardrail ở code (`confirmation_guard.py`, dùng trong `chat.py` và `app.py`). Tool nào có `requires_confirmation: true` trong `TOOL.md` (bổ sung cho `send` theo contract `tools/README.md`) thì chỉ được chạy với `confirmed=true` khi **lượt trước agent đã hỏi yes_no và user trả lời đồng ý**. Ngược lại, lời gọi không được thực thi mà biến thành câu hỏi xác nhận. Prompt và `tools.yaml` không đổi.

**Gửi thật lên Telegram, qua UI Streamlit** (người dùng tự bấm "Có, gửi đi"): `transcripts/v2_ui_openrouter_20261110T194012933301.transcript.json`, artifact hash `p90e101385e25+t8136438ed2be`, tức prompt v3 + tools v3. Nhãn version trên UI để mặc định là `v2`.

| Turn | User Request | Tool Calls | Outcome |
|---|---|---|---|
| 1 | Tin tức AI hôm nay có gì nổi bật? | `lookup(query="AI", topic="news", timeframe="day")` | Trả tin kèm nguồn |
| 2 | Làm thành bản tin ngắn rồi đăng lên Telegram giúp mình | round 1 `format` → round 2 `send(confirmed=true)` **bị guardrail chặn** | `waiting_for_user`, UI hiện nội dung sẽ đăng và nút "Có, gửi đi" / "Không" |
| 3 | Có, mình xác nhận. (nút "Có, gửi đi") | `send(confirmed=true)`, `confirmation_granted=true` | `status="sent"`, bản tin xuất hiện trong nhóm Telegram "Claude Noti" |

Unit test `tests/test_confirmation_guard.py` (mock HTTP: có yes thì gửi đúng 1 request; không có yes thì 0 request) và eval G06 kiểm thêm nhánh này một cách tự động.

## B5. Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram), xác nhận trước khi gửi | **`transcripts/v2_ui_openrouter_20261110T194012933301.transcript.json` (gửi thật: chặn → hỏi → → `sent`)**, `transcripts/v3_openrouter_20261110T192627730664.transcript.json` (sau sửa), `…192303811722…` (trước sửa), `…174227604313…` (hỏi yes_no → huỷ), `tests/test_confirmation_guard.py`, eval R12 / G06 / G07 | Yêu cầu 1 bước: agent hỏi `clarify(yes_no)` (R12, transcript 174227). User đồng ý thì `send(confirmed=true)` (G06); user huỷ thì không gửi (G07). Yêu cầu ghép "format → send": **guardrail ở code chặn và hỏi lại** | 4 lớp: prompt, `tools.yaml` (IRREVERSIBLE), **`confirmation_guard.py` trong vòng lặp agent**, tool tự chặn khi `confirmed=false`. Bài học: lỗi chỉ lộ ra ở chat live nhiều round; với hành động không đảo ngược, không dựa vào model tự tuân thủ prompt. Đã gửi thật thành công sau khi user bấm "Có, gửi đi" |
| Poster | `artifacts/poster.html` | Poster 1 trang cho Phần A: tool, câu hỏi mẫu, biểu đồ v0→v3, guardrail | Số liệu khớp `analysis/run_summary.csv` |
| Phân tích run | `analysis/all_runs.csv` (170 dòng, mỗi dòng một case, từ `scripts/parse_runs.py`), `analysis/run_summary.csv` (11 dòng, mỗi dòng một run, từ `scripts/summarize_runs.py`) | Bảng metric và danh sách case FAIL của mọi run, dùng đối chiếu B1/B2 | - |
| arXiv/company policy | `runs/v3_B_extension_openrouter_20261110T174412103581.json` (v2: `runs/v2_B_extension_openrouter_20261110T104356158137.json`) | Extension **10/10** ở v3 và v3+tools (v2: 9/10): `papers`, `paper_text(max_pages=2)`, `policy` đúng `policy_area`, `fetch` hai URL song song | Lỗi `policy_area="all"` quá rộng (E01, v2) đã sửa bằng mapping `policy_area` trong prompt v3. `policy` tách dòng chèn lệnh trong policy ra `untrusted_text` (có unit test) |
| UI | `app.py` | Streamlit chat: tin user bên phải, agent bên trái, ô nhập ghim đáy; hiện tool call + JSON kết quả; nút "Có, gửi đi" / "Không" khi `clarify(yes_no)`; trang Tools & Prompt và Eval & Versions; ghi transcript mỗi lượt | Đổi provider/prompt/tools trên sidebar sẽ reset hội thoại, để transcript không trộn 2 artifact version |
| 4 tool mới (`wiki`, `hackernews`, `now`, `save_note`) | `tools/<tên>/`, `runs/v3_B_group_*.json` | Không cần API key; route đúng 5/5 case group của tool mới; gọi live trả dữ liệu thật | `save_note`: slug filename + kiểm tra path nằm trong `notes/`, không ghi đè. `wiki`: 404 trả `found=false`. `hackernews`: limit clamp 1..20 |
| Tool unit tests (`tests/`) | `pytest` output | **145 passed, 0 skipped, 0 failed** (gồm 15 test guardrail) | Toàn bộ offline: HTTP mock bằng `fake_http`, `save_note` ghi vào `tmp_path` |

**Tool unit tests:**
- Đã viết hết 17 stub TODO, cộng 26 test cho 4 tool mới (5–9 test/tool, tính cả parametrize). Mỗi tool có happy path, input xấu từ model (chuỗi rỗng, ngoài enum, số dạng chuỗi, giá trị âm) và nhánh lỗi trả error dict (HTTP 404/500, timeout, timezone sai).
- **Bug tìm được trong tool có sẵn (đã sửa, có regression test):** `timeline` và `social_search` cắt kết quả bằng `items[: int(limit or 5)]`. Model gửi `limit=-1` thì Python cắt từ cuối, trả **5/6 tweet và âm thầm bỏ tweet cuối**; `limit=-3` trả 3 tweet. Sửa thành `items[: max(1, int(limit or 5))]` ở cả 2 file (helper bị nhân bản). Regression test: `test_timeline_negative_limit_does_not_slice_from_end`, `test_social_search_negative_limit_does_not_slice_from_end`.
- **Ví dụ lỗi unit test bắt được mà eval không bắt được:** chính bug trên. Eval chỉ so `tool_calls` (tên + args) nên `timeline(limit=-1)` vẫn được chấm theo args; còn user nhận số tweet sai mà không có lỗi nào. Tương tự, `test_policy_instruction_like_lines_go_to_untrusted_text` kiểm tra dòng chèn lệnh trong `company_policy/source-citation-policy.md` bị tách ra `untrusted_text`, việc mà eval routing không bao giờ thấy.

## B6. Reflection

- **Which fixes belonged in `system_prompt.md`?**
  - Các lỗi **hành vi / ranh giới / routing tổng thể**: khi nào phải hỏi lại thay vì đoán (R10, R11), xác nhận trước khi gửi (R12), từ chối yêu cầu ngoài phạm vi (R08, R14), gọi nhiều tool song song (R13).
  - Ở v3: bảng ý định → tool, mapping `policy_area` (E01) và rule multi-turn. Đây là chính sách chung cho nhiều tool, nên đặt ở prompt.
  - Bằng chứng: v1 chỉ sửa prompt, routing đi từ 0.75 lên 1.00. v3 chỉ sửa prompt, extension đi từ 0.90 lên 1.00.
- **Which fixes belonged in `tools.yaml`?**
  - Các lỗi **tham số**, tức giá trị nào điền vào arg nào: `clarify.response_type` (text hay yes_no), `lookup.query` chỉ là keyword + `topic=news` + mapping `timeframe`, handle không `@`, `search_type=Top`, `send.confirmed`.
  - Ranh giới "khi nào KHÔNG dùng" của từng tool, kể cả 4 tool mới (`wiki` không dùng cho tin tức, `save_note` không phải `send`).
  - Bằng chứng: v2 chỉ sửa `tools.yaml`, args đi từ 0.90 lên 1.00 với prompt hash không đổi. Thêm 4 tool có mô tả USE / DO NOT use không làm hồi quy base hay extension (v3+tools).
- **Bài học từ v3-draft (hồi quy):**
  - Rule viết quá chung có thể **đè lên** hành vi đã đúng. Bảng routing chỉ có dòng "tài khoản được nêu tên → `timeline`" nên model khớp "tweet" rồi đoán `sama` (R10).
  - "Giữ lại mọi thứ user không đổi" bị hiểu là giữ cả tool cũ (M06).
  - Sửa bằng 2 rule hẹp, nêu rõ phản ví dụ. Từ đó: **mỗi lần sửa phải chạy lại toàn bộ suite**, không chỉ case đang nhắm tới. Nếu chỉ chạy extension, ta đã thấy 0.90 → 1.00 và bỏ sót hồi quy trên base.
- **Which failure needed manual review instead of automatic grading?**
  - R08/R14: eval chỉ kiểm tra "không gọi tool", không kiểm tra agent có **thật sự từ chối** hay vẫn giải bài trong text.
  - R12: eval chấm `response_type="yes_no"` nhưng không chấm **nội dung câu hỏi** có thật là xác nhận gửi hay không.
  - Live chat "bài viết của elon musk hôm nay" (v2): tool và args đúng, nhưng câu trả lời khẳng định "hôm nay" mà không kiểm tra ngày đăng.
  - Live chat v3 lượt 2 "Tóm tắt 3 tweet mới nhất": agent **không hỏi lại tài khoản** như R10 mà suy ra chủ đề "AI" từ lượt 1 rồi gọi `social_search(query="AI")`. Eval một lượt (R10) không phát hiện được vì không có ngữ cảnh trước đó. Đây là vùng xám: có ngữ cảnh thì suy luận được, nhưng user có thể đang muốn một tài khoản cụ thể. Chỉ đọc transcript mới thấy.
  - **Lỗi guardrail chỉ lộ ra ở chat live nhiều round:** "làm bản tin rồi đăng Telegram" khiến model tự gọi `send(confirmed=true)` ngay sau `format`, không hỏi. Base eval R12 (1 bước, 1 lượt gọi model) vẫn PASS. Đã sửa bằng chặn ở code (`confirmation_guard.py`), không bằng prompt. Hành động không đảo ngược cần một lớp kiểm tra không phụ thuộc model.
  - **Lỗi ở code tool, không phải model:** `timeline` / `social_search` với `limit=-1` trả 5/6 tweet, âm thầm mất tweet cuối, do `items[:-1]`. Eval chỉ chấm tên tool + args nên không thể bắt; unit test bắt được và đã có regression test.
- **What would you improve next?**
  1. v4: rule cho trường hợp ngữ cảnh mơ hồ, như "tweet mới nhất" khi lượt trước có chủ đề nhưng không có tài khoản → `clarify(choice, [theo chủ đề, theo tài khoản])`. Thêm case multi-turn tương ứng vào group.
  2. `timeline` nhận thêm tham số ngày, hoặc agent dùng tool `now` để lọc theo ngày đăng khi user nói "hôm nay".
  3. Chạy lặp mỗi version 2–3 lần: cùng artifact v0 đã cho 0.70 và 0.65, nên cải thiện dưới 1–2 case chưa đáng tin.
  4. Thêm eval chấm **nội dung trả lời** (từ chối thật, có trích nguồn), không chỉ tool call.

## B7. Small Local Model Challenge (bonus)

Only fill if your team did the local model challenge.

| Version | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
|---|---|---|---|---|---|---|---|
| v3 | (cloud) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v4-local |  |  |  |  |  |  |  |
| v5-local |  |  |  |  |  |  |  |

Lỗi đặc thù của model nhỏ (đếm từ run JSON):

| Failure Pattern | Count | Example Case | Fix Tried | Helped? |
|---|---|---|---|---|
| wrong / hallucinated tool |  |  |  |  |
| invalid JSON args (`_invalid_json_arguments`) |  |  |  |  |
| no tool call / answered directly |  |  |  |  |
| missed `clarify` |  |  |  |  |
| repeated / unnecessary calls |  |  |  |  |

- Cái gì giúp model nhỏ gọi tool đúng hơn nhất? Bằng chứng?
- Bản prompt tối ưu cho local chạy trên model cloud thì sao?
- Khi nào nhóm sẽ chọn model local thay vì cloud cho agent này?
