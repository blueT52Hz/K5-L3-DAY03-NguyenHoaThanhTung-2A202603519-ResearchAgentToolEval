# Team

- Bài: Day 03 - Research Agent Tool Eval
- Team: K5-L3-DAY03
- Repo: `K5-L3-DAY03-NguyenHoaThanhTung-2A202603519-ResearchAgentToolEval`

## Thành viên

| STT | Họ và tên | MSSV | Phạm vi |
|---|---|---|---|
| 1 | Nguyễn Hoa Thanh Tùng (Tùng 1) | 2A202603519 | Tool mới `wiki`; viết REPORT; toàn bộ bonus (3 tool thêm, sửa bug `limit`, guardrail gửi Telegram, UI Streamlit, poster, phân tích run) |
| 2 | Tùng 2 | [MSSV] | v1: tối ưu `system_prompt.md` |
| 3 | Tùng 3 | [MSSV] | Baseline v0 + version_log; viết unit test cho các stub TODO |
| 4 | Nguyễn Mạnh Quyền (Tùng 4) | 2A202603518 | v2: viết lại mô tả tool trong `tools.yaml`; 10 case eval nhóm |
| 5 | Tùng 5 | [MSSV] | v3: bảng routing + rule multi-turn trong prompt; transcript chat live |

## Phân chia công việc (làm lần lượt, commit theo đúng thứ tự)

Mỗi bước bắt đầu sau khi commit của bước trước đã được push. Ai đổi artifact (prompt/tools) thì tự thêm dòng của mình vào `starter_v0/artifacts/version_log.csv` trong cùng commit. Cột "Loại" ghi bước thuộc phần bắt buộc hay bonus.

| Bước | Người làm | Loại | Công việc | File chính | Commit |
|---:|---|---|---|---|---|
| 1 | Tùng 1 | - | Danh sách thành viên + phân công | `TEAM.md` | `docs: add team member list` |
| 2 | Tùng 3 | bắt buộc | Chạy baseline v0 trên base eval, ghi version_log | `runs/v0_*.json`, `artifacts/version_log.csv` | `chore: run v0 baseline and log version` |
| 3 | Tùng 2 | bắt buộc | v1: sửa chỉ dẫn xấu trong prompt (hỏi lại thay vì đoán, xác nhận trước khi gửi, scope), chạy eval | `artifacts/system_prompt.md`, `runs/v1_*.json` | `feat: v1 system prompt behavior rules` |
| 4 | Tùng 4 | bắt buộc | v2: viết lại mô tả tool (USE / DO NOT use, convention args, `clarify.response_type` required), chạy base + extension | `artifacts/tools.yaml`, `runs/v2_*.json` | `feat: v2 tool declarations` |
| 5 | Tùng 5 | bắt buộc | v3: bảng routing + rule multi-turn trong prompt; sửa hồi quy của bản nháp; chạy base + extension | `artifacts/system_prompt.md`, `runs/v3_*.json` | `feat: v3 routing and multi-turn rules` |
| 6 | Tùng 1 | bắt buộc + bonus | Tool mới `wiki` (bắt buộc) và `hackernews`, `now`, `save_note` (bonus); chạy lại base + extension | `tools/<tên>/`, `tools/__init__.py`, `artifacts/tools.yaml` | `feat: add wiki, hackernews, now and save_note tools` |
| 7 | Tùng 3 | bắt buộc | Viết hết các stub TODO + test cho 4 tool mới, chạy pytest offline | `tests/test_tools_todo.py` | `test: implement tool unit tests` |
| 8 | Tùng 1 | bonus | Sửa bug `limit` âm mà unit test bước 7 tìm ra | `tools/timeline/`, `tools/social_search/` | `fix: clamp negative limit in timeline and social_search` |
| 9 | Tùng 4 | bắt buộc | 10 case eval nhóm (5 single, 5 multi-turn), chạy eval group | `data/eval_group.json`, `runs/v3_B_group_*.json` | `test: add 10 group eval cases` |
| 10 | Tùng 5 | bắt buộc | Chat live bằng `chat.py`, lưu transcript nhiều lượt | `transcripts/v3_*.transcript.json` | `docs: add live chat transcript` |
| 11 | Tùng 1 | bonus | Guardrail xác nhận trước khi `send` ở code + test + transcript trước/sau khi sửa | `confirmation_guard.py`, `chat.py`, `tests/test_confirmation_guard.py` | `feat: code-level confirmation guard for send` |
| 12 | Tùng 1 | bonus | UI Streamlit + transcript từ UI (có lần gửi Telegram thật) | `app.py`, `transcripts/v2_ui_*.json` | `feat: add streamlit chat UI` |
| 13 | Tùng 1 | bonus | Poster + phân tích run | `artifacts/poster.html`, `analysis/*.csv`, `scripts/summarize_runs.py` | `docs: add poster and run analysis` |
| 14 | Tùng 1 | bắt buộc | Viết REPORT Phần A + B từ run và transcript thật | `artifacts/REPORT.md` | `docs: write lab report` |
| 15 | Tùng 1 | - | Chuẩn hoá dấu gạch trong tài liệu | `README.md`, `TOOL-SETUP.md`, ... | `docs: normalize dashes in docs` |

Phần bắt buộc: Tùng 2 làm 1 bước (v1); Tùng 1, 3, 4, 5 mỗi người 2 bước. Phần bonus do Tùng 1 làm.

Đường dẫn file tính từ `starter_v0/`.
