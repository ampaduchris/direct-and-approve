# Frontload: writing ahead

Some work needs careful reasoning and does not need code to exist. The method calls it frontload and runs it ahead of the builds that use it. The rules are in [`method/FRONTLOAD.md`](../method/FRONTLOAD.md).

## What is written ahead

- Specifications: the requirement table of a build, each requirement marked MUST or SHOULD with the test that will prove it.
- Evaluation designs: the cases, including planted errors, with the expected result and the reason.
- Essay theses: the claim, the strongest objection and the evidence each point needs.
- Review kits and calibration sets: the checks and the examples that prove each check can fail.

## Which model, and why

The owner runs this work on the strongest model available, set to high effort. The reason is cost shape, not a measured result: a mistake in a draft is copied into every later session that reads it, and the draft is written once. This repository does not measure whether a draft written this way is better than one written on the default model. The BUILD-LOG records which model wrote which draft.

## The status block

Every draft starts with a status block: model, effort and date. A reader, and the adopting session, can then see what wrote it and how old it is.

## How a session adopts a draft

The adopting session reconciles the draft with the repository as it now stands and does not redo the work. It reads what changed in the control folder since the draft's date, records each change it makes to the draft as a numbered open point or deviation, and puts the adopted file in the repository. It then adds one first line to the draft: `> Adopted into <repo>/<path> on <date> by session <id>. Do not read this draft; the adopted file is the authority.` Later sessions read the adopted file and skip the draft.

## The BUILD-LOG row records the adoption

The row of the adopting session names the draft's model, effort and date in its model cell, in addition to the model that ran the session.

## One example

| Draft | Adopted by | Adopted file | BUILD-LOG row |
| --- | --- | --- | --- |
| Specification draft of inkproof, written on 14 Nov 2026 by Fable 5.2 at high effort | Session 1.2, run on Sonnet 5.5 at high effort | [`docs/spec.md` at the release commit](https://github.com/ampaduchris/inkproof/blob/1cef639809c2779c19e4783eaa0c53ba471ad290/docs/spec.md) | [Row 1.2 of `docs/BUILD-LOG.md`](https://github.com/ampaduchris/inkproof/blob/1cef639809c2779c19e4783eaa0c53ba471ad290/docs/BUILD-LOG.md), which says "adopted draft: Fable 5.2 / high, 14 Nov 2026" |

The draft itself is private. This repository's own specification was adopted the same way in session 9.1; its row is in [`docs/BUILD-LOG.md`](BUILD-LOG.md).
