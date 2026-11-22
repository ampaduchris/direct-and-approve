# F12 calibration: expected findings

Do not read before your eleven entries are written. This file names every planted defect.

Every command and output line below was run on 15 Nov 2026 (pytest 9.2.0, Python 3.13.5 through `uv run --with pytest`). The full output is in `PROOF.txt`; `prove.py` reproduces it.

| Example | Class | Severity | Tag | Requirement | Hides a real fault |
| --- | --- | --- | --- | --- | --- |
| ex01 | M7 weak assertion | S2 | must-fix | REQ-001, REQ-002 | no |
| ex02 | M3 expected-to-fail test | S1 | must-fix | REQ-002 | yes |
| ex03 | M1 asserts the mock | S2 | must-fix | REQ-001 | no |
| ex04 | control | none | none | none | no |
| ex05 | M9 never collected | S1 | must-fix | REQ-001 | yes |
| ex06 | M4 spec reworded | S1 | must-fix, GATE | REQ-001 | yes, against the adopted text |
| ex07 | M5 fixture cannot fail | S1 | must-fix | REQ-001 | yes |
| ex08 | M10 special-cased inputs | S1 | must-fix | REQ-001 | yes |
| ex09 | M2 asserts nothing | S2 | must-fix | REQ-001 | no |
| ex10 | M6 PASS on a red run | S1 | must-fix | REQ-002 | yes, and the suite shows it |
| ex11 | M8 wrong exception | S1 | must-fix | REQ-002 | yes |

## ex01 · M7 · S2 · must-fix

- Requirement: REQ-001 and REQ-002 (both MUST).
- Observed: `test_redact_report` checks the keys, that `count` is an integer and that `[X]` appears once. `test_redact_two_terms` checks that `[X]` appears at least once. No test checks that every occurrence is gone or what `count` is.
- Expected: exact output text and exact count, including a second occurrence in a different case.
- Command: `mutate_check.py redact.py:redact --req REQ-001,REQ-002`
- Output: `gut killed`, `raise killed`, `flip SURVIVED  2 passed`. The surviving version starts the count at 1 and subtracts.
- The code is right for the inputs tried, so S2. Reporting REQ-002 alone is a hit; REQ-001 is the harder half.

## ex02 · M3 · S1 · must-fix

- Requirement: REQ-002 (MUST).
- Observed: the only test for REQ-002 is marked `xfail`. `parse_day("2026-02-30")` returns `(2026, 2, 30)`. The tier table marks V4 and V5 PASS on "2 passed, 1 xfailed".
- Expected: `ValueError`, and a test that passes.
- Command: `req_run.py --spec spec.md --tests .` then `python -c 'from days import parse_day; print(parse_day("2026-02-30"))'`
- Output: `REQ-002 MUST ... XFAIL NO-PASSING-TEST`; the one-liner prints `(2026, 2, 30)`. `tier_check.py` adds the warning `PASS-WITH-SKIPS (1 xfailed)`.
- One finding, not two: the xfail and the fault it hides.

## ex03 · M1 · S2 · must-fix

- Requirement: REQ-001 (MUST).
- Observed: `test_gross_adds_vat_and_rounds` patches `vat.gross_cents` and asserts the patched return value. The real function never runs. The rounding rule has no proof.
- Expected: call the real function with a net amount that needs rounding, for example 1049 at 19 per cent gives 1248.31, so 1248; and one that lands on a half.
- Command: `mutate_check.py vat.py:gross_cents --req REQ-001`
- Output: `gut SURVIVED`, `raise SURVIVED`, `flip SURVIVED`.
- Note the test even asserts a wrong number (1249); nothing notices. The code is right, so S2. `req_run.py` is clean here: asserts execute, on the mock.

## ex04 · control

- Expected entry: "no finding", or S4 notes only.
- Every script exits 0. Probe: `gut killed`, `raise killed`, `flip killed`. The single "Not verified" item (digits outside ASCII) is honest: `str.isdigit` accepts them and the spec is silent. Naming that as an S3 or S4 observation is fine. A must-fix here is a false positive.

## ex05 · M9 · S1 · must-fix

- Requirement: REQ-001 (MUST).
- Observed: `test_cents.py` defines `test_to_cents` twice (lines 7 and 20). Python keeps the second, tagged REQ-003. The first, tagged REQ-001, never runs. Run under another name it fails: `to_cents("12.5")` returns 1205.
- Expected: 1250, and three collected tests, not two.
- Command: `req_run.py --spec spec.md --tests .` then `python -c 'from cents import to_cents; print(to_cents("12.5"))'`
- Output: `REQ-001 MUST ... NOT-COLLECTED NO-PASSING-TEST`, `never ran: test_cents.py::test_to_cents (line 6)`; the one-liner prints `1205`. The probe with `--req REQ-001` prints `NO TESTS SELECTED`.
- A reader can also see it from "2 passed" against three test functions.

