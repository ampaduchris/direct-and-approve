# Portfolio programme: how Claude works in this folder

This folder is the single project for <owner>'s public portfolio. It is a private git repo (`<account>/<control-repo>`). Public repos live in `repos/<name>/`. Forks of other people's projects live in `upstream/<project>/`. Both folders are ignored here; each entry is its own git repo.

Two goals, in priority order: merged contributions to other people's projects; then own repos and a site that show the method. Upstream work never waits for a build.

The owner types one of these words. Do exactly what the word says, nothing more.

| Owner types | Claude does |
| --- | --- |
| `setup` | One-time setup: follow `SETUP.md` section "What Claude does on setup". |
| `continue` | Run the next session of the current build (procedure below). |
| `upstream` | Run the next step of the upstream track: follow `UPSTREAM.md`. Allowed whatever build is CURRENT. |
| `maintain` | For each released repo: list open dependency pull requests, run the checks in `STANDARD.md` "Maintenance", post one pre-merge check comment on each, report which are ready for the owner to approve. Merge nothing. |
| `status` | Run `python3 tools/brief.py --status` and print its six lines: current build, last session and its PR state, next session with model and effort, open GATEs, upstream ledger counts (new, filed, accepted, merged), builds released. |
| `merged` | Re-check PR state. Mark each merged session `[x]`. Run the "After merge" block of each newly merged session. Then say what `continue` will run next. |
| `frontload` | Run the next unticked item in `FRONTLOAD.md` (needs Fable 5.2 / high; if on another model, apply the model check in step 4). Outputs go to this private folder only; commit and push; tick the item; report in 5 lines. |
| `proceed anyway` | Run the session you just declined to start because of a model mismatch, on the current model, and log that in the build log. |

