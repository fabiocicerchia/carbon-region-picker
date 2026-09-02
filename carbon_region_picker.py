#!/usr/bin/env python3
"""carbon-region-picker — rank cloud regions by grid carbon intensity,
subject to a latency constraint.

  carbon-region-picker --provider aws --near eu --max-latency-ms 60
  carbon-region-picker --provider aws --live --em-token $ELECTRICITYMAPS_TOKEN

Without --live it uses bundled yearly-average intensities (documented,
conservative). With --live it queries Electricity Maps for real-time data.
"""

import argparse
import dataclasses
import json
import sys

HTTPS_PORT = 443
# Below this a grid counts as clean and the region gets the 🌱 marker.
CLEAN_GRID_GCO2_KWH = 100

# Bundled fallback dataset: yearly-average grid intensity (gCO2e/kWh) for the
# grid zone each region sits in, and rough RTT from EU/US-East vantage points.
# Hand-transcribed, undated — treat as approximate. To refresh or verify a
# zone code, use:
#   - Zone-code registry (valid IDs the live API accepts):
#     https://github.com/electricitymaps/electricitymaps-contrib/tree/master/config/zones
#   - Country-level yearly averages (free, versioned CSV):
#     https://files.ember-energy.org/public-downloads/yearly_full_release_long_format.csv
#   - Sub-national zones Ember doesn't cover (US balancing authorities, CA-QC,
#     IN-WE, AU-NSW): https://app.electricitymaps.com/zone/<ZONE> (no static
#     dataset at this granularity without a paid API token — check by hand).
# Latency: rough public latency matrices, also undated.
REGIONS = {
    "aws": [
        # region, zone, gCO2/kWh, rtt_eu_ms, rtt_use_ms
        ("eu-north-1", "SE", 25, 35, 115),
        ("eu-west-3", "FR", 56, 20, 90),
        ("ca-central-1", "CA-QC", 30, 95, 25),
        ("eu-central-1", "DE", 380, 15, 95),
        ("eu-west-1", "IE", 290, 25, 80),
        ("us-east-1", "US-MIDA-PJM", 390, 90, 5),
        # ponytail: "US-OR" is not a real EM zone code (see registry above) —
        # Boardman/Umatilla OR is likely US-NW-BPAT or US-NW-PACW depending on
        # the exact substation, but left unverified rather than guessed.
        # --live silently falls back to this bundled value for this region
        # until the correct zone is confirmed and swapped in.
        ("us-west-2", "US-OR", 120, 140, 70),
        ("ap-southeast-2", "AU-NSW", 550, 280, 210),
        ("ap-south-1", "IN-WE", 650, 120, 200),
    ],
    "gcp": [
        ("europe-north1", "FI", 95, 30, 120),
        ("europe-west1", "BE", 165, 15, 90),
        ("us-central1", "US-MIDW-MISO", 430, 100, 35),
        ("us-west1", "US-NW-PACW", 90, 140, 70),
        ("asia-southeast1", "SG", 400, 160, 220),
        ("australia-southeast1", "AU-NSW", 550, 280, 210),
        ("asia-south1", "IN-WE", 650, 120, 200),
    ],
    "azure": [
        ("northeurope", "IE", 290, 25, 80),
        ("westeurope", "NL", 300, 20, 90),
        ("eastus", "US-MIDA-PJM", 390, 90, 5),
        ("westus2", "US-NW-PACW", 90, 135, 65),
        ("southeastasia", "SG", 400, 160, 220),
        ("australiaeast", "AU-NSW", 550, 280, 210),
        ("centralindia", "IN-WE", 650, 120, 200),
    ],
}
VANTAGE = {"eu": 0, "us-east": 1}  # index into the rtt_* tail of a REGIONS entry

# Per-region public hostnames used by --measure. Azure has no stable
# per-region hostname without a resource name, so it's left out and
# --measure keeps the bundled estimate for those rows.
ENDPOINTS = {
    "aws": lambda region: (f"ec2.{region}.amazonaws.com", HTTPS_PORT),
    "gcp": lambda region: (f"{region}-run.googleapis.com", HTTPS_PORT),
}


