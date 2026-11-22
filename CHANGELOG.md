# Changelog

All notable changes are listed here. The format follows Keep a Changelog.

## 1.0.0

First release. The published method, the scripts that check it, and one real session traced from instruction to merge.

### Added

- `method/`: the procedure, the standard, the session format with a synthetic example build, the frontload pattern, the review and verification kit, the calibration set, the scrubber without a list, and `SETUP.md`. Built by `scripts/extract.py` from a private control folder, source date 2026-11-22.
- `scripts/`: `extract.py`, `check_sessions.py`, `routing.py`, `trace.py`, `boundary.py`, `run_blocks.py`, `check_links.py`, `check_imports.py`, `ci_checks.py`, `snapshot_pr.py`.
- `docs/`: the specification, the worked example, the model-routing numbers, the frontload pattern, the command words (`procedure.md`), the review kit (`review-kit.md`), what stays private, the session format, the independent review of session 9.4 and the result of mutation testing.
- CI on Python 3.11, 3.12 and 3.13: tests, requirement traceability, manifest check, privacy boundary, scrubber, a scripts job with no dependencies installed, the calibration proof, the start-your-own copy, the blocks marked `bash run` run twice, link check, gitleaks.

### Fixed (from the review of session 9.4)

- The README proof command left caches in `method/` and made the test suite fail on its second run (issue 5).
- The three documents that REQ-013, 075 and 110 require did not exist (issue 6).
- Five MUSTs had no test or CI job as their rows say (issue 8); the REQ-034 tests passed with `write_out` removed (issue 9).
- `trace.py` fails CI on an untested MUST. Rows proved only by a document print DOC-ONLY.
- `method/SETUP.md` step 6 no longer leaves two `CURRENT` phases; the third missing file (`UPSTREAM.md`) is named.

### Departures

Deviations DEV-001 to DEV-023 are in `docs/DEVIATIONS.md`. The weekly scheduled run was never added (DEV-018, issue 7). `brief.py` is not published; REQ-016 covers `section.py` only (DEV-020). Mutation testing with mutmut could not be run (`docs/mutation.md`).