## Identities
- In `repos/*` Claude commits, pushes and opens pull requests under the owner's identity. Every commit carries the `Co-Authored-By` line naming the model.
- The owner's account approves and merges. Claude never approves and never merges, in any repo, dependency pull requests included.
- Repository administration (creating a repo, its settings, its ruleset, adding it to the App's installation) uses the owner's `gh` login. Claude runs those commands only in a scaffold session, only from the definitions in `STANDARD.md`, and each one waits for the owner's approval at the prompt. Claude never changes or removes a ruleset afterwards.
- In this private folder and in `upstream/*` the identity is the owner's, and commits are signed. Claude posts nothing to another project. The owner writes and posts every issue, pull request description and reply there. (Enforced: guard G8.)

## The `continue` procedure
1. `git pull --rebase` here. The session start is the time the timer hook printed when the owner typed `continue` (if it printed nothing, record `date -u`). Run `python3 tools/brief.py`. It reads `PLAN.md` and the build's `SESSIONS.md` for you; do not read them again.
2. The next session is the one the brief names under NEXT: the first `[ ]` or `[~]` line of the CURRENT build. If the brief lists PLAN LINT problems for this build, fix the low-risk ones or ask before starting.
3. Merge gate: if the brief prints MERGE GATE with a state other than MERGED, stop and say: "Approve and merge <url> first, then type `merged`."
4. Model check: read the model and effort from the app's session record. If either differs from the session line, stop and give the owner three lines: switch to X at effort Y; why; the risk of staying. Then wait for `continue` after a switch, or `proceed anyway`. If the record cannot be read, write "effort: not machine-verified" in the build log row.
5. Read the files the brief lists under READ, in that order, and no others unless a step needs one. Frontloaded drafts (`SPEC-DRAFT.md`, `EVALS-DRAFT.md`, a `*-THESIS.md` the session names): adopt and reconcile them, do not redo them. The session that adopts a draft adds this as the draft's first line: `> Adopted into <repo>/<path> on <date> by session <id>. Do not read this draft; the adopted file is the authority.` The brief then drops it from every later read list. `DESIGN.md` and the mockups are the visual reference: read its section 0 (session read map) and only what it names for the session; build to them and make no design decision; if something is missing, stop and ask. For any long file, read only the part you need: `python3 tools/section.py <file> "<heading or number>"` or `<file> REQ-030..REQ-046`.
6. Write the confirmation gate in five lines before changing anything: objective, spec sections touched, exit test, what you will not do, first file you will change. Write it as the top of the state file the brief names (`builds/<b>/run/<session-id>.md`). After each step, append one line: step, result, evidence (command and its last line, or a link). If the state file already exists, read it first and resume from its last line. The tier table and the PR body are built from this file. Commit it with this folder at step 12.
7. Do the session's steps in `repos/<name>/` on a branch `s/<session-id>`. Where the session says TDD (test-driven development), commit and push the failing tests first so a red CI run exists, then implement.
8. Verify by running, not asserting: V1 to V6 from `STANDARD.md`; `python3 ../../tools/scrub.py .` must print `CLEAN`; the PR body file and the branch's commit messages must also pass the scrubber.
9. Push the branch. Open the PR as a draft from a body file (`gh pr create --draft --body-file`), title `<session-id>: <title>`. Body: confirmation gate, tier table with evidence, deviations, an "Owner checks" list of three to five things to look at before approving, any `GATE:` lines, provenance line.
10. Append one row to the repo's `docs/BUILD-LOG.md` with the real PR link: date, session id, model, effort and its source, minutes taken, tiers passed, NOT VERIFIED count, PR link. Push. Mark the PR ready for review.
11. Ledger: add one line to `UPSTREAM.md` "Ledger" for each problem met in a dependency or tool during the session. Do not act on it now.
12. Mark the session `[p]` with the PR link here. Commit and push this folder.
13. Report in at most five lines: PR link, tier summary, GATEs, next session id with its model and effort.

Session marks: `[ ]` not started; `[p]` PR open; `[x]` merged and after-merge block done; `[~]` checkpoint with a note.

Sessions that release have two parts. "Before merge" is everything in the PR. "After merge" runs under `merged`: tag the merge commit, create the release, publish, verify, tick the release checklist. Pushing a tag on a merged commit is allowed.

When the last session of a build is `[x]`: mark the build `RELEASED` with the date in `PLAN.md`, mark the next phase `CURRENT`, commit, push, and say so.

## Hard rules
- One build at a time. Never start a session from a build that is not `CURRENT`. Exceptions: `frontload`, `upstream` and `maintain`.
- Never merge or approve a PR. Never push to `main` of a public repo, except the very first commit of a new empty repo. (Enforced: `tools/hooks/guard.py` G1, G6.)
- Never commit anything that fails `tools/scrub.py`, and never put such text in a PR body or commit message. The scrubber skips this repo's own `private/` folder, which holds the denylist and the source material and never leaves this private repo; everything else here and everything in `repos/` and `upstream/` must print `CLEAN`. The plaintext list is `private/denylist.txt`. (Enforced on every commit, push and `gh` text: guard G7.)
- Nothing work-related, ever: no current or past employer work, colleagues, clients, interviewers, addresses, account numbers. Synthetic personas only.
- Honesty clause: NOT VERIFIED is always cheaper than a false PASS. Any check of model output runs 3 times; report all three.
- Dates are never set or changed: no `--date`, no `--reset-author` to re-date, no date environment variables, no amend or rebase to move work to another day. (Enforced: guard G2, G3. No amend at all: make a new commit.)
- One session, one PR, with as many commits as there are separate changes, usually one to three. Never split a change to raise a count. Never open an issue for a change that is already written. No filler changes.
- At most two build sessions a day.
- Stop at 45 minutes with no message from the owner (the timer hook counts from the owner's last message and reports from 40 minutes on; any message resets it) or after two failed attempts at the exit test: commit a checkpoint to the branch, leave the PR as a draft, mark the session `[~]` with a note, report.
- No subagents unless the session says so.
- Secrets live in the macOS Keychain only. Claude never reads, prints or asks for a secret value and never searches the disk for one. (Enforced for the Keychain: guard G5.)
- A hook block is final. Never work around one (another command, another route, a script); report it to the owner.

## Context and tool output
- One conversation per `continue`. Never run a second session in the same conversation.
- Tool output is read in short form. Tests: `-q --tb=line`, output to a file under `/tmp`, then `tail -30`. CI: `gh run view <id> --log-failed | tail -60`. Never `cat` a lockfile, a PDF, a generated fixture or a whole log. Read large files in slices.
- If the conversation was compacted, the state file is the record, not the summary (the session-start hook names it).

## Model advice
Default is Sonnet 5.5. Review sessions need Opus 5.5 so that the reviewer differs from the author of the thing reviewed. Each session line carries the reason and the risk of not switching. Never refuse to run on the owner's choice; record it.

## Public writing style
British English. Short declarative sentences. Specifics over adjectives. No em dashes. No "It is important to note". Every abbreviation written out at first use. Every build repo's README carries: "Built by directing Claude Code. No hand-written code. Every pull request was opened by the agent and approved and merged by me. Model and effort for every session are recorded in docs/BUILD-LOG.md."
