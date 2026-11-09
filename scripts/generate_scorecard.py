#!/usr/bin/env python3
"""Rate every mapped cloud region A-F by its country's yearly grid intensity.

  python scripts/generate_scorecard.py

Joins data/regions-map.json (provider -> region -> country) with Ember's yearly
grid emissions intensity, latest year per country, and writes data/regions-carbon-score.json
and docs/scorecard.md. Standard library only, like the picker itself.
"""

import csv
import io
import json
import sys
import urllib.request
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EMBER_CSV = "https://files.ember-energy.org/public-downloads/generation/outputs/release_generation_yearly_global.csv"
# One row per area, year and source; the all-sources row carries the grid's intensity.
TOTAL_SOURCE = "Total generation"
INTENSITY = "Emissions intensity (gCO2e/kWh)"
ROOT = Path(__file__).resolve().parent.parent
REGIONS_MAP = ROOT / "data" / "regions-map.json"
ISO2_NAMES = ROOT / "data" / "iso2-country-map.json"
SCORE_FILE = ROOT / "data" / "regions-carbon-score.json"
SCORECARD_MD = ROOT / "docs" / "scorecard.md"

# Upper bounds in gCO2e/kWh; a value lands in the first band it is below.
RATING_BANDS: list[tuple[str, float, float]] = [
    ("A", 0, 100),
    ("B", 100, 200),
    ("C", 200, 350),
    ("D", 350, 500),
    ("E", 500, 650),
    ("F", 650, float("inf")),
]
UNKNOWN = "U"
RATING_EMOJI = {"A": "🟢", "B": "🟡", "C": "🟠", "D": "🟤", "E": "🔴", "F": "🟣", UNKNOWN: "⚪"}
RATING_ORDER = {label: i for i, (label, _, _) in enumerate(RATING_BANDS)} | {UNKNOWN: len(RATING_BANDS)}


def rating_for(value: float | None) -> str:
    """The band a grid intensity falls in, or U when there is no number."""
    if value is None:
        return UNKNOWN
    return next((label for label, lo, hi in RATING_BANDS if lo <= value < hi), UNKNOWN)


def latest_intensities(rows: Iterable[dict[str, str]]) -> tuple[dict[str, float], dict[str, int]]:
    """Ember's yearly rows to {area: grid intensity in its latest year}, plus the year range."""
    latest: dict[str, tuple[int, float]] = {}
    years: list[int] = []
    for row in rows:
        if row.get("Electricity source") != TOTAL_SOURCE or not row.get(INTENSITY) or not row.get("Year"):
            continue
        year, value = int(row["Year"]), float(row[INTENSITY])
        years.append(year)
        if row["Area"] not in latest or year > latest[row["Area"]][0]:
            latest[row["Area"]] = (year, value)
    if not years:
        msg = f"no {TOTAL_SOURCE!r} rows with an intensity in the Ember dataset"
        raise ValueError(msg)
    return {area: value for area, (_, value) in latest.items()}, {
        "min": min(years),
        "max": max(years),
        "rows": len(years),
    }


def resolve_area(country: str, areas: dict[str, float], iso2_names: dict[str, str]) -> str | None:
    """An ISO-2 code or a country name to the Ember Area it is published under."""
    if country in areas:
        return country
    if iso2_names.get(country) in areas:
        return iso2_names[country]
    lowered = country.strip().lower()
    return next((area for area in areas if area.lower() == lowered), None)


