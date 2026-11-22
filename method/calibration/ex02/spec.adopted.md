# days specification (synthetic)

| Id | Level | Requirement | Test |
| --- | --- | --- | --- |
| REQ-001 | MUST | `parse_day("2026-11-15")` returns `(2026, 11, 15)`. | `test_parse_day` |
| REQ-002 | MUST | A day that does not exist in the calendar, such as 2026-02-30, raises `ValueError`. | `test_impossible_day_rejected` |
| REQ-003 | MUST | A month outside 1 to 12 raises `ValueError`. | `test_month_out_of_range` |
