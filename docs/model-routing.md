# Model routing

Which model runs which session, and what the record shows. This page states a rule and reports what was used. It does not say that one model is better than another.

## The rule

1. There is a default model. A session line that asks for no switch uses it.
2. A review runs on a model that differs from the author of the thing reviewed. The aim is that the reviewer is not the author's own model.
3. Every session line in `SESSIONS.md` names its model and its effort. `scripts/check_sessions.py` fails a line that does not.
4. A line that asks for a switch carries two things: the reason, and the risk of staying on the current model.
5. The owner's choice is never refused. If the model or effort in the app's session record differs from the session line, the agent says so, then runs on the owner's choice and records it in the BUILD-LOG row.

The text of the rule is in [`method/CLAUDE.md`](../method/CLAUDE.md), section "Model advice", and in step 4 of the `continue` procedure.

## What the sessions used

The data is a copy of the BUILD-LOG of the inkproof repository at a pinned commit: [`docs/data/inkproof-BUILD-LOG.md`](data/inkproof-BUILD-LOG.md). Its first line names the repository, the file and the commit hash. This repository's own log is [`docs/BUILD-LOG.md`](BUILD-LOG.md).

The block below is the output of `scripts/routing.py` on that copy. A test compares this block with a fresh run, so the numbers cannot drift from the data.

```bash run
python3 scripts/routing.py docs/data/inkproof-BUILD-LOG.md
```

```text
Sessions by model and effort (12 sessions)
  Opus 5.5 / high: 1
  Sonnet 5.5 / high: 5
  Sonnet 5.5 / low: 1
  Sonnet 5.5 / medium: 5
total minutes: 166 (12 sessions)
total NOT VERIFIED: 62 (12 sessions)
effort not machine-verified: 0 (12 sessions)
```

## How the script reads the log

- The model is the name and version at the start of the model cell. Where a row says a draft from another model was adopted, the draft's model is in the cell but the session is counted under the model that ran it.
- The effort is the first word of the effort cell. A row whose effort changed during the session is counted under its first word, and its cell says what changed. In this log that applies to session 1.10.
- Minutes are the first number in the minutes cell. A row that says "estimated" is counted at its estimate.
- "Effort not machine-verified" counts rows that say so. A row with no such note had its effort read from the app's session record.
- A malformed row (missing column, non-numeric minutes or count, duplicate id) stops the script with the line number. No total is printed.

## What the numbers do not show

- They come from one repository, one person and one tool (limits LIM-2 and LIM-3). The count of sessions is printed beside every figure.
- One session in the log is a review, so the log holds one case of a reviewer that differs from the author. It says nothing about how often that matters.
- The NOT VERIFIED total counts items the sessions listed themselves. It is not a count of defects, and a session that lists fewer items did not necessarily check more.
- Minutes are the agent's own estimate from the timer hook or the clock. They are not billed time.
