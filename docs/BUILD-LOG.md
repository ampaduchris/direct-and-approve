# Build log

Append-only. Read first, written last. One row per session.

| Date | Session | Model | Effort (source) | Minutes | Tiers passed | NOT VERIFIED | PR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-11-22 | 9.1 | Sonnet 5.5 (adopted draft: Fable 5.2 / medium, 15 Nov 2026) | high (app session record) | ~22 (from the timer hook start 15:59:00Z; includes this row) | V1-V6 PASS | 6 | https://github.com/ampaduchris/direct-and-approve/pull/1 |

CI versions chosen (standard, "CI"): Python 3.11, 3.12 and 3.13 on ubuntu-24.04. All three were green on the 9.1 head before this row was added (run 45043087859; the final head is linked in the pull request). Scripts and tests use the standard library and pytest only.
