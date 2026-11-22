# Sessions: build 00 (a synthetic example)

Session line: `- [<mark>] **<id> <title>** · [switch to ]<model> / <effort>`. Marks: `[ ]` not started, `[p]` pull request open, `[x]` merged, `[~]` checkpoint with a note. Every session has a bullet that begins "Exit test".

- [x] **0.1 Scaffold and spec** · Sonnet 5.5 / high PR: https://github.com/example/wordcount-example/pull/1
  - Create the repository, the project files and CI. Write `docs/spec.md` with one requirement per scope bullet.
  - Exit test: CI is green and every scope bullet maps to a requirement.

- [ ] **0.2 Counting (TDD)** · Sonnet 5.5 / high
  - Failing tests first, pushed so that a red CI run exists. Then `wordcount.py`.
  - Exit test: the PR links the red run and the green run; the five counting cases and the missing-file case pass.