def build_scores(
    region_map: dict[str, dict[str, str]],
    areas: dict[str, float],
    years: dict[str, int],
    iso2_names: dict[str, str],
    now: datetime,
) -> dict[str, Any]:
    """The regions-carbon-score.json document, schema 1.0."""
    providers: dict[str, Any] = {}
    for provider, regions in sorted(region_map.items()):
        rated: dict[str, Any] = {}
        for region, country in sorted(regions.items()):
            area = resolve_area(country, areas, iso2_names)
            intensity = areas.get(area) if area else None
            rated[region] = {
                "country_input": country,
                "ember_area": area,
                "grid_intensity_gco2e_per_kwh": intensity,
                "rating": rating_for(intensity),
            }
        providers[provider] = {"regions": rated}
    bands: dict[str, list[float | None] | None] = {
        label: [lo, None if hi == float("inf") else hi] for label, lo, hi in RATING_BANDS
    }
    return {
        "schema_version": "1.0",
        "generated_at_utc": now.isoformat(),
        "methodology": {
            "grid_intensity_source": {
                "name": "Ember",
                "dataset_url": EMBER_CSV,
                "metric": f"{INTENSITY}, {TOTAL_SOURCE.lower()}",
                "latest_year_in_dataset": years["max"],
            },
            "rating_bands_gco2e_per_kwh": bands | {UNKNOWN: None},
        },
        "providers": providers,
    }


def render_markdown(scores: dict[str, Any]) -> str:
    """docs/scorecard.md: the bands, one table per provider, cleanest first, and the method."""
    source = scores["methodology"]["grid_intensity_source"]
    lines = [
        "# Cloud region carbon scorecard",
        "",
        f"_Generated {scores['generated_at_utc']} by `scripts/generate_scorecard.py`; do not edit by hand._",
        "",
        "Every mapped region of nine providers, rated by the yearly grid intensity of the",
        "country it sits in. Country-level and yearly, so coarser than the picker's zones:",
        "use it to compare providers and regions, not to schedule an hour.",
        "",
        "## Rating bands (gCO₂e/kWh)",
        "",
    ]
    for label, lo, hi in RATING_BANDS:
        span = f"{lo:g}+" if hi == float("inf") else f"{lo:g}-{hi:g}"
        lines.append(f"- {RATING_EMOJI[label]} **{label}**: {span}")
    lines += [f"- {RATING_EMOJI[UNKNOWN]} **{UNKNOWN}**: no data", ""]
    for provider, data in sorted(scores["providers"].items()):
        regions: dict[str, Any] = data["regions"]
        lines += [
            f"## {provider.upper()}",
            "",
            "| Region | Country | Rating | gCO₂e/kWh |",
            "|--------|---------|--------|-----------|",
        ]

        def order(item: tuple[str, Any]) -> tuple[int, float, str]:
            region, row = item
            intensity = row["grid_intensity_gco2e_per_kwh"]
            return RATING_ORDER[row["rating"]], float("inf") if intensity is None else intensity, region

        for region, row in sorted(regions.items(), key=order):
            intensity = row["grid_intensity_gco2e_per_kwh"]
            shown = "N/A" if intensity is None else f"{intensity:.2f}"
            rating = row["rating"]
            lines.append(f"| `{region}` | {row['country_input']} | {RATING_EMOJI[rating]} {rating} | {shown} |")
        lines.append("")
    lines += [
        "## Method",
        "",
        f"- Source: {source['name']}, [{source['metric']}]({source['dataset_url']}),"
        f" latest year per country (newest in the dataset: {source['latest_year_in_dataset']}).",
        "- Mapping: `data/regions-map.json`, provider region to ISO 3166-1 alpha-2 or an Ember area name;"
        " `data/iso2-country-map.json` translates the codes Ember spells out.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    """Download Ember, rate every region, write the JSON and the Markdown page."""
    region_map: dict[str, dict[str, str]] = json.loads(REGIONS_MAP.read_text(encoding="utf-8"))
    iso2_names: dict[str, str] = json.loads(ISO2_NAMES.read_text(encoding="utf-8"))
    with urllib.request.urlopen(EMBER_CSV, timeout=300) as response:
        areas, years = latest_intensities(csv.DictReader(io.TextIOWrapper(response, encoding="utf-8")))
    scores = build_scores(region_map, areas, years, iso2_names, datetime.now(timezone.utc))
    SCORE_FILE.write_text(json.dumps(scores, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SCORECARD_MD.write_text(render_markdown(scores), encoding="utf-8")
    sys.stdout.write(f"wrote {SCORE_FILE.relative_to(ROOT)} and {SCORECARD_MD.relative_to(ROOT)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