@dataclasses.dataclass(frozen=True)
class RankedRegion:
    """One row of the ranking. Field order is the JSON key order."""

    region: str
    zone: str
    gco2_kwh: float
    latency_ms: float


def rank(
    provider: str = "aws",
    near: str = "eu",
    max_latency_ms: int | None = None,
    live_intensities: dict[str, float] | None = None,
    measured_latencies: dict[str, float] | None = None,
) -> list[RankedRegion]:
    """Return regions sorted by carbon intensity, dropping any over the latency cap."""
    rtt_index = VANTAGE.get(near, 0)
    rows = []
    for entry in REGIONS[provider]:
        region, zone, base_intensity, *rtts = entry
        gco2_kwh = float(base_intensity)
        rtt = float(rtts[rtt_index])
        if live_intensities and zone in live_intensities:
            gco2_kwh = live_intensities[zone]
        if measured_latencies and region in measured_latencies:
            rtt = measured_latencies[region]
        if max_latency_ms and rtt > max_latency_ms:
            continue
        rows.append(RankedRegion(region, zone, gco2_kwh, round(rtt, 1)))
    rows.sort(key=lambda row: row.gco2_kwh)
    return rows


def measure_latency_ms(host: str, port: int = HTTPS_PORT, timeout: float = 2.0) -> float | None:
    """TCP-connect timing to a region endpoint; None if it can't be reached."""
    import socket
    import time

    start = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            pass
    except OSError:
        return None
    return (time.perf_counter() - start) * 1000


def measure_all(provider: str) -> dict[str, float]:
    """Measure real latency to every region's endpoint for a provider, where known."""
    endpoint_for = ENDPOINTS.get(provider)
    if not endpoint_for:
        return {}
    latencies = {}
    for entry in REGIONS[provider]:
        region = entry[0]
        host, port = endpoint_for(region)
        ms = measure_latency_ms(host, port)
        if ms is not None:
            latencies[region] = ms
    return latencies


def _em_get(path: str, zone: str, token: str) -> dict | None:
    """GET an Electricity Maps `/v3/<path>/latest`-or-`/forecast`-style endpoint for a zone."""
    import requests

    response = requests.get(
        f"https://api.electricitymap.org/v3/{path}",
        params={"zone": zone},
        headers={"auth-token": token},
        timeout=15,
    )
    return response.json() if response.ok else None


def fetch_live(zones: set[str], token: str, marginal: bool = False) -> dict[str, float]:
    """Query Electricity Maps for the current intensity of each zone.

    `marginal=True` asks for the marginal rather than average grid intensity
    (the rate the *next* unit of demand would be served at).
    """
    path = "marginal-carbon-intensity/latest" if marginal else "carbon-intensity/latest"
    intensities = {}
    for zone in zones:
        latest = _em_get(path, zone, token)
        if latest is not None:
            intensities[zone] = latest.get("carbonIntensity")
    return intensities


def fetch_forecast(zone: str, token: str) -> list[dict]:
    """Query Electricity Maps for the zone's 24h carbon-intensity forecast."""
    payload = _em_get("carbon-intensity/forecast", zone, token)
    return payload.get("forecast", []) if payload else []


def best_forecast_slot(forecast: list[dict]) -> dict | None:
    """Return the forecast entry with the lowest intensity — e.g. tonight's cleanest hour."""
    if not forecast:
        return None
    return min(forecast, key=lambda slot: slot["carbonIntensity"])


