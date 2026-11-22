# The review kit

The kit is the [`independent-review`](../method/.claude/skills/independent-review/SKILL.md) and [`pre-pr-check`](../method/.claude/skills/pre-pr-check/SKILL.md) skills with their scripts, and a set of eleven small examples in [`method/calibration/`](../method/calibration/README.md), each with one planted defect. The skill lists ten ways that agent-written code and tests mislead. This page gives, for each, the command that exposes it and the example that plants it.

The examples and their answers are public. A model that can read the answers has not been calibrated by them (limit LIM-6). The set shows that each command exposes its defect; it does not measure a reviewer.

| Id | The way it misleads | The command that exposes it | Planted in |
| --- | --- | --- | --- |
| M1 | The test asserts the mock | `mutate_check.py <file>:<function> --req <id>`: `gut SURVIVED` and `raise SURVIVED` | ex03 |
| M2 | A requirement tag on a test that asserts nothing | `req_run.py --spec <spec> --tests <dir>`: `ZERO-ASSERT`, `0 asserts executed (0 written)` | ex09 |
| M3 | A skipped or expected-to-fail test | `req_run.py`: `XFAIL` or `SKIPPED`, then `NO-PASSING-TEST` | ex02 |
| M4 | A spec requirement reworded to fit the code | `spec_diff.py --base <commit>`: `TEXT-CHANGED`, `NO-DEVIATION` | ex06 |
| M5 | A fixture that cannot fail | `req_run.py`: `ZERO-ASSERT`, `0 asserts executed (N written)`; `mutate_check.py`: `gut SURVIVED` | ex07 |
| M6 | A tier row marked PASS whose evidence is red or missing | `tier_check.py <body> --rerun`: `RERUN-FAILED`, `EVIDENCE-MISMATCH` | ex10 |
| M7 | An assertion too weak to tell right from wrong | `mutate_check.py`: `gut killed`, `raise killed`, `flip SURVIVED` | ex01 |
| M8 | A test that passes on the wrong exception | `req_run.py`: `BROAD-RAISES`; `mutate_check.py`: `raise SURVIVED` | ex11 |
| M9 | A tagged test that is never collected | `req_run.py`: `NOT-COLLECTED`, `never ran: <file>::<function>` | ex05 |
| M10 | Code that special-cases the test inputs | `literal_overlap.py --src <dir> --tests <file>`: `OVERLAP` | ex08 |

`ex04` is the control: every command exits 0 on it. A kit that flags the control is wrong, not careful.

To run all of it, `uv run --locked python method/calibration/_answers/prove.py` runs the five scripts on the eleven examples and fails unless every planted defect is exposed and the control is clean. CI runs the same proof on every pull request (the `kit` job).
