# Frontload track

Work that needs the strongest reasoning and does not depend on code existing. The owner types `frontload` in a session set to the strongest model; the agent runs the next unticked item below. Outputs are drafts in the private control folder. Nothing goes to a public repository. Later sessions pick the drafts up.

## Rules
- Order the items by value per token. Stop when the strongest model's allowance runs out. Every item stands on its own.
- Every draft starts with a status block: model, effort and date.
- The session that adopts a draft reconciles it with the repository and does not redo it. It adds one first line to the draft: `> Adopted into <repo>/<path> on <date> by session <id>. Do not read this draft; the adopted file is the authority.`
- The BUILD-LOG row of the adopting session records the adoption: the draft's model, effort and date.
- Each item ends with a "Done when" line that a command or a count can check.
- Kinds of work that suit the track: specifications, evaluation designs, essay theses, review kits and calibration sets.

## Item template
- [ ] **F<n> <title>** (`<path of the draft>`)
  - <What to read and what to write, in one or two lines.>
  - Done when: <a check the owner or a script can run>.

## How later sessions use these
| Draft | Consumed by | Effect |
| --- | --- | --- |
| SPEC-DRAFT.md | The spec session of a build | The session adopts the draft into `docs/spec.md` and reconciles it with the repository on the default model |
| EVALS-DRAFT.md | The evals sessions of a build | The first writes the spec from the draft; the second builds the cases |
| Essay thesis | The drafting session of an essay | The evidence table is filled from released work; the thesis is not re-derived |
| Review kit and calibration set | Every review session | The same checks every time, written once by the strongest model |
| README pattern | Every release session | Same section order, first screen and fixed sentences in every repository |
