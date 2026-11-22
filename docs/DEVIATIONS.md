# Deviations

Every departure from `docs/spec.md`, numbered, with the reason. Any hand edit to code by the owner is logged here. Session 9.1 also logs the places where the adopted spec differs from the build brief (`BUILD.md` in the private control folder), so that the owner sees each one.

| # | Departure | Reason | Logged |
| --- | --- | --- | --- |
| DEV-001 | CI runs `scripts/trace.py --report-only` while the build is CURRENT. REQ-120 and the standard's R1 say it fails on an untested MUST. | Most MUSTs have no test until sessions 9.2 and 9.3. Session 9.5 removes the flag, so the released workflow fails on an untested MUST. | 9.1 |
| DEV-002 | `scripts/trace.py` is the inkproof copy with two changes: the scope table is found by its "Scope to requirements" heading (section 16.1), not by the heading number 11.1, and its header row reads "BUILD.md scope bullet". | The two specifications number their sections differently. No logic changed. | 9.1 |
| DEV-003 | Section 2 of the draft said `trace.py` builds its matrix from a test run. It reads the `@pytest.mark.req` tags in the test source and counts them; the workflow runs the tests first and fails if any fail. Section 2 now says that. | The draft described a script that does not exist. A tag on a failing test never reaches `trace.py` because CI has already failed. | 9.1 |
| DEV-004 | The owner chose, at the 9.1 GATE on 22 Nov 2026, not to publish the upstream procedure. `BUILD.md` proposed yes. REQ-014 is withdrawn. | Owner decision. No upstream item has been filed by the procedure yet. | 9.1 |
| DEV-005 | The owner chose, at the same GATE, to publish `tools/brief.py` and `tools/section.py`, which `BUILD.md` lists in no row. REQ-016 and LIM-8 are new. | Owner decision. `method/CLAUDE.md` cites both tools. Open point N11 records that `brief.py` as it stands names unpublished builds and reads the upstream ledger, so 9.2 must resolve that before the entry can be written. | 9.1 |
| DEV-006 | `BUILD.md` scope S6 says "the five scripts". The kit holds six (`literal_overlap.py`, `mutate_check.py`, `req_run.py`, `reqprobe.py`, `spec_diff.py`, `tier_check.py`). The spec says six (REQ-071). | A count in the brief that was never checked against the folder. | 9.1 |
