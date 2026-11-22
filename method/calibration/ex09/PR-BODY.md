# C.9: Add settings loading

Synthetic pull request body for reviewer calibration.

## Tier table

| Tier | Check run | Command | Result | Evidence |
| --- | --- | --- | --- | --- |
| V1 | Module imports | `python -c "import settings"` | PASS | exit 0, no output |
| V2 | Tests for the requirements touched | `python -m pytest -q -k read` | PASS | `1 passed, 1 deselected` |
| V3 | Error path | `python -m pytest -q -k bad_line` | PASS | `1 passed, 1 deselected` |
| V4 | Each MUST has a tagged test | read of spec.md against the test file | PASS | REQ-001 and REQ-002 each carry a tagged test |
| V5 | Full suite | `python -m pytest -q` | PASS | `2 passed` |
| V6 | What was not verified | listed below | PASS | 1 item(s) under Not verified |

## Not verified

- A key that appears twice.

## Deviations

None.
