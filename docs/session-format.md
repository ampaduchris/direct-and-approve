# Session format

A session line in a `SESSIONS.md` has this form:

`- [ ] **<id> <title>** · [switch to ]<model> / <effort>`

- The mark is the part in square brackets.
- The id and title follow in bold.
- The model and effort come after the dot. Effort is one of low, medium, high, xhigh or max.

A session also needs a bullet that begins "Exit test". `scripts/check_sessions.py` checks all of this.

| Mark | Meaning |
| --- | --- |
| `[ ]` | Not started. |
| `[p]` | A pull request is open. The line carries its link. |
| `[x]` | Merged, and the "After merge" block has run. |
| `[~]` | A checkpoint, with a note. The pull request stays a draft. |
