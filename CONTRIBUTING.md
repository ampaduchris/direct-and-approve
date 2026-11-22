# Contributing

This repository is built by directing Claude Code against `docs/spec.md`. Issues describing a spec gap, a leak of private text through the extraction, or a document that says more than the evidence shows are welcome.

For a change: open an issue first. Pull requests need green CI and a test tagged with the requirement id it proves. Files under `method/` are generated; change `extract.toml` or the source instead.

Set up: `uv sync --locked`, then `uv run pytest -q --tb=line`.

By contributing you agree that your contribution is licensed under the MIT licence of this repository.
