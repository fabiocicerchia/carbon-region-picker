"""Tests for the carbon-region-picker ranking, rendering, and CLI."""

import json

import pytest

from carbon_region_picker import main, rank, render


def test_rank_sorts_by_intensity():
    """Regions come back ordered from cleanest to dirtiest grid."""
    rows = rank(near="eu")
    intensities = [r["gco2_kwh"] for r in rows]
    assert intensities == sorted(intensities)
    assert rows[0]["region"] == "eu-north-1"


def test_latency_constraint_filters():
    """A latency cap drops regions beyond it while keeping those within."""
    rows = rank(near="eu", max_latency_ms=40)
    assert all(r["latency_ms"] <= 40 for r in rows)
    assert any(r["region"] == "eu-central-1" for r in rows)
    assert not any(r["region"] == "us-east-1" for r in rows)


def test_live_overrides_bundled_values():
    """A live intensity for a zone replaces its bundled value."""
    rows = rank(near="eu", live_intensities={"DE": 90})
    de = next(r for r in rows if r["zone"] == "DE")
    assert de["gco2_kwh"] == 90


def test_live_ignores_unknown_zone():
    """Live data for a zone we don't ship leaves the ranking untouched."""
    baseline = rank(near="eu")
    rows = rank(near="eu", live_intensities={"XX-ZZ": 1})
    assert rows == baseline


def test_render_mentions_savings_factor():
    """The rendered table includes the savings note and clean-grid marker."""
    out = render(rank(near="eu"), "eu", None)
    assert "cuts" in out and "🌱" in out


def test_unknown_provider_rejected():
    """An unsupported --provider is rejected by argument parsing."""
    with pytest.raises(SystemExit):
        main(["--provider", "gcp"])


def test_missing_token_returns_error(monkeypatch):
    """--live without a token (flag or env) exits with a usage error."""
    monkeypatch.delenv("EM_TOKEN", raising=False)
    assert main(["--live"]) == 64


def test_json_output_is_valid(capsys):
    """--json emits a parseable list of region records."""
    assert main(["--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list) and data[0]["region"] == "eu-north-1"
