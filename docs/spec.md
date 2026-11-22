# direct-and-approve specification

Status: adopted in session 9.1 and reconciled with the control folder on 22 Nov 2026. Section 16.3 says what is settled and what is still open. Nothing in this document has been run except the repository checks of session 9.1 listed in the build log.

## 1. Purpose

direct-and-approve publishes the procedure by which one person directs a coding agent and approves every change, together with the scripts that check the procedure and one real session traced from instruction to merge.

This document is the sole authority for the repository's behaviour and contents. Prompts, README text and tests never override it.

### 1.1 The claim, exactly

Every file under `method/` is the output of `scripts/extract.py` from the owner's private control folder at a stated date. A reader who copies `method/` to an empty folder has a control folder that passes its own checks. Every number in the documents is printed by a script in the repository from data in the repository.

### 1.2 What is not claimed

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

The README repeats this table.

## 2. Conventions

- MUST, MUST NOT, SHOULD and MAY have their usual specification meaning. Every MUST and MUST NOT has at least one proof. A SHOULD without a proof is allowed.
- Requirement ids are `REQ-###`. Ids are never reused or renumbered. A removed requirement keeps its row with the text "withdrawn" and the reason.
- Tests are tagged `@pytest.mark.req("REQ-###")`. One test may carry several tags. `--strict-markers` is set.
- `scripts/trace.py` reads every table row in this file that begins `| REQ-`, reads the `@pytest.mark.req` tags in the test source, prints the matrix, and exits 1 if any MUST or MUST NOT has no tagged test, if a tag names an id that is not in this file, if an id appears twice, or if a scope row of section 16.1 names no MUST. It does not run tests. The workflow runs the tests first and fails if any test fails, so a tag counts only on a green run (DEV-003). While the build is CURRENT the workflow passes `--report-only` (DEV-001).
- Proof kinds: T, a pytest test; P, a Hypothesis property; CI, a named job or step; D, the document check of section 14.
- CI is continuous integration. PR is pull request.

## 3. Definitions

**Control folder.** A folder with `CLAUDE.md`, `STANDARD.md`, `PLAN.md`, a `builds/` folder, a `tools/` folder and a `private/` folder, as section 5 lays out.

**Mapping.** The file `extract.toml` at the repository root. It lists entries, replacements and forbidden patterns (section 7).

