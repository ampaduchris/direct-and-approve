# The command words

The owner types one word. The agent does what the word says and nothing more. Each entry says what the word does and cites the line of [`method/CLAUDE.md`](../method/CLAUDE.md) that defines it. The definition is the authority; this page only explains it.

| Word | What it does | Defined at |
| --- | --- | --- |
| `setup` | Runs the one-time setup of a new control folder, once. | `method/CLAUDE.md` line 11 |
| `continue` | Runs the next session of the current build: read the brief, check the model, write a five-line gate, work on a branch, verify, open a draft pull request, log it. One conversation per `continue`. | `method/CLAUDE.md` line 12 |
| `upstream` | Runs the next step of the track that contributes to other people's projects. This copy does not publish that procedure (deviation DEV-004), so the word points at a file a reader does not have. | `method/CLAUDE.md` line 13 |
| `maintain` | Lists open dependency pull requests in released repositories, runs the standard's maintenance checks and posts one comment on each. It merges nothing. | `method/CLAUDE.md` line 14 |
| `status` | Prints six lines: current build, last session, next session with its model and effort, open decision points, ledger counts, builds released. | `method/CLAUDE.md` line 15 |
| `merged` | Re-checks pull request state after the owner has merged. It ticks each merged session and runs that session's "After merge" block. | `method/CLAUDE.md` line 16 |
| `frontload` | Runs the next item of the list of work to write ahead with the strongest model: specifications, evaluation designs, essay theses. Outputs stay private. | `method/CLAUDE.md` line 17 |
| `proceed anyway` | Runs a session that the agent declined to start because the model or effort did not match its session line, on the model in use, and records that in the build log. | `method/CLAUDE.md` line 18 |

The words are a closed set. An agent that is asked for something else should say that no word covers it.
