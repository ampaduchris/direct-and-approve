---
name: independent-review
description: Independent review of agent-written code and tests against the spec. Use in every review session of a build. Runs the commands that expose misleading tests and false PASS claims, then writes numbered findings with severity. Changes no code.
---

# Independent review

You are reviewing work that another model wrote. The suite is green and the tier tables say PASS. Your job is to find where that is not true. Agent-written tests mislead in a small number of repeatable ways. Each one has a command that exposes it. Run the command. Do not decide by reading.

## Rules

1. Change no code, no test and no spec. The only files you add are the review file and, for must-fix findings, issues.
2. Your model must differ from the model that wrote the thing reviewed. Read the builder's model from `docs/BUILD-LOG.md` and your own from the session record. If they match, say so in the review header.
3. A finding needs a command and its output. A finding from reading alone says "read, not run" and is never must-fix until it has been run.
4. Any check of model output runs three times. Report all three.
5. Never approve and never merge. The owner does both.
6. The review file and every issue text pass `python3 ../../tools/scrub.py <file>` before they are committed or posted.
7. NOT VERIFIED is cheaper than a false finding and cheaper than a false "clean". List what you did not run.

## The kit

Five scripts live beside this file in `scripts/`. From a repo in `repos/<name>/`:

```bash
K=../../.claude/skills/independent-review/scripts
```

Run them with the project's interpreter (`uv run python $K/...` in the build repos). Each prints `--help`.

| Script | What it does |
| --- | --- |
| `req_run.py` | Runs the suite and prints, for each requirement id, the tagged tests, whether they ran, their outcomes and how many asserts executed |
| `mutate_check.py` | Breaks one function three ways, runs its tests each time, restores the file |
| `spec_diff.py` | Lists every requirement row that changed after the spec was adopted |
| `tier_check.py` | Checks a pull request body: every tier row, every PASS and its evidence, the Not verified count |
| `literal_overlap.py` | Finds test inputs that also sit in the source as literals |

## Order of work

**Step 0. Set up.** Record the commit under review (`git rev-parse HEAD`), your model and effort, and the builder's. If this is the first review session of the programme, run the calibration first: `calibration/README.md`. It takes about ten minutes and its score goes in the review header.

**Step 1. Pass A: spec and code only.** Do not open `docs/BUILD-LOG.md`, `docs/DEVIATIONS.md`, pull request bodies or earlier reviews yet. They are the builder's account, and you are checking the work, not the account.

```bash
uv run pytest -q -rsxX                                   # the suite, with every skip and xfail named
uv run python $K/req_run.py --spec docs/spec.md          # trace by running
uv run python $K/literal_overlap.py --src src --tests tests
git log --first-parent --date=short --format='%h %ad %s' -- docs/spec.md
uv run python $K/spec_diff.py --base <commit of the spec session>
```

Then probe. For each MUST, find the function that implements it and run:

```bash
uv run python $K/mutate_check.py src/<package>/<file>.py:<function> --req REQ-0NN
```

Order the probes: first every MUST that `req_run.py` flagged, then the MUSTs behind the headline claim in the README, then the rest. If the time limit stops you, list the MUSTs you did not probe under "Not verified by this review". Last, read each MUST against the code that implements it, line by line. The scripts find tests that cannot fail. Only reading finds a requirement nobody tested at all the way the spec means it.

**Step 2. Pass B: the claims.** Now open the builder's account and check it against what Pass A found.

```bash
gh pr list --state merged --limit 50 --json number,title
uv run python $K/tier_check.py --pr <n> --build-log docs/BUILD-LOG.md --session <id>   # each session of the build
```

Run every command in the README's "Verify it yourself" block. Compare `docs/DEVIATIONS.md` with the output of `spec_diff.py`: every changed row needs an entry. A tier row that says PASS for something Pass A showed red, skipped or unproven is a finding (M6).

**Step 3. Write up.** One file, `docs/reviews/<session-id>.md`, in the format below. One issue per must-fix finding. Then follow the session's own steps for the pull request.

## The ways agent-written code and tests mislead

Each entry: what it looks like, the command that exposes it, and what the output shows when it is present.

**M1. The test asserts the mock.** The function under test is patched, or the assertion is about a mock's return value. The real code never runs.
`mutate_check.py <file>:<function> --req REQ-0NN` prints `gut SURVIVED` and `raise SURVIVED`. To find candidates: `grep -rnE "patch\(|monkeypatch\.setattr|Mock\(|MagicMock\(" tests/`, then check whether the patched name is the thing the requirement is about.

**M2. A requirement tag on a test that asserts nothing.** The test calls the code and stops, or it compares with `==` and forgets `assert`.
`req_run.py` prints `ZERO-ASSERT` with "passed with 0 asserts executed (0 written)". The probe prints `gut SURVIVED` and `raise killed`: the code runs, and nothing about its result is checked.

