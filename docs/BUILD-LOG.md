# Build log

Append-only. Read first, written last. One row per session.

| Date | Session | Model | Effort (source) | Minutes | Tiers passed | NOT VERIFIED | PR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-11-22 | 9.1 | Sonnet 5.5 (adopted draft: Fable 5.2 / medium, 15 Nov 2026) | high (app session record) | ~22 (from the timer hook start 15:59:00Z; includes this row) | V1-V6 PASS | 6 | https://github.com/ampaduchris/direct-and-approve/pull/1 |
| 2026-11-22 | 9.2 | Sonnet 5.5 | high (app session record) | ~14 (timer hook start 16:27:01Z to about 16:41Z by the clock; includes this row) | V1-V6 PASS | 8 | https://github.com/ampaduchris/direct-and-approve/pull/3 |
| 2026-11-22 | 9.3 | Sonnet 5.5 | medium (app session record) | ~30 (timer hook start 16:56:38Z to about 17:27Z by the clock; includes this row) | V1-V6 PASS | 7 | https://github.com/ampaduchris/direct-and-approve/pull/4 |
| 2026-11-22 | 9.4 | Opus 5.5 | high (app session record) | ~24 (timer hook start 17:37:22Z to about 18:01Z by the clock; includes this row; fourth build session on 22 Nov, past the two-a-day limit at the owner's choice) | V1-V6 PASS | 10 | https://github.com/ampaduchris/direct-and-approve/pull/10 |
| 2026-11-22 | 9.5 | Sonnet 5.5 | high (app session record; the session line asks for medium, owner typed `proceed anyway`) | ~35 (timer hook start 18:27:52Z to about 19:03Z by the clock; includes this row) | V1-V6 PASS | 8 | https://github.com/ampaduchris/direct-and-approve/pull/11 |

CI versions chosen (standard, "CI"): Python 3.11, 3.12 and 3.13 on ubuntu-24.04. All three were green on the 9.1 head before this row was added (run 45043087859; the final head is linked in the pull request). Scripts and tests use the standard library and pytest only.
