# Worked example: one session from instruction to merge

One real session of the [inkproof](https://github.com/ampaduchris/inkproof) repository, session 1.5, written test-first. Every step links to its source. Every quotation below is compared by a test with the pull request record saved in [`docs/data/worked-example.json`](data/worked-example.json), fetched on 2026-11-22 by `scripts/snapshot_pr.py`. Nothing inside a quotation is paraphrased.

The session was chosen because it is test-first and because its list of what was not verified is not empty. It is one session. It is not a sample.

## 1. The session line as written

The agent follows the session line of the plan. This is the line as first written in the private control folder on 15 Nov 2026, before the session ran. The control folder is private, so the line is copied to [`docs/data/worked-example-session-line.md`](https://github.com/ampaduchris/direct-and-approve/blob/54e790db8f3dc12c94622d0036f717441f939d0c/docs/data/worked-example-session-line.md).

> - [ ] **1.5 Audit mode and hidden text (TDD)** · Sonnet 5.5 / high
>   - Failing tests for every planted fixture, then the detectors.
>   - Exit test: every planted leak caught; no control file flagged.

## 2. The confirmation gate

Before changing anything, the agent writes five lines: objective, specification sections touched, exit test, what it will not do, first file it will change. They are the first section of the [pull request body](https://github.com/ampaduchris/inkproof/pull/7).

> - Objective: `inkproof audit FILE --terms --patterns` with leak detection on every surface S1 to S11, earlier revisions, leak classes for page text, the JSON report, and the audit column of the exit codes and output hygiene.
> - Spec sections touched: 7 to 7.2 (REQ-055 to 058, 060, 061, 065 to 072, 074), 5.1 (REQ-002 to 005 for audit), 8 (REQ-075 to 078 for audit reports), 9 (REQ-080, 081, 082, 085, 088 for audit). `apply` changes only to share code.
> - Exit test: every planted leak is caught with the class the spec names; control C01 and R1 report no leak; audit never changes the file.
> - Will not do: Hypothesis properties (1.6), mutation testing (1.9), the SHOULD classes `tiny`, `clipped` and `hidden-layer` (REQ-073), any spec change without a DEVIATIONS row, any real document, any model call, any network access.
> - First file changed: new failing tests in `tests/test_audit.py`. Red run (35 failing, audit module absent): https://github.com/ampaduchris/inkproof/actions/runs/44787191933

## 3. The failing run

The agent commits and pushes the failing tests first, so that a red run exists. The [run](https://github.com/ampaduchris/inkproof/actions/runs/44787191933) ended in `failure`. The gate above names it.

## 4. The passing run

After the code, the [run](https://github.com/ampaduchris/inkproof/actions/runs/44787865644) for the final commit ended in `success`. The pull request had 4 commits: the failing tests, the code, stronger tests, and the build log row.

## 5. The tier table

Every pull request carries one row per verification tier, V1 to V6, with the command run and its evidence. This is the table of [pull request 7](https://github.com/ampaduchris/inkproof/pull/7).

> | Tier | Check run | Command | Result | Evidence |
> | --- | --- | --- | --- | --- |
> | V1 | The tool runs and has the `audit` command | `uv run inkproof --version` | PASS | `0.0.0`; audit help lists all exit codes (`test_audit_help_documents_exit_codes`) |
> | V2 | Planted leaks are found with the class the spec names, on every surface | `uv run pytest -q --tb=line -k "test_class_ or test_audit_surfaces or test_incremental_update_leak or test_annotation_leaks or test_non_page_surface_leaks"` | PASS | 11 passed, 380 deselected |
> | V3 | It fails correctly: no source, unknown pattern, unreadable file, internal error, file unchanged | `uv run pytest -q --tb=line -k "test_audit_requires_a_source or test_audit_unknown_pattern or test_audit_unreadable_documents or test_exit_codes_audit or test_audit_internal_error_is_masked or test_audit_does_not_modify"` | PASS | 6 passed, 385 deselected |
> | V4 | Trace matrix: every MUST touched has a test; the untested ones are not this session's (listed below) | `uv run python scripts/trace.py --report-only` | PASS | `79 requirements, 3 untested MUST, 18 scope rows, 0 errors`; the 3 are REQ-090, 091, 092; probes under Pre-PR check |
> | V5 | Nothing that worked before broke | `env PYTHONWARNINGS=ignore uv run pytest -q --tb=line -p no:warnings` | PASS | 391 passed; CI https://github.com/ampaduchris/inkproof/actions/runs/44787865644 |
> | V6 | What was not verified | listed below | PASS | 8 item(s) under Not verified |

## 6. Not verified

The agent lists what it did not check. This session listed 8 items, in its own words, in the same [pull request body](https://github.com/ampaduchris/inkproof/pull/7).

> - Leak classes on rotated pages, text under a clipping path, a match that spans spans of different colour, a filled shape that is not a rectangle and an image with a soft mask: no fixture reaches them (spec 12.3b).
> - Files whose objects sit in object streams, and files with more than two revisions: not generated, not audited.
> - A page-text match that only pdfminer.six finds: the code path is tested with the trace stubbed out, and no real fixture produces such a match.
> - REQ-073 (SHOULD): the classes `tiny`, `clipped` and `hidden-layer` are not built.
> - REQ-093 (SHOULD): audit speed on a 100-page file is not measured.
> - REQ-090 (earlier session, flagged by `req_run.py`): no test carries the tag; the matrix itself (3.11, 3.12, 3.13) and gitleaks ran green in CI for this head.
> - REQ-091 (earlier session, flagged by `req_run.py`): `test_all_fixtures_regenerate_byte_identically_*` exist but carry no `REQ-091` tag. Fixture A06 changed in this session; the tests pass.
> - REQ-092 (session 1.9): mutation score floor not measured. Hand probes only, below.

## 7. The BUILD-LOG row

The last commit of the pull request adds one row to the repository's build log: model, effort and where the effort was read from, minutes, tiers passed and the count of items not verified. This is the row, in [the log at the release commit](https://github.com/ampaduchris/inkproof/blob/1cef639809c2779c19e4783eaa0c53ba471ad290/docs/BUILD-LOG.md).

> | 2026-11-20 | 1.5 | Sonnet 5.5 | high (app session record) | 14 (from the timer hook start 17:41:36Z) | V1-V6 PASS | 8 | https://github.com/ampaduchris/inkproof/pull/7 |

## 8. The owner's merge comment

The method asks the owner to write a comment on each pull request naming what was checked, then merge (control R8). On this pull request there is none. The record saved on 2026-11-22 holds 0 comments, 0 reviews and 0 review comments. See [the conversation of pull request 7](https://github.com/ampaduchris/inkproof/pull/7).

This is a gap between the method as written and the method as practised. It is stated here, not repaired. A comment written now would not be a contemporary record, so none is shown.

## 9. The time from opening to merge

The [pull request](https://github.com/ampaduchris/inkproof/pull/7) was opened at 2026-11-20T17:50:53Z and merged at 2026-11-20T17:58:29Z by `ampaduchris`, the account that opened it. That is 7.6 minutes. The final green run was created at 2026-11-20T17:55:19Z, so the merge came 3.2 minutes after it.

The ruleset requires a pull request and green checks. It does not require that anyone read the change in that time (limit LIM-1). Whether 7.6 minutes is enough to check a change of this size is for the reader to judge. The method publishes the figure and does not judge it.
