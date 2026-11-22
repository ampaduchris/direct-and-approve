# C.5: Add amount to cents conversion

Synthetic pull request body for reviewer calibration.

## Tier table

| Tier | Check run | Command | Result | Evidence |
| --- | --- | --- | --- | --- |
| V1 | Module imports | `python -c "import cents"` | PASS | exit 0, no output |
| V2 | Tests for the requirements touched | `python -m pytest -q -k to_cents` | PASS | `1 passed, 1 deselected` |
| V3 | Error path | `python -m pytest -q -k rejected` | PASS | `1 passed, 1 deselected` |
| V4 | Each MUST has a tagged test | read of spec.md against the test file | PASS | REQ-001, REQ-002 and REQ-003 each carry a tagged test |
| V5 | Full suite | `python -m pytest -q` | PASS | `2 passed` |
| V6 | What was not verified | listed below | PASS | 1 item(s) under Not verified |

## Not verified

- Amounts written with a comma as the decimal mark.

## Deviations

None.
