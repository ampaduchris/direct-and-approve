# Setup: from an empty folder to a first `continue`

About ten minutes. You need a computer with a shell, an account on GitHub, and Claude Code. This file is written for a reader who has none of the author's files. Everything the author's own folder holds beyond the contents of `method/` stays private (see `docs/what-stays-private.md` in the repository this folder came from).

## What you do
1. Check the tools. Each line should print a version.
   - `git --version`
   - `gh auth status` (the GitHub command line, signed in to your account)
   - `python3 --version` (3.11 or later)
   - `uv --version`
   - `claude --version`
2. Make an empty folder for your control repository and copy the contents of `method/` into it. The folder then holds `CLAUDE.md`, `STANDARD.md`, `PLAN.md`, `builds/`, `tools/`, `private/`, `calibration/` and `.claude/skills/`.
3. Create your private list: copy `private/denylist.example.txt` to `private/denylist.txt`, then replace the invented entries with your own: names of employers, colleagues and clients that must never appear in a public repository. The list never leaves this folder.
4. Run `python3 tools/scrub.py --self-test`. It must print `SELF-TEST PASS`.
5. Run `python3 <path-to-scripts>/check_sessions.py .` from a clone of direct-and-approve, or read `builds/00-example/SESSIONS.md` by hand. It must report no problems.
6. Replace the example build. Copy `builds/00-example/` to `builds/01-<name>/`, write your `BUILD.md` and `SESSIONS.md` in the same format, add one row to the phases table in `PLAN.md` with the status `CURRENT`, and change the status of the example row (`00-example`) to `planned` or delete the row. Only one phase may be `CURRENT`, and step 5's check fails if two are.
7. Replace the placeholders in `CLAUDE.md`: `<owner>`, `<account>` and `<control-repo>`.
8. Make it a private repository: `git init -b main`, commit, then `gh repo create <account>/<control-repo> --private --source . --push`. Confirm that `gh repo view <account>/<control-repo> --json visibility` says `PRIVATE`.
9. Start Claude Code in the folder and type `continue`.

## What Claude does on setup
When the owner types `setup`, in an empty control folder:
1. Preflight, reporting each result: the tool checks of step 1 above, and `git config user.email` is a verified address on the GitHub account, so that commits count on the contribution graph.
2. Private list: if `private/denylist.txt` does not exist, copy `private/denylist.example.txt` to it and ask the owner to replace the invented entries.
3. Run `python3 tools/scrub.py --self-test`. It must print `SELF-TEST PASS`.
4. Make the folder a private repository as in step 8 above. Stop if the repository is not private.
5. Report in at most eight lines, ending with: "Type `continue` to start the first build."

## Three things this copy does not give you
- `tools/hooks/` is not published (limit LIM-8). `CLAUDE.md` cites the hook rules as text. Write your own enforcement, or follow the rules by hand.
- `tools/brief.py` is not published (DEV-008 in the repository's `docs/DEVIATIONS.md`). Step 1 of the `continue` procedure runs it. Without it, read the first session line marked `[ ]` or `[~]` of the `CURRENT` build yourself.
- `UPSTREAM.md` is not published (DEV-004 in the repository's `docs/DEVIATIONS.md`). The `upstream` word and step 11 of the `continue` procedure point at it. Ignore both, or write your own track for contributing to other people's projects.
