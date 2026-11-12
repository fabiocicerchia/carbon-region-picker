"""Tests for the region scorecard generator, offline: Ember rows are built in memory."""

from datetime import datetime, timezone

from scripts.generate_scorecard import (
    INTENSITY,
    TOTAL_SOURCE,
    build_scores,
    latest_intensities,
    rating_for,
    render_markdown,
    resolve_area,
)


def _row(area: str, year: int, value: str, source: str = TOTAL_SOURCE) -> dict[str, str]:
    return {"Area": area, "Year": str(year), "Electricity source": source, INTENSITY: value}


def test_rating_bands_are_half_open() -> None:
    """A value on a boundary belongs to the band above it; no number is U."""
    assert rating_for(99.9) == "A"
    assert rating_for(100) == "B"
    assert rating_for(650) == "F"
    assert rating_for(None) == "U"


def test_latest_year_of_the_total_wins() -> None:
    """Only the all-sources row counts, and a later year replaces an earlier one."""
    rows = [
        _row("France", 2024, "40"),
        _row("France", 2025, "30"),
        _row("France", 2025, "900", source="Coal"),
        _row("Chad", 2025, ""),
    ]
    areas, years = latest_intensities(rows)
    assert areas == {"France": 30.0}
    assert years == {"min": 2024, "max": 2025, "rows": 2}


def test_country_codes_resolve_through_the_name_map() -> None:
    """An ISO-2 code finds its Ember spelling; an unknown one stays unresolved."""
    areas = {"United States": 380.0, "France": 30.0}
    assert resolve_area("US", areas, {"US": "United States"}) == "United States"
    assert resolve_area("france", areas, {}) == "France"
    assert resolve_area("XX", areas, {}) is None


def test_scores_and_page_rank_cleanest_first() -> None:
    """Each region is rated, and the page lists a provider's regions A to U."""
    scores = build_scores(
        {"aws": {"us-east-1": "US", "eu-west-3": "FR", "xx-1": "XX"}},
        {"United States": 380.0, "France": 30.0},
        {"min": 2025, "max": 2025, "rows": 2},
        {"US": "United States", "FR": "France"},
        datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    regions = scores["providers"]["aws"]["regions"]
    assert [regions[r]["rating"] for r in ("eu-west-3", "us-east-1", "xx-1")] == ["A", "D", "U"]
    page = render_markdown(scores)
    assert page.index("`eu-west-3`") < page.index("`us-east-1`") < page.index("`xx-1`")