def render(
    rows: list[RankedRegion],
    near: str,
    max_latency_ms: int | None,
    best_slot: dict | None = None,
) -> str:
    """Render the ranked regions as a Markdown table with a savings footnote."""
    constraint = f" (≤{max_latency_ms}ms from {near})" if max_latency_ms else ""
    lines = [
        f"# Regions by carbon intensity{constraint}\n",
        "| rank | region | gCO2e/kWh | latency |",
        "|---|---|---|---|",
    ]
    for i, row in enumerate(rows, 1):
        marker = " 🌱" if row.gco2_kwh < CLEAN_GRID_GCO2_KWH else ""
        lines.append(f"| {i} | {row.region}{marker} | {row.gco2_kwh} | {row.latency_ms}ms |")
    if rows:
        best, worst = rows[0], rows[-1]
        if worst.gco2_kwh > best.gco2_kwh:
            factor = worst.gco2_kwh / max(best.gco2_kwh, 1)
            lines.append(
                f"\nPicking `{best.region}` over `{worst.region}` cuts "
                f"compute carbon ~{factor:.0f}x."
            )
        if best_slot:
            lines.append(
                f"\nCleanest hour in the next 24h for `{best.region}`: "
                f"{best_slot['datetime']} ({best_slot['carbonIntensity']} gCO2e/kWh)."
            )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    """Declare the command line. Kept apart so main() reads as a list of steps."""
    parser = argparse.ArgumentParser(
        prog="carbon-region-picker",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--provider", default="aws", choices=sorted(REGIONS.keys()))
    parser.add_argument(
        "--near", default="eu", choices=sorted(VANTAGE.keys()), help="latency vantage point"
    )
    parser.add_argument("--max-latency-ms", type=int)
    parser.add_argument(
        "--measure",
        action="store_true",
        help="probe real TCP latency to each region's endpoint instead of the bundled "
        "estimate (aws/gcp only)",
    )
    parser.add_argument("--live", action="store_true", help="use Electricity Maps real-time data")
    parser.add_argument(
        "--marginal",
        action="store_true",
        help="use marginal instead of average grid intensity (requires --live)",
    )
    parser.add_argument(
        "--forecast",
        action="store_true",
        help="suggest the cleanest hour in the next 24h for the top region (requires --live)",
    )
    parser.add_argument(
        "--em-token",
        help="Electricity Maps API token. Prefer the EM_TOKEN env var; a token "
        "passed here is visible in the process list.",
    )
    parser.add_argument("--json", action="store_true")
    return parser


def resolve_token(args: argparse.Namespace) -> str | None:
    """The Electricity Maps token: --em-token first, else the EM_TOKEN env var."""
    import os

    return args.em_token or os.environ.get("EM_TOKEN")


def emit(rows: list[RankedRegion], best_slot: dict | None, args: argparse.Namespace) -> None:
    """Write the ranking to stdout, as JSON or as the Markdown table."""
    if args.json:
        records = [dataclasses.asdict(row) for row in rows]
        out: dict[str, object] = {"regions": records}
        if best_slot:
            out["best_forecast_slot"] = best_slot
        json.dump(out if best_slot else records, sys.stdout, indent=2)
    else:
        print(render(rows, args.near, args.max_latency_ms, best_slot))


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: parse args, optionally fetch live data, print the ranking."""
    args = build_parser().parse_args(argv)

    if (args.marginal or args.forecast) and not args.live:
        print("carbon-region-picker: --marginal/--forecast require --live", file=sys.stderr)
        return 64

    live = None
    token = None
    if args.live:
        token = resolve_token(args)
        if not token:
            print("carbon-region-picker: --live needs --em-token or EM_TOKEN", file=sys.stderr)
            return 64
        live = fetch_live({e[1] for e in REGIONS[args.provider]}, token, marginal=args.marginal)

    measured = measure_all(args.provider) if args.measure else None
    rows = rank(args.provider, args.near, args.max_latency_ms, live, measured)

    best_slot = None
    if args.forecast and rows:
        # Guaranteed set: the early-return above requires --live (and a token)
        # whenever --forecast is passed.
        assert token is not None
        best_slot = best_forecast_slot(fetch_forecast(rows[0].zone, token))

    emit(rows, best_slot, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
