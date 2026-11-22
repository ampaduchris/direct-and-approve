# What stays private

`method/` is a published copy of part of a private control folder. This page lists what never leaves that folder, and why. [`scripts/boundary.py`](../scripts/boundary.py) fails CI if a path or pattern from the list is in this repository, and `scripts/extract.py` refuses to write `method/` if a replaced string survives.

| What | Why it stays private |
| --- | --- |
| The denylist (`private/denylist.txt`) | It holds the strings the scrubber blocks. Publishing it would publish exactly the values it exists to hide. `method/` carries only a synthetic example list. |
| Source material (`private/`) | It is the owner's raw inputs, not the method. |
| Notes and advisory files | They record opinions and advice that were never checked for publication. |
| Metrics | They count the owner's own sessions and time, and are not needed to follow the method. The numbers in this repository come from published build logs instead. |
| The real plan (`PLAN.md`) | It names unreleased projects and their order. `method/PLAN.md` holds a synthetic format example. |
| Every real build folder (`builds/*`) | Each holds a specification draft, a session list and run records for work that is not public. `method/builds/00-example/` is synthetic. |
| The upstream ledger and shortlist | They name other people's projects and problems that have not been filed. The owner writes and posts everything to another project. |
| Local settings (`.claude/settings.local.json`) | They hold machine paths and permission choices for one computer. |
| The hook scripts (`tools/hooks/`) | They enforce rules for one folder and one machine (limit LIM-8). A reader writes their own. |

## Values in `extract.toml` are public by design

The mapping `extract.toml` is a public file. Every replacement in it has a `from` string, and the `from` string is the text that was in the private source. Every replaced value in `extract.toml` is therefore public by design.

A value that must not be public is never written there. Put it in the private denylist, which the scrubber reads and which is never published. The scrubber and `boundary.py` would not notice a sensitive value written into the mapping, because to them it is only a replacement. Review 9.4 F-10 found this. The rule above is the review's cheaper remedy, applied in session 9.5; the owner has not chosen the alternative, which is a private file of replacements that `extract.py` would read when it is present.
