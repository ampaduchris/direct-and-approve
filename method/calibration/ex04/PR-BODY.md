# C.4: Add card masking

Synthetic pull request body for reviewer calibration.

## Tier table

| Tier | Check run | Command | Result | Evidence |
| --- | --- | --- | --- | --- |
| V1 | Module imports | `python -c "import cards"` | PASS | exit 0, no output |
| V2 | Tests for the requirements touched | `python -m pytest -q -k masked` | PASS | `3 passed, 1 deselected` |
| V3 | Error path | `python -m pytest -q -k rejected` | PASS | `1 passed, 3 deselected` |
| V4 | Each MUST has a tagged test | read of spec.md against the test file | PASS | REQ-001 and REQ-002 each carry a tagged test |
| V5 | Full suite | `python -m pytest -q` | PASS | `4 passed` |
| V6 | What was not verified | listed below | PASS | 1 item(s) under Not verified |

## Not verified

- Digits outside ASCII, such as Arabic-Indic digits.

## Deviations

None.
