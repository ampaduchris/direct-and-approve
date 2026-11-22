---
name: pre-pr-check
description: Run in every build session before the pull request is opened (`continue` step 8) and again before it is marked ready for review (step 10). Proves that the test for each touched MUST can fail, that every PASS has evidence that resolves, that the NOT VERIFIED count is honest, and that the scrubber has run on the tree, the PR body and the commit messages.
---

# Pre-PR check

You wrote this code and these tests in this session, so you are the worst-placed reader to judge them. This check replaces judgement with four things that can be run. It has two passes: one before the push, one after CI (continuous integration) has finished on the final commit.

The scripts are shared with the independent-review skill. From `repos/<name>/`:

```bash
K=../../.claude/skills/independent-review/scripts
```

## Rules

1. A row is PASS only if a command was run at this commit, in this session, and its output is in the evidence cell or behind the link.
2. A probe that survives is never hidden. Strengthen the test and run it again, or write NOT VERIFIED.
3. Never change a requirement row to make a check pass. A spec change outside a spec session needs an entry in `docs/DEVIATIONS.md` and a `GATE:` line for the owner.
4. If anything below prints an error, the pull request stays a draft.
5. The 45-minute limit still applies. If time runs out, the honest result is more NOT VERIFIED items, not fewer checks.

## Pass 1: before the push

**1. Record the starting state.**

```bash
git status --porcelain; git rev-parse HEAD
```

Everything for the session is committed on `s/<session-id>`. Keep this output: step 5 compares against it.

**2. List the MUSTs this session touched.** A MUST is touched if its code or its test changed.

```bash
git diff --name-only main...HEAD
git diff main...HEAD -- tests | grep -oE "REQ-[0-9]+" | sort -u
git diff main...HEAD -- docs/spec.md | grep -E "^[-+]\| REQ-"
```

Add the ids named in the confirmation gate. The third command must print nothing unless this is a spec session; if it prints a row, apply rule 3 before going on.

**3. Trace by running.**

```bash
uv run python $K/req_run.py --spec docs/spec.md
```

No touched MUST may carry a flag. A flag on a MUST from an earlier session is not yours to fix here: list it under "Not verified" and tell the owner in the report.

**4. Break the code behind each touched MUST and watch its test fail.**

```bash
uv run python $K/mutate_check.py src/<package>/<file>.py:<function> --req REQ-0NN
```

The tool empties the function, makes it raise, and inverts its logic, runs the tagged tests each time, and restores the file. The wanted output is three lines saying `killed` and `result: all probes killed`. For any `SURVIVED`:

| Output | What to do |
| --- | --- |
| `gut SURVIVED` and `raise SURVIVED` | The test does not run this code. Remove the patch or fix the fixture so the real function is called |
| `gut SURVIVED`, `raise killed` | Nothing about the result is asserted. Assert the exact value the spec gives |
| `raise SURVIVED`, `gut killed` | Any exception passes. Name the exception type and match its message |
| only `flip SURVIVED` | The assertion is too weak. Run with `--show`, see which wrong behaviour passes, assert against it |
| `NO TESTS SELECTED` | No collected test carries the tag. Tag the test, or find why it is not collected |
| `n/a` | The probe had nothing to change. That is not a survivor |

Commit the stronger test and run the probe again. If you cannot make it fail in the time left, the V4 row for that requirement is NOT VERIFIED and the probe output goes in the list.

Where the code behind a MUST is not a Python function (a workflow file, a configuration value, TypeScript, a document), do the same by hand: delete or invert the line, run the check that should catch it, paste the red line, then `git checkout -- <file>`.

In a test-first session the red CI run already shows the tests fail with no implementation. Link it, and still run the probe: `flip` tests something the red run does not.

**5. Confirm nothing was left behind.**

```bash
git status --porcelain; git rev-parse HEAD
```

The output must equal step 1, apart from commits you made on purpose in step 4.

**6. Write the PR body file.** Keep it outside the repository, in the session's scratch folder. Beside what `CLAUDE.md` step 9 lists, it carries these three parts in this form:

