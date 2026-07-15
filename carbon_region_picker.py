#!/usr/bin/env python3
"""carbon-region-picker — rank cloud regions by grid carbon intensity,
subject to a latency constraint.

  carbon-region-picker --provider aws --near eu --max-latency-ms 60
  carbon-region-picker --provider aws --live --em-token $ELECTRICITYMAPS_TOKEN

Without --live it uses bundled yearly-average intensities (documented,
conservative). With --live it queries Electricity Maps for real-time data.
"""

import argparse
import json
import sys

# Bundled fallback dataset: yearly-average grid intensity (gCO2e/kWh) for the
# grid zone each region sits in, and rough RTT from EU/US-East vantage points.
# Sources: ElectricityMaps yearly summaries + public latency matrices.
REGIONS = {
    "aws": [
        # region, zone, gCO2/kWh, rtt_eu_ms, rtt_use_ms
        ("eu-north-1", "SE", 25, 35, 115),
        ("eu-west-3", "FR", 56, 20, 90),
        ("ca-central-1", "CA-QC", 30, 95, 25),
        ("eu-central-1", "DE", 380, 15, 95),
        ("eu-west-1", "IE", 290, 25, 80),
        ("us-east-1", "US-VA", 390, 90, 5),
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
        ("eastus", "US-VA", 390, 90, 5),
        ("westus2", "US-NW-PACW", 90, 135, 65),
        ("southeastasia", "SG", 400, 160, 220),
        ("australiaeast", "AU-NSW", 550, 280, 210),
        ("centralindia", "IN-WE", 650, 120, 200),
    ],
}
VANTAGE = {"eu": 3, "us-east": 4}

# Per-region public hostnames used by --measure. Azure has no stable
# per-region hostname without a resource name, so it's left out and
# --measure keeps the bundled estimate for those rows.
ENDPOINTS = {
    "aws": lambda region: (f"ec2.{region}.amazonaws.com", 443),
    "gcp": lambda region: (f"{region}-run.googleapis.com", 443),
}


def rank(
    provider: str = "aws",
    near: str = "eu",
    max_latency_ms: int | None = None,
    live_intensities: dict[str, float] | None = None,
    measured_latencies: dict[str, float] | None = None,
) -> list[dict]:
    """Return regions sorted by carbon intensity, dropping any over the latency cap."""
    idx = VANTAGE.get(near, 3)
    rows = []
    for entry in REGIONS[provider]:
        region, zone, intensity, *rtts = entry
        rtt = entry[idx]
        if live_intensities and zone in live_intensities:
            intensity = live_intensities[zone]
        if measured_latencies and region in measured_latencies:
            rtt = measured_latencies[region]
        if max_latency_ms and rtt > max_latency_ms:
            continue
        rows.append(
            {"region": region, "zone": zone, "gco2_kwh": intensity, "latency_ms": round(rtt, 1)}
        )
    rows.sort(key=lambda r: r["gco2_kwh"])
    return rows


def measure_latency_ms(host: str, port: int = 443, timeout: float = 2.0) -> float | None:
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
    out = {}
    for entry in REGIONS[provider]:
        region = entry[0]
        host, port = endpoint_for(region)
        ms = measure_latency_ms(host, port)
        if ms is not None:
            out[region] = ms
    return out


def fetch_live(zones: set[str], token: str, marginal: bool = False) -> dict[str, float]:
    """Query Electricity Maps for the current intensity of each zone.

    `marginal=True` asks for the marginal rather than average grid intensity
    (the rate the *next* unit of demand would be served at).
    """
    import requests

    path = "marginal-carbon-intensity" if marginal else "carbon-intensity"
    out = {}
    for zone in zones:
        r = requests.get(
            f"https://api.electricitymap.org/v3/{path}/latest",
            params={"zone": zone},
            headers={"auth-token": token},
            timeout=15,
        )
        if r.ok:
            out[zone] = r.json().get("carbonIntensity")
    return out


def fetch_forecast(zone: str, token: str) -> list[dict]:
    """Query Electricity Maps for the zone's 24h carbon-intensity forecast."""
    import requests

    r = requests.get(
        "https://api.electricitymap.org/v3/carbon-intensity/forecast",
        params={"zone": zone},
        headers={"auth-token": token},
        timeout=15,
    )
    if not r.ok:
        return []
    return r.json().get("forecast", [])


def best_forecast_slot(forecast: list[dict]) -> dict | None:
    """Return the forecast entry with the lowest intensity — e.g. tonight's cleanest hour."""
    if not forecast:
        return None
    return min(forecast, key=lambda f: f["carbonIntensity"])


def render(
    rows: list[dict],
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
    for i, r in enumerate(rows, 1):
        marker = " 🌱" if r["gco2_kwh"] < 100 else ""
        lines.append(f"| {i} | {r['region']}{marker} | {r['gco2_kwh']} | {r['latency_ms']}ms |")
    if rows:
        best, worst = rows[0], rows[-1]
        if worst["gco2_kwh"] > best["gco2_kwh"]:
            factor = worst["gco2_kwh"] / max(best["gco2_kwh"], 1)
            lines.append(
                f"\nPicking `{best['region']}` over `{worst['region']}` cuts "
                f"compute carbon ~{factor:.0f}x."
            )
        if best_slot:
            lines.append(
                f"\nCleanest hour in the next 24h for `{best['region']}`: "
                f"{best_slot['datetime']} ({best_slot['carbonIntensity']} gCO2e/kWh)."
            )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: parse args, optionally fetch live data, print the ranking."""
    p = argparse.ArgumentParser(
        prog="carbon-region-picker",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--provider", default="aws", choices=sorted(REGIONS.keys()))
    p.add_argument(
        "--near", default="eu", choices=sorted(VANTAGE.keys()), help="latency vantage point"
    )
    p.add_argument("--max-latency-ms", type=int)
    p.add_argument(
        "--measure",
        action="store_true",
        help="probe real TCP latency to each region's endpoint instead of the bundled "
        "estimate (aws/gcp only)",
    )
    p.add_argument("--live", action="store_true", help="use Electricity Maps real-time data")
    p.add_argument(
        "--marginal",
        action="store_true",
        help="use marginal instead of average grid intensity (requires --live)",
    )
    p.add_argument(
        "--forecast",
        action="store_true",
        help="suggest the cleanest hour in the next 24h for the top region (requires --live)",
    )
    p.add_argument(
        "--em-token",
        help="Electricity Maps API token. Prefer the EM_TOKEN env var; a token "
        "passed here is visible in the process list.",
    )
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    if (args.marginal or args.forecast) and not args.live:
        print("carbon-region-picker: --marginal/--forecast require --live", file=sys.stderr)
        return 64

    live = None
    token = None
    if args.live:
        import os

        token = args.em_token or os.environ.get("EM_TOKEN")
        if not token:
            print("carbon-region-picker: --live needs --em-token or EM_TOKEN", file=sys.stderr)
            return 64
        live = fetch_live({e[1] for e in REGIONS[args.provider]}, token, marginal=args.marginal)

    measured = measure_all(args.provider) if args.measure else None
    rows = rank(args.provider, args.near, args.max_latency_ms, live, measured)

    best_slot = None
    if args.forecast and rows:
        best_slot = best_forecast_slot(fetch_forecast(rows[0]["zone"], token))

    if args.json:
        out = {"regions": rows}
        if best_slot:
            out["best_forecast_slot"] = best_slot
        json.dump(out if best_slot else rows, sys.stdout, indent=2)
    else:
        print(render(rows, args.near, args.max_latency_ms, best_slot))
    return 0


if __name__ == "__main__":
    sys.exit(main())
