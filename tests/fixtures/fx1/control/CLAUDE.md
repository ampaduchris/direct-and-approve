# Fixture programme: how Claude works in this folder

This folder is the single project for Ada Fixture's public portfolio. It is a private git repo (`adafixture/control`). The account is `adafixture`.

| Owner types | Claude does |
| --- | --- |
| `setup` | One-time setup. |
| `continue` | Run the next session. |
| `status` | Print the status. |

## The `continue` procedure
1. Pull and run the brief.
2. Do the session.

## Hard rules
- Never merge or approve a pull request.

## Context and tool output
- Read tool output in short form.

## Model advice
Default is Sonnet 5.5. Review sessions need Opus 5.5.

Session marks: `[ ]` not started; `[p]` PR open; `[x]` merged; `[~]` checkpoint.
