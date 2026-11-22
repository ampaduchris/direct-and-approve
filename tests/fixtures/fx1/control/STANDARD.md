# Build standard

Every public repo meets this at v1.0.

## Verification tiers (every session)
| Tier | Question |
| --- | --- |
| V1 | Does it exist and run at all |
| V2 | Does it do the thing |
| V3 | Does it fail correctly |
| V4 | Does it match the spec |
| V5 | Did it break what already worked |
| V6 | What did it not verify |

## Controls
| Id | Control | Mechanism | Gate |
| --- | --- | --- | --- |
| R1 | Requirement traceability | Tagged tests | CI |
| R2 | Mutation testing | mutmut | Release |
| R3 | Property-based tests | Hypothesis | CI |
| R4 | Eval harness | Inspect AI | Release |
| R5 | Privacy scrubber | scrub.py | Every PR |
| R6 | Model provenance | BUILD-LOG row | Every session |
| R7 | Independent review | One session | Once per build |
| R8 | Owner approval | A comment, then merge | Every PR |
