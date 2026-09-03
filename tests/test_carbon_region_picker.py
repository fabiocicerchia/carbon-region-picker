"""Tests for the carbon-region-picker ranking, rendering, and CLI."""

import json
import socket
from dataclasses import fields

import pytest

from carbon_region_picker import (
    best_forecast_slot,
    fetch_forecast,
    fetch_live,
    main,
    measure_all,
    measure_latency_ms,
    rank,
    render,
)


def test_rank_sorts_by_intensity():
    """Regions come back ordered from cleanest to dirtiest grid."""
    rows = rank(near="eu")
    intensities = [r.gco2_kwh for r in rows]
    assert intensities == sorted(intensities)
    assert rows[0].region == "eu-north-1"


def test_latency_constraint_filters():
    """A latency cap drops regions beyond it while keeping those within."""
    rows = rank(near="eu", max_latency_ms=40)
    assert all(r.latency_ms <= 40 for r in rows)
    assert any(r.region == "eu-central-1" for r in rows)
    assert not any(r.region == "us-east-1" for r in rows)


def test_live_overrides_bundled_values():
    """A live intensity for a zone replaces its bundled value."""
    rows = rank(near="eu", live_intensities={"DE": 90})
    de = next(r for r in rows if r.zone == "DE")
    assert de.gco2_kwh == 90


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
        main(["--provider", "oci"])


def test_gcp_and_azure_region_sets():
    """GCP and Azure rank like AWS: sorted by intensity, same record shape."""
    for provider in ("gcp", "azure"):
        rows = rank(provider=provider, near="eu")
        assert rows
        assert [r.gco2_kwh for r in rows] == sorted(r.gco2_kwh for r in rows)
        assert {f.name for f in fields(rows[0])} == {"region", "zone", "gco2_kwh", "latency_ms"}


def test_missing_token_returns_error(monkeypatch):
    """--live without a token (flag or env) exits with a usage error."""
    monkeypatch.delenv("EM_TOKEN", raising=False)
    assert main(["--live"]) == 64


def test_measure_latency_ms_success():
    """A reachable TCP endpoint returns a non-negative round-trip time."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    host, port = srv.getsockname()
    try:
        ms = measure_latency_ms(host, port, timeout=1)
        assert ms is not None and ms >= 0
    finally:
        srv.close()


def test_measure_latency_ms_unreachable():
    """A closed local port returns None instead of raising."""
    assert measure_latency_ms("127.0.0.1", 1, timeout=0.5) is None


def test_measure_all_unknown_provider_is_noop():
    """Azure has no per-region endpoint convention, so --measure is a no-op for it."""
    assert measure_all("azure") == {}


def test_rank_uses_measured_latency_over_bundled():
    """A measured latency for a region overrides its bundled estimate."""
    rows = rank(near="eu", measured_latencies={"eu-north-1": 999})
    en = next(r for r in rows if r.region == "eu-north-1")
    assert en.latency_ms == 999


def test_best_forecast_slot_picks_lowest():
    """The forecast slot with the lowest carbon intensity wins."""
    forecast = [
        {"datetime": "2026-07-15T22:00:00Z", "carbonIntensity": 120},
        {"datetime": "2026-07-16T02:00:00Z", "carbonIntensity": 40},
        {"datetime": "2026-07-16T06:00:00Z", "carbonIntensity": 90},
    ]
    assert best_forecast_slot(forecast)["datetime"] == "2026-07-16T02:00:00Z"


def test_best_forecast_slot_empty():
    """No forecast data means no suggested slot."""
    assert best_forecast_slot([]) is None


def test_fetch_live_marginal_hits_marginal_endpoint(monkeypatch):
    """--marginal switches fetch_live to the marginal-intensity endpoint."""
    calls = []

    class FakeResp:
        ok = True

        def json(self):
            return {"carbonIntensity": 42}

    monkeypatch.setattr("requests.get", lambda url, **kw: calls.append(url) or FakeResp())
    out = fetch_live({"SE"}, "tok", marginal=True)
    assert out == {"SE": 42}
    assert "marginal-carbon-intensity" in calls[0]


def test_fetch_forecast_returns_list(monkeypatch):
    """fetch_forecast unwraps the API's forecast array."""

    class FakeResp:
        ok = True

        def json(self):
            return {"forecast": [{"datetime": "x", "carbonIntensity": 1}]}

    monkeypatch.setattr("requests.get", lambda url, **kw: FakeResp())
    assert fetch_forecast("SE", "tok") == [{"datetime": "x", "carbonIntensity": 1}]


def test_render_includes_forecast_note():
    """render() appends the cleanest-hour suggestion when a best_slot is given."""
    out = render(
        rank(near="eu"), "eu", None, best_slot={"datetime": "02:00", "carbonIntensity": 10}
    )
    assert "Cleanest hour" in out and "02:00" in out


def test_marginal_without_live_rejected():
    """--marginal only makes sense with --live."""
    assert main(["--marginal"]) == 64


def test_forecast_without_live_rejected():
    """--forecast only makes sense with --live."""
    assert main(["--forecast"]) == 64


def test_json_output_is_valid(capsys):
    """--json emits a parseable list of region records."""
    assert main(["--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list) and data[0]["region"] == "eu-north-1"
