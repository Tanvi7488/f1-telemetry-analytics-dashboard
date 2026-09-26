"""
tests/test_analysis.py
------------------------
Unit tests for utils/analysis.py.

Scope note: these tests cover the *pure* computation functions
(format_timedelta, format_speed, compute_average_speed_from_telemetry,
compute_delta_time, build_lap_summary) directly with synthetic data,
plus the lap-selection logic (get_fastest_lap / _filter_valid_laps)
using the FakeSession/FakeLaps test doubles from conftest.py.

get_lap_telemetry() is intentionally NOT unit tested here: it is a
one-line delegation to FastF1's own get_car_data()/add_distance(),
which is FastF1's responsibility to test, not this project's. Testing
it meaningfully would require either a live network call or
reimplementing FastF1 internals as a mock — neither adds confidence
proportional to the effort. This is a deliberate testing-boundary
decision, not an oversight.
"""

import math

import pandas as pd
import pytest

from tests.conftest import FakeLap
from utils.analysis import (
    format_timedelta,
    format_speed,
    compute_average_speed_from_telemetry,
    compute_delta_time,
    build_lap_summary,
    get_fastest_lap,
    _filter_valid_laps,
)


# ==========================================================================
# format_timedelta
# ==========================================================================

def test_format_timedelta_typical_lap():
    td = pd.Timedelta(minutes=1, seconds=32, milliseconds=190)
    assert format_timedelta(td) == "1:32.190"


def test_format_timedelta_under_a_minute():
    td = pd.Timedelta(seconds=58, milliseconds=5)
    assert format_timedelta(td) == "0:58.005"


def test_format_timedelta_handles_nat():
    assert format_timedelta(pd.NaT) == "N/A"


def test_format_timedelta_handles_none():
    assert format_timedelta(None) == "N/A"


# ==========================================================================
# format_speed
# ==========================================================================

def test_format_speed_normal_value():
    assert format_speed(312.456) == "312.5 km/h"


def test_format_speed_handles_nan():
    assert format_speed(float("nan")) == "N/A"


def test_format_speed_handles_none():
    assert format_speed(None) == "N/A"


# ==========================================================================
# compute_average_speed_from_telemetry
# ==========================================================================

def test_average_speed_constant_speed_matches_speed():
    """If speed never changes, the time-weighted average must equal it exactly."""
    telemetry = pd.DataFrame({
        "Time": [pd.Timedelta(seconds=s) for s in [0, 1, 2, 3]],
        "Speed": [200.0, 200.0, 200.0, 200.0],
    })
    assert compute_average_speed_from_telemetry(telemetry) == pytest.approx(200.0)


def test_average_speed_weights_by_time_not_sample_count():
    """A long, slow segment should pull the average down further than a
    naive (unweighted) mean would — this is exactly the bias a plain
    mean gets wrong, and the reason this function exists.
    """
    telemetry = pd.DataFrame({
        "Time": [pd.Timedelta(seconds=s) for s in [0, 1, 2, 12]],  # long final segment
        "Speed": [300.0, 300.0, 100.0, 100.0],
    })
    result = compute_average_speed_from_telemetry(telemetry)
    naive_mean = 200.0  # (300 + 300 + 100 + 100) / 4
    assert result < naive_mean


def test_average_speed_empty_telemetry_returns_nan():
    assert math.isnan(compute_average_speed_from_telemetry(pd.DataFrame()))


def test_average_speed_single_sample_returns_nan():
    telemetry = pd.DataFrame({"Time": [pd.Timedelta(seconds=0)], "Speed": [250.0]})
    assert math.isnan(compute_average_speed_from_telemetry(telemetry))


def test_average_speed_missing_columns_returns_nan():
    assert math.isnan(compute_average_speed_from_telemetry(pd.DataFrame({"Foo": [1, 2]})))


# ==========================================================================
# compute_delta_time
# ==========================================================================

def test_delta_time_identical_traces_is_zero():
    telemetry = pd.DataFrame({
        "Distance": [0, 100, 200, 300],
        "Time": [pd.Timedelta(seconds=s) for s in [0, 1, 2, 3]],
    })
    delta = compute_delta_time(telemetry, telemetry.copy())
    assert delta["Delta"].abs().max() == pytest.approx(0.0, abs=1e-9)


def test_delta_time_sign_matches_slower_driver():
    """Driver A takes longer to cover the same distance than Driver B,
    so the delta should be non-negative everywhere and strictly
    positive away from the shared starting point (where both are,
    correctly, tied at zero)."""
    tel_a = pd.DataFrame({
        "Distance": [0, 100, 200],
        "Time": [pd.Timedelta(seconds=s) for s in [0, 1.5, 3.0]],
    })
    tel_b = pd.DataFrame({
        "Distance": [0, 100, 200],
        "Time": [pd.Timedelta(seconds=s) for s in [0, 1.0, 2.0]],
    })
    delta = compute_delta_time(tel_a, tel_b)
    assert (delta["Delta"] >= 0).all()
    assert delta["Delta"].max() > 0
    assert delta.iloc[0]["Delta"] == pytest.approx(0.0, abs=1e-9)


