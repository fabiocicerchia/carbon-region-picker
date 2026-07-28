# carbon-region-picker

[![CI](https://github.com/fabiocicerchia/carbon-region-picker/actions/workflows/ci.yml/badge.svg)](https://github.com/fabiocicerchia/carbon-region-picker/actions/workflows/ci.yml)
[![Security](https://github.com/fabiocicerchia/carbon-region-picker/actions/workflows/security.yml/badge.svg)](https://github.com/fabiocicerchia/carbon-region-picker/actions/workflows/security.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/fabiocicerchia/carbon-region-picker/badge)](https://securityscorecards.dev/viewer/?uri=github.com/fabiocicerchia/carbon-region-picker)
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Ffabiocicerchia%2Fcarbon-region-picker.svg?type=shield)](https://app.fossa.com/projects/git%2Bgithub.com%2Ffabiocicerchia%2Fcarbon-region-picker?ref=badge_shield)
[![Release](https://img.shields.io/github/v/release/fabiocicerchia/carbon-region-picker)](https://github.com/fabiocicerchia/carbon-region-picker/releases)

Ranks cloud regions by **grid carbon intensity** under a **latency
constraint**. The two numbers you actually trade off when picking a region,
in one table.

```console
$ carbon-region-picker --near eu --max-latency-ms 60
| rank | region | gCO2e/kWh | latency |
|---|---|---|---|
| 1 | eu-north-1 🌱 | 25  | 35ms |
| 2 | eu-west-3 🌱  | 56  | 20ms |
| 3 | eu-west-1     | 290 | 25ms |
| 4 | eu-central-1  | 380 | 15ms |

Picking `eu-north-1` over `eu-central-1` cuts compute carbon ~15x.
```

## Data

- **Bundled** (default): yearly-average grid intensities per region zone —
  conservative, documented in the source, fine for placement decisions.
- **Live** (`--live --em-token …`): real-time intensity from the
  [Electricity Maps](https://www.electricitymaps.com) API, for
  carbon-aware scheduling of batch work.

## Install

```sh
pipx install git+https://github.com/fabiocicerchia/carbon-region-picker
```

Or with pip:

```sh
pip install git+https://github.com/fabiocicerchia/carbon-region-picker
```

Or the one-line installer:

```sh
curl -fsSL https://raw.githubusercontent.com/fabiocicerchia/carbon-region-picker/main/install.sh | bash
```

## Usage

```sh
pipx install .
carbon-region-picker --near eu --max-latency-ms 60
carbon-region-picker --live --em-token $EM_TOKEN --json   # feed schedulers
```

## Documentation

Full docs live in [`docs/`](docs/). Runnable examples live in [`examples/`](examples/).

## Development

`make setup` (once), then `make dev` and `make test` / `make lint`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). By participating you agree to the
[Code of Conduct](CODE_OF_CONDUCT.md).

## Security

Found a vulnerability? See [SECURITY.md](SECURITY.md) — please don't open a public issue.

## Support

Need help implementing this? [Get in touch](https://fabiocicerchia.it/contact).

## License

Apache 2.0 — see [LICENSE](LICENSE).