**M3. A skipped or expected-to-fail test.** `skip`, `skipif`, `xfail`, `importorskip`, or a deselection in the configuration. The suite is green and the requirement has no passing test.
`req_run.py` prints `SKIPPED`, `XFAIL` or `XPASS`, and `NO-PASSING-TEST` when nothing else covers the id. `uv run pytest -q -rsxX` names each one with its reason. `uv run pytest -q --runxfail` shows what the xfail hides. For deselection: `grep -nE "addopts|testpaths|norecursedirs|collect_ignore|deselect" pyproject.toml pytest.ini setup.cfg tox.ini tests/conftest.py`.

**M4. A spec requirement reworded to fit the code.** At HEAD the spec, the code and the test agree. The requirement the owner adopted said more.
`spec_diff.py --base <adoption commit>` prints the old and new row with `TEXT-CHANGED`, `LEVEL-DOWN`, `REMOVED` or `WITHDRAWN`, plus `WITH-CODE` when the same commit changed code and `NO-DEVIATION` when `docs/DEVIATIONS.md` does not name the id. Then test the code against the old text yourself.

**M5. A fixture that cannot fail.** The test data makes the assertion empty. Three forms: the fixture yields nothing, so a loop body never runs; the expected value is computed by the code under test, so both sides move together; the planted error is missing from the fixture that should carry it.
`req_run.py` prints `ZERO-ASSERT` with "0 asserts executed (N written)", N above zero: the asserts exist and none ran. The probe prints `gut SURVIVED`; for an empty fixture also `raise SURVIVED`. For golden files, check who wrote them: `git log --format='%h %s' -- <golden file>` against the commits of the code that produces them. For a planted-error fixture, run the detector on a copy with the planted item removed. The answer must change.

**M6. A tier row marked PASS whose evidence is red or missing.** The cell is empty, says "see CI", links a failed run, links a run for an older commit, or pastes a count the command does not give.
`tier_check.py --pr <n>` prints `NO-EVIDENCE`, `RED-EVIDENCE`, `STALE-EVIDENCE`, `PENDING-EVIDENCE` or `UNRESOLVED-LINK`. On a local body file, `tier_check.py <body> --rerun` runs each command again and prints `RERUN-FAILED` or `EVIDENCE-MISMATCH`. A PASS with skips in its evidence prints the warning `PASS-WITH-SKIPS`.

**M7. An assertion too weak to tell right from wrong.** The test checks a type, a key, a length, "not None", an exit code, or that some marker appears. Wrong output passes.
`mutate_check.py` prints `gut killed`, `raise killed` and `flip SURVIVED`. Run it with `--show` and say in the finding which part of the requirement the surviving version breaks.

**M8. A test that passes on the wrong exception.** `pytest.raises(Exception)`, or a `try` with a bare `except`, satisfied by a `TypeError` from a wrong call instead of the error the spec names.
`req_run.py` prints `BROAD-RAISES` or `SWALLOWS`. The probe prints `raise SURVIVED` while `gut` is killed: any exception will do. Then call the function once with a well-typed bad input, for example `uv run python -c "from pkg.mod import f; print(f('-3'))"`, and compare with the spec.

**M9. A tagged test that is never collected.** A second function with the same name replaces it, the file or class name does not match the collection pattern, or the continuous integration (CI) job never runs that folder. A trace that reads tags counts it. Nothing runs it.
`req_run.py` prints `NOT-COLLECTED` with "never ran: file::function (line N)". Cross-check the counts: `uv run pytest --collect-only -q | tail -1` against `grep -rcE "^\s*(async )?def test_" tests/`. For CI: `gh run view <id> --log | grep -E "[0-9]+ passed"` must match the local count, and `grep -nE "\|\| true|continue-on-error|if: false" .github/workflows/*.yml` must print nothing.

**M10. Code that special-cases the test inputs.** A lookup table, a "fast path" or a cache holds exactly the values the tests use, or the code checks whether it is under test. Every test passes and every probe is killed.
`literal_overlap.py --src src --tests tests` prints `OVERLAP` for each shared literal and `TEST-AWARE` for test detection. Then try one input of the same kind that appears in no test and work out the right answer independently.

### Reading the probe

| `mutate_check.py` output | Meaning | Usual class |
| --- | --- | --- |
| `gut SURVIVED` and `raise SURVIVED` | The tests never execute this code | M1, M5 |
| `gut SURVIVED`, `raise killed` | The code runs and nothing about its result is asserted | M2, M5 |
| `raise SURVIVED`, `gut killed` | Any exception satisfies the test | M8 |
| only `flip SURVIVED` | The assertions cannot tell right from wrong | M7 |
| `NO TESTS SELECTED` | No collected test carries that requirement id | M9, M3 |
| all killed | The tests can fail. It does not show the code is right: see M4 and M10 |

