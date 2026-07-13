# Architecture

Single Python module (`carbon_region_picker.py`), no framework.

## Overview

Given a provider and a latency vantage point, the tool ranks that provider's
regions by grid carbon intensity (gCO2e/kWh), optionally filtering by a maximum
latency, and prints a table (or JSON).

## Components

- **Region data** (`REGIONS`) — per-provider region → grid zone mapping and
  bundled yearly-average intensities.
- **Vantage points** (`VANTAGE`) — approximate latency from a `--near` origin
  to each region.
- **Ranking** — sort by intensity, apply the `--max-latency-ms` constraint.
- **Live source** — with `--live`, intensities come from the Electricity Maps
  API instead of the bundled table.

## Data flow

`main()` parses args → selects provider/vantage → resolves intensities
(bundled or live) → filters by latency → sorts → renders table or JSON.

## Decisions

- Bundled data is conservative yearly averages: good enough for placement
  decisions without a network call or token.
- Live mode is opt-in to keep the default path offline and dependency-light.
