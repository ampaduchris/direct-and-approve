# direct-and-approve

Directing a coding agent without reading its code needs a procedure, or approval turns into habit. This repository publishes the procedure one person uses, as `method/`, together with the scripts that check it and one real session traced from instruction to merge. Every file under `method/` is the output of `scripts/extract.py` from a private control folder at a stated date, and the checks below run on it.

```console
$ uv run --locked python method/calibration/_answers/prove.py | tail -n 4
ok   ex11 tier      exit 0 (expected 0)
ok   ex11 overlap   exit 0 (expected 0)
ok   ex11 fresh     prints '-3' (expected '-3')
ALL RUNS MATCH: 11 examples, 5 tools each, plus 5 fresh-input probes
```

The narrowest limit: nothing enforces that the owner looked at a change before merging it. See [Limits](#limits).

Claude Code wrote this code under my direction. I merged every pull request. One example: [pull request 3](https://github.com/ampaduchris/direct-and-approve/pull/3), where the failing tests were committed first. It carries no review comment from me.

## Demo

The demo is a document, not a recording: [the worked example](docs/worked-example.md) follows one session of another repository, [inkproof](https://github.com/ampaduchris/inkproof), from the session line to the merge. It is generated from a saved copy of the pull request, and a test compares every quotation and number in it with that copy. It includes what the session did not verify, and the fact that no owner comment exists on that pull request.

## Install

Clone the repository, then `uv sync --locked`. The scripts use the Python standard library only. CI (continuous integration) runs them on Python 3.11, 3.12 and 3.13 on Ubuntu. They are not tested on other systems. No script uses the network except `scripts/snapshot_pr.py`, which is run by hand and is never run in CI.

## Usage

- `python3 scripts/extract.py <control-folder> [--out method] [--check] [--date YYYY-MM-DD]` builds `method/` from a control folder. Exit codes: 0 done, 1 `--check` found a difference, 2 a private marker was found, 3 usage or input error. Without a control folder, `python3 scripts/extract.py --repo . --verify-manifest` compares `method/` with its manifest.
- `python3 scripts/check_sessions.py <control-folder>` checks the session format. Exit 0 if no problem, 1 if there is one.
- `python3 scripts/routing.py <BUILD-LOG.md> [--json]` counts sessions by model and effort, minutes and items not verified. Exit 1 on a malformed row.
- `python3 scripts/boundary.py` fails if a private path or pattern is in the tree.

To start your own: [`method/SETUP.md`](method/SETUP.md). The source date of `method/` is 2026-11-22, read from `method/MANIFEST.json`. The numbers in [`docs/model-routing.md`](docs/model-routing.md) come from 12 sessions of one repository.

## How the claim is proved

1. `scripts/extract.py` reads the mapping `extract.toml`. Each entry copies a file or folder of the control folder with literal replacements, or copies a file written for the public from `static/`. If any replaced string or forbidden pattern survives in the output, the run exits 2 and writes nothing.
2. `method/MANIFEST.json` holds the SHA-256 hash of every file and the source date. CI compares `method/` with it, so a hand edit to `method/` fails.
3. `scripts/boundary.py` fails if a private path or pattern is anywhere in the tree.
4. The calibration set in `method/calibration/` plants one defect in each of eleven small examples. `prove.py` runs the five kit scripts on them and fails unless every defect is exposed by its command and the control is clean.
5. A CI job copies `method/` to a folder outside the repository and runs the session checker, the scrubber self-test and the calibration proof there. That is the check that a reader who copies `method/` gets a control folder that passes its own checks.
6. A documents job runs every block marked `bash run` and checks relative links.

Each tool has one job. Python's standard library runs the scripts. pytest and Hypothesis run the tests. gitleaks scans for secrets. uv installs from the lockfile. Mutation testing with mutmut is planned for the release session.

Not proved by CI: that the owner ran the real scrubber and the real list before each push. Those run on the owner's machine. The result is a row in each pull request's tier table.

## Limits

What direct-and-approve does not do. The same table is in the specification.

| Limit | Meaning |
| --- | --- |
| LIM-1 Attention | The ruleset enforces a pull request and green checks. Nothing enforces that the owner looked. The method publishes the time from opening to merge and leaves the reader to judge. |
| LIM-2 One person, one tool | The procedure was used by one person with Claude Code. Nothing here was tried by a team or with another agent. |
| LIM-3 Small evidence | The numbers come from the sessions of the repos named in `docs/model-routing.md`. The count is printed beside every number. |
| LIM-4 No code reading by the owner | The owner does not read code. Review is by a second model and by checks that run. This is a stated design choice, not a guarantee of correctness. |
| LIM-5 Lag | `method/` is a copy. The private folder is the authority and can be ahead of it. The copy states its source date. |
| LIM-6 Public answers | The calibration answers are published. A model that can read them has not been calibrated by them. |
| LIM-7 Scrubber | The scrubber finds strings on a list. It does not know that a sentence describes a private fact in other words. |
| LIM-8 Hooks not included | The control folder enforces some rules with hook scripts (`tools/hooks/`). They stay private. `method/CLAUDE.md` cites them. A reader gets the rules as text and writes their own enforcement. |

## Verify it yourself

Run `uv sync --locked` once. Then three commands. CI runs the same three on every pull request.

```bash run
uv run --locked pytest -q --tb=line
```

Expected: the last line ends `passed` with no `failed`.

```bash run
uv run --locked python method/calibration/_answers/prove.py | tail -n 4
```

Expected: the last line is `ALL RUNS MATCH: 11 examples, 5 tools each, plus 5 fresh-input probes`.

```bash run
python3 scripts/routing.py docs/data/inkproof-BUILD-LOG.md
```

Expected:

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

## Status

Status: active.

## How this was built

Built by directing Claude Code. No hand-written code. Every pull request was opened by the agent and approved and merged by me. Model and effort for every session are recorded in docs/BUILD-LOG.md.

The record: [build log](docs/BUILD-LOG.md), [specification](docs/spec.md), [deviations from it](docs/DEVIATIONS.md). The independent review is session 9.4 and has not run.

The code here was generated by Claude Code under my direction. I wrote the requirements and approved each change. The law on copyright in machine-generated code is unsettled. I license whatever rights I hold under the licence in this repository.

## Licence

direct-and-approve is licensed under the MIT licence. The full text is in LICENSE.

## Security and contributing

See [SECURITY.md](SECURITY.md) and [CONTRIBUTING.md](CONTRIBUTING.md).
