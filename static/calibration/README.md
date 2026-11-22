# Calibration set for the independent-review skill

The answers are public, so this set is for demonstration only. A model that can read `_answers/` has not been calibrated by running the set. It shows what the commands expose.

Eleven tiny synthetic Python projects, `ex01` to `ex11`. Ten carry one planted defect each, one for each entry in the skill's taxonomy (M1 to M10). One is a control with no planted defect. The order is shuffled and the file names say nothing.

## What is in each example

| File | Stands for |
| --- | --- |
| `spec.md` | `docs/spec.md` at HEAD |
| `spec.adopted.md` | the spec as the owner first adopted it. It stands in for the git history |
| `<module>.py` | the code |
| `test_<module>.py` | the tests, tagged `@pytest.mark.req("REQ-###")` |
| `PR-BODY.md` | the body of the pull request that added the code, with its tier table |

## Prove that every planted defect is exposed

`_answers/prove.py` runs the kit scripts on all eleven examples, checks that each planted defect is exposed by its command and that the control is clean, and writes its transcript to `PROOF.txt` in the system temporary folder. The `_answers/PROOF.txt` in this folder is the transcript of one earlier run. The proof leaves no cache and no bytecode in this folder. From the root of the control folder (the folder that holds `.claude/` and `calibration/`):

```bash
uv run --with pytest python calibration/_answers/prove.py
```

## A real calibration

To calibrate a reviewer, give it `ex01` to `ex11` without `_answers/`, score its findings against `_answers/EXPECTED.md` afterwards, and write a new set of examples if the old one has been read. Change nothing in the examples; `mutate_check.py` restores what it touches, so `git status --porcelain calibration` is empty afterwards.
