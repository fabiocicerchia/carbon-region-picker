# CLAUDE.md

Guidance for Claude Code (and other AI agents) working in this repo.

## Project

`carbon-region-picker` is a single-module Python CLI that ranks cloud regions
by grid carbon intensity under a latency constraint. Source lives in
`carbon_region_picker.py` (entry point: `main`), tests in
`tests/test_carbon_region_picker.py`. Bundled yearly-average intensities are
the default; `--live` queries the Electricity Maps API.

## Commands

```sh
make dev     # editable install with dev deps (pytest, ruff, build)
make test    # pytest -q
make lint    # ruff check .
make build   # python -m build
carbon-region-picker --near eu --max-latency-ms 60   # run
make help    # Show this help
make setup   # Install the pre-commit hook
make install # Install the package
```

## Tooling

- `make setup` installs the pre-commit hook, and that is the whole of it.
  Don't add a `.githooks/` directory: `core.hooksPath` replaces `.git/hooks/`
  wholesale, so setting it silently stops every pre-commit hook from running.
- Hooks are pinned by commit SHA with the tag in a trailing comment. A tag can
  be moved, a SHA cannot.
- CI runs this same `.pre-commit-config.yaml` through `pre-commit/action`, so
  what passes locally is what gates the pull request.

## Conventions

- Match existing style; don't reformat unrelated code.
- Conventional Commits for messages (see CONTRIBUTING.md).
- Keep it a single module with a stdlib-only footprint plus `requests`; don't
  add dependencies without a clear reason.
- Update docs/ and examples/ with behavior changes. Don't hand-edit
  CHANGELOG.md or the pyproject version — release-please generates both.
- Never commit secrets (EM_TOKEN). Keep `.env` out of git; CI runs gitleaks.

## Guardrails

- Don't touch generated files (`*.egg-info/`, `build/`) or caches by hand.
- Ask before large refactors or destructive operations.