```markdown
## Tier table
| Tier | Check run | Command | Result | Evidence |
| --- | --- | --- | --- | --- |
| V1 | ... | `one command in backticks` | PASS | pasted output line, or a CI run link |
| ... |
| V6 | What was not verified | listed below | PASS | 2 item(s) under Not verified |

## Not verified
- One list item per gap. See the rules below.

## Pre-PR check
| Check | Result |
| --- | --- |
| Requirements touched | REQ-014, REQ-015, REQ-016 |
| Requirement run | 3 of 3 clean; suite: 41 passed |
| Probes | REQ-014: gut killed, raise killed, flip killed. REQ-015: ... |
| Skipped or expected-to-fail tests | 0 in the suite; 0 added this session |
| Requirement rows changed | none |
| Tier table check | 0 errors, 0 warnings |
| Not verified | 2, listed above |
| Scrubber | tree CLEAN, body CLEAN, commit messages CLEAN, names CLEAN |
```

Paste probe results as printed. Never write "killed" for a probe you did not run. V6 is PASS when the list exists and its count is right; a V1 to V5 row that was not run is NOT VERIFIED and appears in the list.

**7. Check the tier table by running it.**

```bash
uv run python $K/tier_check.py <body file> --rerun --cwd .
```

It runs each command in the Command column again and compares. Zero errors is required. Each warning is either fixed or becomes a "Not verified" item.

**8. Run the scrubber on everything that will be public.**

```bash
python3 ../../tools/scrub.py .
python3 ../../tools/scrub.py <body file>
git log main..HEAD --format='%s%n%b' > <scratch>/commits.txt && python3 ../../tools/scrub.py <scratch>/commits.txt
{ git diff --name-only main...HEAD; git branch --show-current; echo "<the PR title>"; } > <scratch>/names.txt && python3 ../../tools/scrub.py <scratch>/names.txt
```

Each must print `CLEAN`. `NO DENYLIST LOADED` is not clean. A hit in a commit message means the commit is rewritten before the push, on the same day, without changing any date.

## What counts as not verified

Not verified means: not run at this commit, in this session. Each of these is one list item:

- a tier row whose command was not run;
- a MUST that was touched and not probed, or whose probe survived and was not fixed;
- a skipped or expected-to-fail test, named, with its reason;
- a Python or Node version in the CI matrix not seen green;
- a model output checked fewer than three times (all three results are reported when it is checked);
- a number in the README or the PR body that no command in this session reproduced;
- a behaviour the spec names that no test or command reached: an operating system, a file size, an input class.

A check run in an earlier session, on an earlier commit, or only reasoned about, is not verified. Do not merge two gaps into one item. Do not move an item to "Deviations" to shorten the list. Zero items is allowed only with one sentence saying why nothing was out of reach; most sessions have at least one.

The count appears in three places and must be the same number in each: the list, the V6 evidence cell, and the BUILD-LOG row.

## Pass 2: after the push, before "ready for review"

The BUILD-LOG row is itself a commit, so it moves the head. Evidence must belong to the final head.

1. Open the draft pull request, append the BUILD-LOG row with the real link and the Not verified count, push.
2. When CI has finished on that head commit, replace pasted evidence with the run link wherever a CI job ran the same command. Keep pasted lines for checks CI does not run. Update the body from the file.
3. Check the published body against GitHub and the log:

```bash
uv run python $K/tier_check.py --pr <number> --build-log docs/BUILD-LOG.md --session <session-id>
```

`RED-EVIDENCE` means the linked run failed. `STALE-EVIDENCE` means the link is to a run for an older commit: link the run for the head. `NV-COUNT-MISMATCH` means the three counts differ. Zero errors, then mark the pull request ready for review.

4. In the five-line report to the owner, give the Not verified count and name any probe that survived.

## What this check does not do

It shows that the tests for the touched MUSTs can fail and that the claims in the body match what ran. It does not show the tests mean what the spec means, and it cannot see code written to fit the test inputs. The independent review session looks for both.
