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
```

`--json` emits machine-readable output for schedulers; omit it for the table.
