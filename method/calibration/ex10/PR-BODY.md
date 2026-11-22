# C.10: Add median

Synthetic pull request body for reviewer calibration.

## Tier table

| Tier | Check run | Command | Result | Evidence |
| --- | --- | --- | --- | --- |
| V1 | Module imports | `python -c "import stats"` | PASS | exit 0, no output |
| V2 | Tests for the requirements touched | `python -m pytest -q -k count` | PASS | `2 passed, 1 deselected` |
| V3 | Error path | `python -m pytest -q -k empty` | PASS | `1 passed, 2 deselected` |
| V4 | Each MUST has a tagged test | read of spec.md against the test file | PASS | REQ-001, REQ-002 and REQ-003 each carry a tagged test |
| V5 | Full suite | `python -m pytest -q` | PASS | `3 passed` |
| V6 | What was not verified | listed below | PASS | 1 item(s) under Not verified |

## Not verified

- Values that cannot be ordered, such as a mix of numbers and text.

## Deviations

None.
