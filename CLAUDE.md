# direct-and-approve: rules for an agent in this repo

- `docs/spec.md` is the sole authority. Prompts never override it. If the spec and a request disagree, stop and say so.
- Tag every test with `@pytest.mark.req("REQ-###")`. `scripts/trace.py` fails CI on an untested MUST once the build is released.
- Nothing under `method/` is edited by hand. It is the output of `scripts/extract.py` from the control folder. Change the mapping (`extract.toml`) or the source, then extract again.
- Never put private material in this repository: no denylist, no real plan, no real build folder, no ledger, no local settings. `docs/what-stays-private.md` lists them.
- Scripts use the Python standard library only. No script calls a model or the network, except `scripts/snapshot_pr.py`, which is run by hand.
- Run tests from the lockfile: `uv sync --locked`, then `uv run pytest -q --tb=line`.
- One session, one pull request. Open it as a draft. Never merge or approve.
- Append one row to `docs/BUILD-LOG.md` per session. Log every departure from the spec in `docs/DEVIATIONS.md`.
- Do not write that one model is better than another, that the method prevents defects, or that the owner reviewed code.
- British English. Short declarative sentences. No em dashes.