## Severity

Severity follows the claim that is affected, not the size of the change.

| Level | When | Tag |
| --- | --- | --- |
| S1 Critical | A MUST is false at the commit reviewed and a command shows it. Or a public claim is false: a README number, a tier row marked PASS on a red run. Or a matched value, secret or personal detail is exposed | must-fix, always |
| S2 Major | A MUST is unproven: its only tests cannot fail or do not run, while your own probe shows the behaviour is right for the inputs you tried. Or a requirement row changed after adoption with no deviation entry, and the code still meets the adopted text | must-fix: the fix is a test or a log entry, not code |
| S3 Minor | A SHOULD is not met. A MUST is proven for one class of input only. The documentation and the behaviour differ where no claim depends on it | log-as-deviation is acceptable |
| S4 Note | Worth a sentence. At most five. Never style | none |

Calibration rules:

- A misleading test that hides a real fault is one finding, S1, naming both: the fault, and why the suite stayed green.
- A misleading test on a MUST is at least S2 even when the code is right. The repository's claim is proof, and the proof is missing.
- A reworded MUST whose adopted text the code fails is S1. Restoring the row or accepting the weaker one is the owner's decision: write `GATE:` in the suggested change.
- The same defect in several places is one finding with every location listed.
- No command, no must-fix. "Read, not run" findings are S3 at most until run.
- Do not report style, naming, formatting, structure you would have chosen differently, a SHOULD without a test (the spec allows it), or anything the spec's limits section already states.
- A review with no findings is allowed. Its "What was run" section then carries the weight, and it must name every MUST probed.
- The worked anchors are the eleven calibration cases in `calibration/_answers/EXPECTED.md`. Read them only after your calibration run.

## Finding format

```markdown
### F-03 · S2 Major · must-fix · M7
- Requirement: REQ-016 (MUST)
- Where: tests/test_terms.py::test_term_boundaries (line 41); src/inkproof/match.py:88
- Observed: the test checks only that a list is returned. With every comparison in `find_terms` inverted it still passes.
- Expected: the test fails when `ann` matches inside `annual`.
- Command: `uv run python $K/mutate_check.py src/inkproof/match.py:find_terms --req REQ-016`
- Output: `flip    SURVIVED  1 passed, 57 deselected`
- Suggested change: assert the exact match list for `annual` and for `ann`.
```

Every field is required. `Output` is one to three pasted lines, never a paraphrase. Number findings in order of severity.

## Review file

```markdown
# Review <session-id>

- Commit reviewed: <sha>
- Reviewer: <model> / <effort> (source: session record). Builder: <model> (source: BUILD-LOG)
- Calibration: <n> of 10 planted defects found, control clean: yes or no (first review only)
- Findings: <n> (S1 <n>, S2 <n>, S3 <n>, S4 <n>); must-fix <n>; log-as-deviation <n>

## What was run
One line per command: the command, the count it covered, the result line.

## Findings
(blocks in the format above)

## Not verified by this review
One list item per MUST not probed, per check not run, and why.
```

For each must-fix finding: write the finding block to a file, run the scrubber on it, then `gh issue create --title "Review <session-id> F-NN: <short title>" --body-file <file>`. Put the issue link in the finding.

## Other scopes

**TypeScript builds.** `spec_diff.py` and `tier_check.py` work unchanged. The other three read Python only, so do the same probes by hand: replace the function body with `throw new Error("mutation probe")`, run that test, see it fail, then `git checkout -- <file>` and confirm `git status --porcelain` is unchanged. Repeat with the body returning nothing, and with the comparisons inverted. For skips: `grep -rnE "\.(skip|todo|only|fixme|fails)\(|\bxit\(|\bxdescribe\(" src tests e2e`. A stray `.only` skips everything else in the file. The requirement tag convention comes from that build's spec.

**Evals and prompts.** The same classes apply to an eval harness. A judge that cannot fail (M5): run the two known-bad outputs through each judged check three times; all six runs must fail. A planted-error case with a loose expected output (M7): swap in the clean input; the case must flip. A baseline from one run (M6): the baseline file must hold three runs, the runner, the model ids and the date. An eval that never calls the model (M1): look for recorded responses and check the log shows real requests. These need the owner's key. Without it, list them under "Not verified by this review".

**Method repo.** Run every command the documents tell a reader to run. Every number has a script: run it. Every link resolves.

## Limits of the kit

The probes are coarse. `flip` changes everything at once and two changes can cancel. `req_run.py` counts asserts in test modules only, so a test that asserts through a helper can show `ZERO-ASSERT` wrongly: confirm with the probe. Mutation testing in the mutation session does the fine-grained work. A clean run of all five scripts is not a clean review. It means the tests can fail. Whether they test what the spec means is still yours to read.
