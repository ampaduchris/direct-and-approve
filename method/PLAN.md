# Plan

The phases of the programme, one row each. `scripts/check_sessions.py` reads this table: it needs the columns `Status` and `Folder`, at most one row marked `CURRENT`, and a `SESSIONS.md` in `builds/<Folder>/` for every row.

Status is `planned`, `CURRENT`, or `RELEASED <date>`. One build is `CURRENT` at a time. Claude starts a session only from the `CURRENT` build.

## Phases

| Id | Name | Status | Folder |
| --- | --- | --- | --- |
| 00 | Example build (synthetic) | CURRENT | 00-example |
