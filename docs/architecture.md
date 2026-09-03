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
  `rank()` returns `RankedRegion` records (region, zone, gco2_kwh,
  latency_ms); the field order is the `--json` key order.
- **Live source** — with `--live`, intensities come from the Electricity Maps
  API instead of the bundled table.

## Data flow

`build_parser()` declares the CLI → `main()` validates the flag combination →
resolves intensities (bundled, or live via `fetch_live`) → `rank()` filters by
latency and sorts → `emit()` writes the Markdown table or the JSON.

A machine-derived map of the same tree lives in `ARCHITECTURE.md` at the
repository root; regenerate it with `automap map`.

## Decisions

- Bundled data is conservative yearly averages: good enough for placement
  decisions without a network call or token.
- Live mode is opt-in to keep the default path offline and dependency-light.
