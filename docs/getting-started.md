# Getting Started

## Prerequisites

- Python 3.10+
- (Optional) an [Electricity Maps](https://www.electricitymaps.com) API token
  for `--live` real-time data.

## Install

```sh
pipx install .        # or: pip install .
```

## Run

```sh
# Bundled yearly-average intensities (no network):
carbon-region-picker --near eu --max-latency-ms 60

# Real-time data from Electricity Maps:
export EM_TOKEN=...           # or pass --em-token
carbon-region-picker --live --json

# Real TCP latency instead of the bundled RTT estimate (aws/gcp only):
carbon-region-picker --measure

# Marginal intensity + the cleanest hour in the next 24h ("run tonight at 02:00"):
carbon-region-picker --live --marginal --forecast
```

`--json` emits machine-readable output for schedulers; omit it for the table.
