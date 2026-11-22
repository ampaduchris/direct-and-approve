# C.7: Add digit hiding

Synthetic pull request body for reviewer calibration.

## Tier table

| Tier | Check run | Command | Result | Evidence |
| --- | --- | --- | --- | --- |
| V1 | Module imports | `python -c "import digits"` | PASS | exit 0, no output |
| V2 | Tests for the requirements touched | `python -m pytest -q -k survives` | PASS | `1 passed, 1 deselected` |
| V3 | Error path | none | NOT VERIFIED | no error path in scope |
| V4 | Each MUST has a tagged test | read of spec.md against the test file | PASS | REQ-001 and REQ-002 each carry a tagged test |
| V5 | Full suite | `python -m pytest -q` | PASS | `2 passed` |
| V6 | What was not verified | listed below | PASS | 2 item(s) under Not verified |

## Not verified

- No error path exists in this change, so V3 has nothing to run.
- Digits outside ASCII.

## Deviations

None.