**Entry.** One line of the mapping that produces one file or one tree under `method/`. Kinds: `copy` (a file from the control folder, with replacements), `tree` (a folder from the control folder, with replacements and exclusions), `static` (a file from this repository's `static/` folder, written for the public and copied unchanged).

**Replacement.** A pair of literal strings, `from` and `to`. Applied to `copy` and `tree` entries, longest `from` first.

**Private marker.** Any `from` string of a replacement, or any match of a forbidden pattern, found in the output.

**Manifest.** `method/MANIFEST.json`: for each file under `method/`, its path, entry kind, SHA-256 and, once for the whole run, the source date.

**Session line.** A line in a `SESSIONS.md` that begins `- [` and holds a mark, an id, a title, a model and an effort (section 8).

**Fixture control folder.** A synthetic control folder under `tests/fixtures/`. It contains no text from the real one.

## 4. Repository

| Id | Level | Requirement | Proof |
| --- | --- | --- | --- |
| REQ-001 | MUST | The repository carries every file named in the standard's "Files every repo carries" that applies to a build with no factual content pipeline: `docs/spec.md`, `docs/BUILD-LOG.md`, `docs/DEVIATIONS.md`, `CLAUDE.md`, `README.md`, `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `LICENSE`, the PR template, `portfolio.yml`. | T: presence test |
| REQ-002 | MUST | The top level holds `method/`, `static/`, `scripts/`, `tests/`, `docs/` and `extract.toml`. No file under `method/` is edited by hand: every file's SHA-256 equals its manifest entry, and no file is missing from or extra to the manifest. | T: manifest test on the tree; T: planted hand edit fails |
| REQ-003 | MUST | Scripts use the Python standard library only and run on Python 3.11 and later. | CI: scripts job runs with no dependencies installed |
| REQ-004 | MUST NOT | No script calls a model or the network, except `scripts/snapshot_pr.py` (REQ-097), which is never run in CI. | T: import scan for network modules outside that file |

## 5. The procedure (S1)

| Id | Level | Requirement | Proof |
| --- | --- | --- | --- |
| REQ-010 | MUST | `method/CLAUDE.md` is a `copy` entry of the control folder's `CLAUDE.md`. | T: mapping test |
| REQ-011 | MUST | It contains the word table with every command word of the source, the numbered `continue` procedure, the "Hard rules" list, the "Context and tool output" section, the session marks and the "Model advice" section. A source heading missing from the output fails. | T: heading and table-row comparison on the fixture; CI: same check on `method/` against a recorded heading list |
| REQ-012 | MUST | Owner-specific values (the owner's name, account name, private repository name) appear only as the placeholders `<owner>`, `<account>`, `<control-repo>`. | T: fixture with all three planted |
| REQ-013 | MUST | `docs/procedure.md` explains each command word in at most three sentences and links to the line of `method/CLAUDE.md` that defines it. Every command word in the table has an entry. | D; T: word list comparison |
| REQ-014 | SHOULD | Withdrawn on 22 Nov 2026: the owner chose at the 9.1 GATE not to publish the upstream procedure (DEV-004). No upstream item has been filed by it yet. The row stays so that the id is not reused. | None |
| REQ-016 | MUST | `method/tools/brief.py` and `method/tools/section.py` are `copy` entries, published at the owner's choice of 22 Nov 2026 (DEV-005). The copy runs on `method/` as a control folder and names no real repository, build folder or account. If the private script cannot meet this through replacements alone, session 9.2 raises a GATE and does not edit `method/` by hand (N11). | T: `brief.py --no-gh` run on a copy of the fixture; forbidden-pattern and name scan of both files |

## 6. The standard (S2)

| Id | Level | Requirement | Proof |
| --- | --- | --- | --- |
| REQ-020 | MUST | `method/STANDARD.md` is a `copy` entry of the control folder's `STANDARD.md`. | T: mapping test |
| REQ-021 | MUST | Its first line after the title states: "Copied from the private authority on <date>." with the source date of the manifest. | T |
| REQ-022 | MUST | The tier table V1 to V6 and the controls table R1 to R8 are present with the same row ids as the source. | T on the fixture; CI: row ids on `method/` |
| REQ-023 | MUST | This repository meets the standard it publishes. Where it does not, the departure is a numbered entry in `docs/DEVIATIONS.md`. Known at draft time: R4 does not apply (no model is called); there is no 60-second recording, the worked example is the demo. | T: each known departure has an entry |

## 7. Extraction (S3)

`python3 scripts/extract.py <control-folder> [--out method] [--check] [--date YYYY-MM-DD]`

| Id | Level | Requirement | Proof |
| --- | --- | --- | --- |
| REQ-030 | MUST | Every file under `method/` is produced by exactly one entry of the mapping. Two entries with the same target are a configuration error. | T |
| REQ-031 | MUST | The same control folder, mapping, `static/` folder and source date give byte-identical output, manifest included, on two runs. Output does not depend on file system order, locale or the clock. | T: two runs compared; P: order of entries shuffled |
| REQ-032 | MUST | Replacements are literal and case-sensitive. They are applied longest `from` first. | T |
| REQ-033 | MUST | After replacement, if any output contains a private marker, the run exits 2, names the entry and the line number, and does not print the matched text. | T: planted marker in a `copy`, in a `tree` file and in a file name |
| REQ-034 | MUST | A refused run leaves the output folder exactly as it was. Output is built in a temporary folder and moved into place only on success. | T: hash of the output folder before and after a refusal |
| REQ-035 | MUST | Forbidden patterns in the shipped mapping include at least: a home directory path (`/Users/`, `/home/`, `C:\Users\`), an email address, and a link to a private artifact or session. | T: one planted case each |
| REQ-036 | MUST | A `tree` entry copies only files matched by its `include` globs and none matched by its `exclude` globs. A symbolic link is never followed and never copied. | T |
| REQ-037 | MUST | A source file that is missing, unreadable or not valid UTF-8 text in a `copy` entry exits 3 and names the entry. | T: three cases |
| REQ-038 | MUST | `--check` writes nothing. It exits 0 if a fresh extraction equals the existing output and 1 otherwise, listing the paths that differ. | T: clean and drifted fixtures |
| REQ-039 | MUST | Extracting the output of an extraction with the same mapping changes nothing: no replacement `to` string is itself a `from` string or contains one. The mapping is rejected at load, exit 3, if this does not hold. | P; T: rejected mapping |
| REQ-040 | MUST | The source date is the `--date` value, or else the date of the control folder's newest commit read from `git log`. It is never the current time. | T |
| REQ-041 | MUST | Exit codes: 0 success; 1 `--check` found a difference; 2 private marker; 3 usage, configuration or input error. | T: one test per code |
| REQ-042 | SHOULD | The run prints one line per entry: kind, target, bytes, replacements made. | None |

## 8. Session format (S4)

A session line has this form, where the mark is a space, `p`, `x` or `~`:

`- [ ] **<id> <title>** · [switch to ]<model> / <effort>`

`python3 scripts/check_sessions.py <control-folder>`

| Id | Level | Requirement | Proof |
| --- | --- | --- | --- |
| REQ-050 | MUST | `method/PLAN.md`, `method/builds/00-example/BUILD.md` and `method/builds/00-example/SESSIONS.md` are `static` entries. The example build is synthetic, has two sessions and is named so that nobody takes it for a real project. | T: mapping test; T: no name of a real repo in the three files |
| REQ-051 | MUST | The checker fails, exit 1, naming file and line, on a session line with no model, no effort, an effort outside low, medium, high, xhigh and max, or more than one model. | T: four cases |
| REQ-052 | MUST | It fails on a session with no bullet that begins "Exit test". | T |
| REQ-053 | MUST | It fails on a mark outside the four, on a `[p]` session with no pull request link, and on a `[~]` session with no note. | T: three cases |
| REQ-054 | MUST | It fails on a duplicate session id in one file. | T |
| REQ-055 | MUST | In `PLAN.md` it requires a phases table with a "Status" and a "Folder" column, at most one row marked `CURRENT`, and for every row a folder under `builds/` that holds a `SESSIONS.md`. | T: two CURRENT rows; missing folder; missing column |
| REQ-056 | MUST | It fails if a session is `[x]` or `[p]` while an earlier session in the same file is `[ ]`. | T |
| REQ-057 | MUST | It passes on `method/` and exits 0 with one summary line: files read, sessions read. | CI: start-your-own job |
| REQ-058 | SHOULD | `docs/session-format.md` shows one session line with each part named, and the four marks with their meanings. | None |

## 9. Frontload pattern (S5)

| Id | Level | Requirement | Proof |
| --- | --- | --- | --- |
| REQ-065 | MUST | `docs/frontload.md` states: what kind of work is written ahead (specifications, evaluation designs, essay theses, review kits), on which model and why; that a draft carries a status block with model, effort and date; that the adopting session reconciles and does not redo; that the BUILD-LOG row records the adoption. | D: required headings present |
| REQ-066 | MUST | `method/FRONTLOAD.md` is a `static` entry: the track's rules, one empty item template with "Done when", and the "How later sessions use these" table with example rows. It contains none of the owner's items. | T: no item id of the form F followed by digits other than in the template |
| REQ-067 | MUST | Every draft-to-session pair named in `docs/frontload.md` as an example links to a real adopted specification and its BUILD-LOG row in a released repo. | D: links resolve |

## 10. Review and verification kit (S6)

| Id | Level | Requirement | Proof |
| --- | --- | --- | --- |
| REQ-070 | MUST | `method/.claude/skills/independent-review/` and `method/.claude/skills/pre-pr-check/` are `tree` entries. Each `SKILL.md` keeps its front matter with `name` and `description`. | T: front matter parse |
| REQ-071 | MUST | The six script files of the kit are present and byte-identical to the control folder's. | T on the fixture: no replacement touches a `.py` file under the skills tree; a replacement that would is a configuration error |
| REQ-072 | MUST | Every path that a `SKILL.md` names resolves inside `method/` when `method/` is taken as the control folder root. A path written `../../tools/...` is read from `repos/<name>/` of that root, as the skills use it. | T: path scan of both skill files |
| REQ-073 | MUST | `method/calibration/` holds every example and the answers folder. The calibration README and the answers folder README each state, in the first paragraph, that the answers are public and the set is for demonstration only (LIM-6). | T |
| REQ-074 | MUST | A CI job runs the calibration proof. Every planted defect is exposed by its command, the control example is clean, and no example file is changed by the run. | CI: kit job; the job fails if `git status --porcelain` is not empty afterwards |
| REQ-075 | MUST | `docs/review-kit.md` lists every taxonomy entry with its exposing command and the example that plants it. An entry in the skill with no row in the document fails. | T: id comparison |

## 11. Scrubber (S7)

| Id | Level | Requirement | Proof |
| --- | --- | --- | --- |
| REQ-080 | MUST | `method/tools/scrub.py` is a `copy` entry. `method/` holds no denylist. It holds `method/private/denylist.example.txt`, a `static` entry with synthetic entries only. | T: no file named `denylist.txt` in the tree; T: every example entry matches a list of invented names kept in the test |
| REQ-081 | MUST | `python3 method/tools/scrub.py --self-test` passes in CI. | CI |
| REQ-082 | MUST | The scrubber, run with the example list on the repository tree, prints `CLEAN`. | CI |
| REQ-083 | MUST | Before every push in a build session, the owner's real scrubber and list are run on the tree, the PR body and the commit messages, and at release on the full history. This runs locally and its result is a row in the PR's tier table. | D: release checklist row; not provable in CI, stated as such in the README |

## 12. Model routing (S8)

`python3 scripts/routing.py <BUILD-LOG.md> [--json]`

| Id | Level | Requirement | Proof |
| --- | --- | --- | --- |
| REQ-085 | MUST | `docs/model-routing.md` states the rule: a default model; a review runs on a model that differs from the author of the thing reviewed; each session line names its model and effort; a line that asks for a switch carries the reason and the risk of not switching; the owner's choice is never refused, it is recorded. | D: required headings |
| REQ-086 | MUST | `routing.py` reads the BUILD-LOG table of the standard (date, session id, model, effort and its source, minutes, tiers passed, NOT VERIFIED count, PR link) and prints: sessions by model and effort, total minutes, total NOT VERIFIED, and the number of rows whose effort was not machine-verified. | T: fixture log with known counts |
| REQ-087 | MUST | A row with a missing column, a non-numeric minutes or count cell, or a duplicate session id exits 1 naming the line. No partial total is printed. | T: three cases |
| REQ-088 | MUST | Every table printed carries the number of sessions it was computed from. | T |
| REQ-089 | MUST | The numbers in `docs/model-routing.md` equal the output of `routing.py` on the BUILD-LOG copies under `docs/data/`, each of which names its repository and commit hash in its first line. | T: document compared with script output |
| REQ-090 | MUST NOT | The document makes no claim that one model is better than another. It reports what was used and what was not verified. | D: reviewed in session 9.4; listed in the review scope |

## 13. Worked example (S9)

| Id | Level | Requirement | Proof |
| --- | --- | --- | --- |
| REQ-095 | MUST | `docs/worked-example.md` follows one real session of a released repo that used test-driven development. In order: the session line as written, the confirmation gate, the failing run, the passing run, the tier table, the "Not verified" list, the BUILD-LOG row, the owner's merge comment, the time from opening to merge. | D: nine headings in order |
| REQ-096 | MUST | Each of the nine parts carries a link to its source: a file at a commit hash, a CI run or a pull request comment. No link points at a branch name. | T: link pattern check |
| REQ-097 | MUST | `scripts/snapshot_pr.py` saves the pull request's record (title, body, opened and merged times, the merge comment, run links) to `docs/data/worked-example.json` with the fetch date. It is run by hand in session 9.3. Every quotation and number in the document equals a value in that file. | T: document compared with the snapshot, offline |
| REQ-098 | MUST | The example shows at least one thing that went wrong or was not verified in that session, in the session's own words. An example with an empty "Not verified" list is not accepted; choose another session. | T: list length in the snapshot is at least 1 |
| REQ-099 | MUST | All links in the documents resolve. PR CI checks relative links and anchors offline. External links are checked once in session 9.3 and again at release, and the output is pasted into the PR body. | CI: offline link check; D: release checklist row |

## 14. Start your own (S10) and documents

| Id | Level | Requirement | Proof |
| --- | --- | --- | --- |
| REQ-105 | MUST | `method/SETUP.md` is a `static` entry. It takes a reader from an empty folder to a first `continue` in numbered steps, names every tool needed with its check command, and contains no machine path and no account name. | T: forbidden pattern scan; D |
| REQ-106 | MUST | A CI job copies `method/` to a temporary folder outside the repository and there runs `check_sessions.py`, the scrubber self-test and the calibration proof. All three exit 0. | CI: start-your-own job |
| REQ-107 | MUST | In every document, a fenced block whose info string is `bash run` is executed by `scripts/run_blocks.py` in CI from the repository root and must exit 0. A block that needs the network or the owner's login is tagged `bash` only. | CI: documents job; T: a failing block fails the script |
| REQ-108 | MUST | The README's "Verify it yourself" section holds exactly three `bash run` blocks: the test suite, the calibration proof, `routing.py` on a file under `docs/data/`. | T: block count; CI by REQ-107 |

## 15. Privacy boundary (S11), limits (S12) and CI

| Id | Level | Requirement | Proof |
| --- | --- | --- | --- |
| REQ-110 | MUST | `docs/what-stays-private.md` lists what never leaves the control folder: the denylist, source material, notes, advisory files, metrics, the real plan and build folders, the upstream ledger and shortlist, local settings. For each: one sentence on why. | D: every row of the BUILD.md "never public" list has an entry |
| REQ-111 | MUST | `scripts/boundary.py` fails, exit 1, if the tree holds any path matching the forbidden path list in `extract.toml` (at least `denylist.txt`, `settings.local.json`, any `private/` folder other than `method/private/` with the example list, any folder under `method/builds/` other than `00-example`). | T: planted path fails; CI on the tree |
| REQ-112 | MUST | `boundary.py` also runs the forbidden patterns of REQ-035 over every text file in the repository, not only `method/`, with a declared allowlist for the test fixtures that plant them. | T: planted marker in `docs/` fails; fixture allowlist honoured |
| REQ-115 | MUST | The README carries, word for word: the limits table of section 1.2; the disclosure line "Built by directing Claude Code. No hand-written code. Every pull request was opened by the agent and approved and merged by me. Model and effort for every session are recorded in docs/BUILD-LOG.md."; the authorship note of the standard; one status line of the standard. | T: four substring checks |
| REQ-116 | MUST | The README states the source date of `method/` and the number of sessions behind the numbers, both read from files by a test, not typed. | T: README values compared with the manifest and the `routing.py` output |
| REQ-117 | MUST NOT | No document says or implies that the method prevents defects, that the owner reviewed code, or that approval was enforced. | D: reviewed in session 9.4; phrases "guarantees", "ensures correctness", "human-reviewed code" absent, by T |
| REQ-120 | MUST | The PR workflow runs, in order: tests from the lockfile; `trace.py`; manifest check (REQ-002); `boundary.py`; scrubber self-test and example-list scan; kit job; start-your-own job; documents job; offline link check; gitleaks. Any failure fails the workflow. | CI: workflow file read by a test that asserts the step names in order |
| REQ-121 | MUST | The workflow meets the CI section of the standard: actions pinned to full hashes, runner image pinned, read-only permissions, 10-minute timeout on the test job, concurrency group, no secrets in the test job. | T: workflow file scan |
| REQ-122 | SHOULD | Hypothesis runs with a fixed derandomised profile in CI so a red run can be reproduced from its link. | None |

## 16. Traceability, evidence and open points

### 16.1 Scope to requirements

| BUILD.md scope bullet | MUSTs |
| --- | --- |
| S1 Procedure | REQ-010, 011, 012, 013, 016 |
| S2 Standard | REQ-020, 021, 022, 023 |
| S3 Extraction | REQ-030 to 041, REQ-002 |
| S4 Session format | REQ-050 to 057 |
| S5 Frontload pattern | REQ-065, 066, 067 |
| S6 Review and verification kit | REQ-070 to 075 |
| S7 Scrubber | REQ-080, 081, 082, 083 |
| S8 Model routing | REQ-085 to 090 |
| S9 Worked example | REQ-095 to 099 |
| S10 Start your own | REQ-105, 106, 107, 108 |
| S11 Privacy boundary | REQ-110, 111, 112, REQ-033, 035 |
| S12 Limits | REQ-115, 116, 117 |

Counts, as `trace.py` reads them on 22 Nov 2026: 72 live requirements, of which 69 are MUST or MUST NOT and 3 are SHOULD (REQ-042, 058, 122). REQ-014 is withdrawn and not counted. REQ-016 is new. The draft counted 72 including REQ-014, 68 MUST and 4 SHOULD.

### 16.2 Fixtures

| Id | What | Used by |
| --- | --- | --- |
| FX-1 | Clean fixture control folder: all source files, three planted owner values | REQ-010 to 041 |
| FX-2 | FX-1 with a private marker in a copied file, in a tree file and in a file name | REQ-033, 034 |
| FX-3 | FX-1 with a missing source, an unreadable source and a binary file where text is expected | REQ-037 |
| FX-4 | Seven `SESSIONS.md` files and three `PLAN.md` files, each with one defect, and one clean pair | REQ-051 to 056 |
| FX-5 | Four BUILD-LOG files: clean with known counts, missing column, non-numeric cell, duplicate id | REQ-086, 087 |
| FX-6 | A tree with a planted forbidden path and a planted pattern in `docs/` | REQ-111, 112 |

### 16.3 Open points

Status as of session 9.1, 22 Nov 2026. SETTLED means a check was read or run in 9.1 and the result is stated. OPEN means a later session settles it. Nothing is marked settled that was only read.

| # | Point | Status | Who settles it |
| --- | --- | --- | --- |
| N1 | `direct-and-approve` is free on GitHub | SETTLED 22 Nov: `gh repo view` found no repository of that name under the owner's account, and a name search of GitHub returned no repository of that name anywhere. Created. Trade mark use was not checked and cannot be checked by this repository's tools. NOT VERIFIED | none |
| N2 | The calibration proof after the move to `method/calibration/` | OPEN. `_answers/prove.py` finds the kit with `HERE.parents[3]`, which is right for the private path and wrong under `method/`. The mapping carries a literal replacement to `HERE.parents[1]` (a `.py` outside the skills tree, so REQ-071 is not touched). Not run yet | 9.2 writes the test; 9.3 runs the kit job |
| N3 | The skills load with the Skill tool from a copied `method/.claude/skills/` | OPEN | 9.4, in the stranger's walk-through |
| N4 | REQ-071 (kit scripts byte-identical) against REQ-072 (paths resolve) | SETTLED in design: the six kit scripts hold no control-folder path (`grep` for `private/`, `/Users`, `F12` found none), so both hold. The only path in the kit is in `SKILL.md` text and in `prove.py` (N2). Not proven by a test yet | 9.2 |
| N5 | `scrub.py --history` and `--text-file` exist | SETTLED 22 Nov: both are in the control folder's `tools/scrub.py` (session 0.1, 16 Nov) and `--help` lists them | none |
| N6 | `CLAUDE.md` holds private text beyond the three owner values | PARTLY SETTLED. A grep for home paths, email addresses and private links found none in `CLAUDE.md`, `STANDARD.md`, the skills, `tools/brief.py`, `tools/section.py` or `tools/scrub.py`; the owner's scrubber printed CLEAN on each. The owner values in `CLAUDE.md` are the owner's name and the control repository name. The scrubber does not read for private facts in other words (LIM-7). The mapping check in 9.2 runs the forbidden patterns on the real output | 9.2 |
| N7 | An inkproof session with TDD and a non-empty "Not verified" list exists | OPEN. inkproof is released (v1.0.0, 21 Nov 2026). Sessions 1.4 and 1.5 are the candidates named in the session line; not read in 9.1 | 9.3 |
| N8 | Step numbers that the skills cite in the `continue` procedure | SETTLED 22 Nov by reading: `pre-pr-check` cites steps 8, 9 and 10, and `CLAUDE.md` step 8 is verification, step 9 the pull request body, step 10 the BUILD-LOG row and ready for review. They match today. A later change to the numbering would break the citation silently | 9.2 adds a check if cheap |
| N9 | Session sizes | OPEN. 9.1 is the first row of timing | BUILD-LOG minutes |
| N10 | Nothing in the draft was run | PARTLY SETTLED. In 9.1 only: `trace.py` runs on this file and the scaffold's tests run in CI. Every other requirement is unrun | all sessions |
| N11 | `tools/brief.py` is not publishable as it stands | OPEN. It names real build folders that are not public (in the read-list code), special-cases real repository names, and reads `UPSTREAM.md`, which is not published. The owner chose to publish it (DEV-005). Replacements cannot remove these without changing what the script does. Options for 9.2: change the private script so a generic version exists, publish a static rewrite, or the owner withdraws REQ-016. This is a GATE for 9.2, raised in the 9.1 pull request | owner, then 9.2 |
| N12 | The `description` of `independent-review/SKILL.md` and its text name real session ids (1.7, 2.9, 3.9, 7.4, 9.4) and real project steps | OPEN. A literal replacement can generalise them (SKILL.md is not a script). Its text also cites "upstream step 8" and Gate C of the upstream procedure, which is not published (REQ-014 withdrawn), so those lines point at nothing for a reader. Not designed here beyond `extract.toml` | 9.2 |

### 16.4 Reconcile record (session 9.1)

What changed in the control folder between the draft (15 Nov 2026) and adoption (22 Nov 2026), read from `git log` of the control folder: `CLAUDE.md` changed once, on 16 Nov, when signing and the timer wording were added. `tools/scrub.py` gained `--history` and `--text-file` on 16 Nov. `STANDARD.md`, `SETUP.md`, `FRONTLOAD.md` and the skills did not change in that period. `UPSTREAM.md` changed often; it is not published (REQ-014). Added to this document as a result: LIM-8, REQ-016, N11, N12 and the "Context and tool output" heading in REQ-011. Whether a section was added to `SETUP.md` or `FRONTLOAD.md` is not a concern here because both are `static` entries written for the public in 9.3.
