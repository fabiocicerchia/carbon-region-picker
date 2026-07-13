# Contributing

Thanks for taking the time to contribute to carbon-region-picker! By
participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).

## Development setup

You need Python 3.10+ and `make`.

```sh
make setup   # install git hooks + pre-commit (run once)
make dev     # editable install with dev dependencies (pytest, ruff, build)
make lint    # ruff check .
make test    # pytest
```

## Making changes

- Keep changes focused; one logical change per PR, keeping the existing style.
- Add or update tests.
- Update `docs/` and `examples/` when behavior changes.
- Make sure `make lint` and `make test` pass locally.

Don't edit `CHANGELOG.md` or the version in `pyproject.toml` by hand — both are
generated from commit messages by release-please (see [Releases](#releases)).

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/): `feat:`,
`fix:`, `docs:`, `chore:`, etc. This drives the version bump: `fix:` → patch,
`feat:` → minor, `feat!:` or a `BREAKING CHANGE:` footer → major.

## Releases

Releases are automated by [release-please](.github/workflows/release.yml); you
don't tag or edit the changelog manually.

1. Merge `feat:`/`fix:` PRs into `main` as normal — **no tag is created**.
2. release-please keeps an open **release PR** ("chore: release X.Y.Z"),
   recalculating the next version and changelog on every merge.
3. When you're ready to ship, **merge the release PR** — that (and only that)
   bumps `pyproject.toml`, tags `vX.Y.Z`, creates the GitHub Release with build
   artifacts attached, and (if enabled) publishes to PyPI.

## License

By contributing you agree that your contributions are licensed under the
Apache License 2.0 (see `LICENSE`).