def test_delta_time_empty_input_returns_empty_frame():
    assert compute_delta_time(pd.DataFrame(), pd.DataFrame()).empty


def test_delta_time_missing_columns_returns_empty_frame():
    a = pd.DataFrame({"Distance": [1, 2]})
    b = pd.DataFrame({"Distance": [1, 2]})
    assert compute_delta_time(a, b).empty


# ==========================================================================
# build_lap_summary
# ==========================================================================

def test_build_lap_summary_happy_path(fake_lap, telemetry_df):
    summary = build_lap_summary("VER", fake_lap, telemetry_df)
    assert summary is not None
    assert summary.driver == "VER"
    assert summary.compound == "SOFT"
    assert summary.lap_number == 15
    assert summary.lap_time == "1:32.190"
    assert summary.top_speed == telemetry_df["Speed"].max()


def test_build_lap_summary_none_lap_returns_none(telemetry_df):
    assert build_lap_summary("VER", None, telemetry_df) is None


def test_build_lap_summary_missing_lap_time_returns_none(telemetry_df):
    lap = FakeLap(lap_time_seconds=None)
    assert build_lap_summary("VER", lap, telemetry_df) is None


def test_build_lap_summary_nan_compound_shows_unknown(telemetry_df):
    """Regression test for a real bug: a Compound column holding NaN
    (rather than being absent) used to render the literal string "nan"
    in the UI instead of falling back to "Unknown".
    """
    lap = FakeLap(lap_time_seconds=90.0, compound=float("nan"))
    summary = build_lap_summary("HAM", lap, telemetry_df)
    assert summary.compound == "Unknown"


def test_build_lap_summary_empty_telemetry_still_returns_lap_time(fake_lap):
    """Missing telemetry shouldn't prevent showing the lap time itself —
    only the speed-derived stats should degrade to N/A-equivalent NaNs.
    """
    summary = build_lap_summary("VER", fake_lap, pd.DataFrame())
    assert summary is not None
    assert summary.lap_time == "1:32.190"
    assert math.isnan(summary.top_speed)
    assert math.isnan(summary.avg_speed)


# ==========================================================================
# _filter_valid_laps
# ==========================================================================

def test_filter_valid_laps_excludes_deleted():
    laps = pd.DataFrame({
        "Driver": ["VER", "VER"],
        "LapTime": [pd.Timedelta(seconds=90.0), pd.Timedelta(seconds=88.0)],
        "Deleted": [False, True],
    })
    filtered = _filter_valid_laps(laps)
    assert len(filtered) == 1
    assert filtered.iloc[0]["LapTime"] == pd.Timedelta(seconds=90.0)


def test_filter_valid_laps_excludes_inaccurate():
    laps = pd.DataFrame({
        "Driver": ["VER", "VER"],
        "LapTime": [pd.Timedelta(seconds=90.0), pd.Timedelta(seconds=87.0)],
        "IsAccurate": [True, False],
    })
    filtered = _filter_valid_laps(laps)
    assert len(filtered) == 1
    assert filtered.iloc[0]["LapTime"] == pd.Timedelta(seconds=90.0)


def test_filter_valid_laps_missing_columns_keeps_everything():
    laps = pd.DataFrame({
        "Driver": ["VER", "VER"],
        "LapTime": [pd.Timedelta(seconds=90.0), pd.Timedelta(seconds=88.0)],
    })
    assert len(_filter_valid_laps(laps)) == 2


def test_filter_valid_laps_falls_back_when_all_flagged():
    """If literally every lap is deleted (e.g. a fully red-flagged
    session), fall back to the unfiltered set rather than returning
    nothing — a degraded result is more useful than none at all.
    """
    laps = pd.DataFrame({
        "Driver": ["VER", "VER"],
        "LapTime": [pd.Timedelta(seconds=90.0), pd.Timedelta(seconds=88.0)],
        "Deleted": [True, True],
    })
    assert len(_filter_valid_laps(laps)) == 2


def test_filter_valid_laps_empty_input():
    laps = pd.DataFrame({"Driver": [], "LapTime": [], "Deleted": []})
    assert _filter_valid_laps(laps).empty


# ==========================================================================
# get_fastest_lap (integration-style, using FakeSession/FakeLaps)
# ==========================================================================

def test_get_fastest_lap_picks_the_quickest_non_deleted_lap(fake_session_factory):
    session = fake_session_factory(
        "VER", [91.0, 88.0, 89.5], Deleted=[False, True, False],
    )
    fastest = get_fastest_lap(session, "VER")
    assert fastest is not None
    assert fastest["LapTime"] == pd.Timedelta(seconds=89.5)


def test_get_fastest_lap_returns_none_for_unknown_driver(fake_session_factory):
    session = fake_session_factory("VER", [91.0])
    assert get_fastest_lap(session, "HAM") is None


def test_get_fastest_lap_returns_none_when_all_laps_are_nat(fake_session_factory):
    session = fake_session_factory("VER", [None, None])
    assert get_fastest_lap(session, "VER") is None
