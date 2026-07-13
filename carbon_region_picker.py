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
}
VANTAGE = {"eu": 3, "us-east": 4}


def rank(
    provider: str = "aws",
    near: str = "eu",
    max_latency_ms: int | None = None,
    live_intensities: dict[str, float] | None = None,
) -> list[dict]:
    """Return regions sorted by carbon intensity, dropping any over the latency cap."""
    idx = VANTAGE.get(near, 3)
    rows = []
    for entry in REGIONS[provider]:
        region, zone, intensity, *rtts = entry
        rtt = entry[idx]
        if live_intensities and zone in live_intensities:
            intensity = live_intensities[zone]
        if max_latency_ms and rtt > max_latency_ms:
            continue
        rows.append({"region": region, "zone": zone, "gco2_kwh": intensity, "latency_ms": rtt})
    rows.sort(key=lambda r: r["gco2_kwh"])
    return rows


def fetch_live(zones: set[str], token: str) -> dict[str, float]:
    """Query Electricity Maps for the current intensity of each zone."""
    import requests

    out = {}
    for zone in zones:
        r = requests.get(
            "https://api.electricitymap.org/v3/carbon-intensity/latest",
            params={"zone": zone},
            headers={"auth-token": token},
            timeout=15,
        )
        if r.ok:
            out[zone] = r.json().get("carbonIntensity")
    return out


def render(rows: list[dict], near: str, max_latency_ms: int | None) -> str:
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
    p.add_argument("--live", action="store_true", help="use Electricity Maps real-time data")
    p.add_argument(
        "--em-token",
        help="Electricity Maps API token. Prefer the EM_TOKEN env var; a token "
        "passed here is visible in the process list.",
    )
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    live = None
    if args.live:
        import os

        token = args.em_token or os.environ.get("EM_TOKEN")
        if not token:
            print("carbon-region-picker: --live needs --em-token or EM_TOKEN", file=sys.stderr)
            return 64
        live = fetch_live({e[1] for e in REGIONS[args.provider]}, token)

    rows = rank(args.provider, args.near, args.max_latency_ms, live)
    if args.json:
        json.dump(rows, sys.stdout, indent=2)
    else:
        print(render(rows, args.near, args.max_latency_ms))
    return 0


if __name__ == "__main__":
    sys.exit(main())
