---
name: now
track: bonus
kind: local_knowledge
provider: none (system clock + zoneinfo)
requires_env: []
inputs: [timezone, offset_days]
outputs: [now_iso, date, weekday_vi, target_date, target_weekday_vi]
side_effect: false
---
# now

Returns the current date/time in an IANA timezone (default `Asia/Ho_Chi_Minh`) and the
date `offset_days` away from today (`-1` = hôm qua, `-7` = tuần trước, `+1` = ngày mai).

- Use when the user asks what day/date it is, or to resolve relative dates before
  answering. The model's own sense of "today" is unreliable (training cutoff).
- Unknown timezone or non-integer offset returns an error dict, never raises.