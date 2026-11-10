from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from tools._shared import err

WEEKDAYS_VI = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]


def current_datetime(timezone: str = "Asia/Ho_Chi_Minh", offset_days: int = 0, _now: datetime | None = None) -> dict[str, Any]:
    """Current date/time in a timezone, plus the date `offset_days` away (e.g. -1 = hôm qua, -7 = tuần trước).

    `_now` is only for unit tests (inject a fixed clock); the model never sees it.
    """
    try:
        tz = ZoneInfo((timezone or "Asia/Ho_Chi_Minh").strip())
        offset = int(offset_days or 0)
        if abs(offset) > 3650:
            raise ValueError("offset_days must be within ±3650")
        now = (_now or datetime.now(tz)).astimezone(tz)
        target = now + timedelta(days=offset)
        return {
            "tool": "now",
            "timezone": str(tz),
            "now_iso": now.isoformat(timespec="seconds"),
            "date": now.date().isoformat(),
            "weekday_vi": WEEKDAYS_VI[now.weekday()],
            "offset_days": offset,
            "target_date": target.date().isoformat(),
            "target_weekday_vi": WEEKDAYS_VI[target.weekday()],
        }
    except Exception as exc:  # unknown timezone (ZoneInfoNotFoundError), non-int offset...
        return err("now", exc)