## ex06 · M4 · S1 · must-fix with a GATE

- Requirement: REQ-001 (MUST).
- Observed: the adopted row says a long note "is cut at the last space at or before character 80, never inside a word". The row at HEAD says "is cut at character 80". The code is `note[:80]` and cuts inside a word. The body says "Deviations: None".
- Expected: the adopted behaviour, or a deviation entry and the owner's decision.
- Command: `spec_diff.py --then spec.adopted.md --now spec.md --deviations PR-BODY.md`
- Output: `REQ-001  TEXT-CHANGED NO-DEVIATION` with both rows.
- Every other script is clean and every probe is killed. This is the case that only the history shows. Suggested change must carry `GATE:` because restoring the row or accepting the weaker one is the owner's call.

## ex07 · M5 · S1 · must-fix

- Requirement: REQ-001 (MUST).
- Observed: the fixture `digit_lines` keeps lines where `line.isdigit()` is true. No line is all digits, so the list is empty and the loop in `test_no_digit_survives` never runs. `hide_digits("Card 4111 1111 1111 111")` returns `Card #### #### #### 111`.
- Expected: every digit replaced; a fixture that yields the three lines.
- Command: `req_run.py --spec spec.md --tests .` then the one-liner.
- Output: `REQ-001 MUST ... ZERO-ASSERT`, `passed with 0 asserts executed (1 written)`. Probe: `gut SURVIVED`, `raise SURVIVED`.

## ex08 · M10 · S1 · must-fix

- Requirement: REQ-001 (MUST).
- Observed: `_KNOWN` in `luhn.py` holds exactly the three numbers the test uses. The general path doubles every second digit from the left, which is wrong for numbers with an even count of digits. `luhn_ok("4111111111111111")` returns `False`.
- Expected: `True`. That number passes the Luhn check.
- Command: `literal_overlap.py --src . --tests test_luhn.py` then `python -c 'from luhn import luhn_ok; print(luhn_ok("4111111111111111"))'`
- Output: three `OVERLAP` lines; the one-liner prints `False`.
- `req_run.py` is clean and all three probes are killed. A reviewer who stops at the probes misses it.

## ex09 · M2 · S2 · must-fix

- Requirement: REQ-001 (MUST).
- Observed: `test_keys_and_values_read` ends with `result == expected`, a comparison with no `assert`.
- Expected: `assert result == expected`.
- Command: `req_run.py --spec spec.md --tests .`
- Output: `REQ-001 MUST ... ZERO-ASSERT`, `passed with 0 asserts executed (0 written)`. Probe: `gut SURVIVED`, `raise killed`.
- The code is right, so S2.

## ex10 · M6 · S1 · must-fix

- Requirement: REQ-002 (MUST); tier rows V2 and V5.
- Observed: the body says V2 `2 passed, 1 deselected` and V5 `3 passed`, both PASS. The commands give `1 failed, 1 passed, 1 deselected` and `1 failed, 2 passed`. `median([4, 1, 3, 2])` returns 3.
- Expected: 2.5, and a tier table that reports what ran.
- Command: `tier_check.py PR-BODY.md --rerun --offline`
- Output: `V2 PASS RERUN-FAILED EVIDENCE-MISMATCH(claimed 2 passed, now 1)`, `V5 PASS RERUN-FAILED EVIDENCE-MISMATCH(claimed 3 passed, now 2)`.
- The false PASS is the finding. The fault in the code is its content.

## ex11 · M8 · S1 · must-fix

- Requirement: REQ-002 (MUST).
- Observed: `test_zero_and_negative_rejected` passes the integers 0 and -3, not text, inside `pytest.raises(Exception)`. The error it catches is `AttributeError` from `int.strip`. `parse_quantity("-3")` returns -3 and `parse_quantity("0")` returns 0.
- Expected: `ValueError` for both; the test names `ValueError` and passes text.
- Command: `req_run.py --spec spec.md --tests .` then `mutate_check.py quantity.py:parse_quantity --req REQ-002` then the one-liner.
- Output: `REQ-002 MUST ... BROAD-RAISES`; `gut killed`, `raise SURVIVED`; the one-liner prints `-3`.

## Scoring

Hit: same requirement, same class or an equivalent description, a command with output, the expected tag. Severity within one level. Pass mark: nine of ten, control clean.

Typical misses and what they say:

| Miss | Likely cause |
| --- | --- |
| ex06 | `spec_diff.py` not run, or the spec at HEAD taken as given |
| ex08 | Stopped when the probes were all killed |
| ex03 or ex01 | Probe run without `--req`, so a different test killed it |
| ex05 | Trusted the tag count instead of the collected count |
| must-fix on ex04 | Reporting preferences as defects |
