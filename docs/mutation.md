# Mutation testing result (control R2)

Run in session 9.5 on 22 November 2026, macOS, Python 3.13, mutmut 3 from the lockfile. The spec sets no floor, so this reports what was done and what was not.

## mutmut: not run to completion

mutmut was tried three times on `scripts/extract.py`, `scripts/check_sessions.py` and `scripts/routing.py`. Each time it stopped while collecting statistics, before it mutated anything.

| Attempt | Setting | What stopped it |
| --- | --- | --- |
| 1 | default paths | `tests/test_ci.py` reads `.github/workflows/ci.yml`, which mutmut did not copy into its working folder |
| 2 | that file copied | `test_output_does_not_depend_on_locale_or_working_directory` runs the script from another folder, where mutmut's rewritten script cannot find its configuration |
| 3 | all files copied | `FileNotFoundError` for `portfolio.yml` in the first attempt's folder, then, once copied, mutmut's key check: it expects tests to import `scripts.extract`, and this suite puts `scripts/` on `sys.path` and imports `extract` |

Making mutmut work needs the suite's imports and its subprocess tests changed. That is a change to every test file and was not made in a release session. No mutmut score exists and none is claimed. The three-attempt configuration was removed again from `pyproject.toml`.

## What was run instead

The review kit's `mutate_check.py` breaks one function three ways (empty body, raise, flip a condition) and runs the tests tagged with the function's requirement ids. It is a function-level probe, not a mutation score.

| Function | Requirements | gut | raise | flip |
| --- | --- | --- | --- | --- |
| `routing.py:parse` | REQ-086, 087 | killed | killed | killed |
| `routing.py:summarise` | REQ-086, 088 | killed | killed | killed |
| `routing.py:render` | REQ-088 | killed | killed | killed |
| `check_sessions.py:check_sessions_file` | REQ-051 to 054, 056 | killed | killed | killed |
| `check_sessions.py:check_plan` | REQ-055 | killed | killed | killed |
| `trace.py:doc_only` | REQ-120 | killed | killed | killed |
| `extract.py:write_out` | REQ-034 | killed on all 3 runs of the `gut` probe | not run | not run |

Review 9.4 ran the same probe on 15 functions of `scripts/` for 13 MUSTs. It found one survivor, `extract.py:write_out` (F-05, `gut` survived 3 of 3). Session 9.5 added three tests; the `gut` probe then killed it on 3 of 3 runs.

## Not verified

- Every function of the three files that neither this session nor review 9.4 probed.
- The `raise` and `flip` probes on `write_out` after the fix.
- Any mutation of the 40 MUSTs that review 9.4 lists as not probed.
- No surviving mutant exists to review, because mutmut produced none.
