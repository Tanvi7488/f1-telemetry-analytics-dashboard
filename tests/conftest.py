"""
tests/conftest.py
------------------
Shared pytest fixtures.

Rather than hitting the real FastF1 API (which needs network access
and would make tests slow and non-deterministic), these fixtures build
small, realistic stand-ins for the pieces of the FastF1 object model
the app depends on. This lets utils/analysis.py be exercised in
complete isolation, deterministically, with zero network access.

Note on timedelta construction: telemetry/lap-time fixtures below build
Timedelta values one at a time with `pd.Timedelta(seconds=x)` rather
than `pd.to_timedelta([...], unit="s")`. During development, the list
form was found to mis-parse whole-number float seconds (e.g. 91.0) as
91 *nanoseconds* on some pandas versions — a real, reproducible
parsing quirk. Per-element construction sidesteps it entirely and is
the pattern used throughout this test suite.
"""

import pandas as pd
import pytest


def _seconds_to_timedelta_series(seconds_list):
    """Safely build a Series of Timedeltas from a list of second counts."""
    return pd.Series([pd.Timedelta(seconds=s) if s is not None else pd.NaT for s in seconds_list])


def make_telemetry(n=50, base_speed=250.0, distance_step=20.0, dt=0.2):
    """Build a synthetic, monotonically-increasing telemetry trace that
    looks enough like real FastF1 car data for the analysis functions
    under test (Time, Distance, Speed, Throttle, Brake, nGear).
    """
    time = _seconds_to_timedelta_series([i * dt for i in range(n)])
    distance = [i * distance_step for i in range(n)]
    speed = [base_speed + (i % 10) * 2 for i in range(n)]
    throttle = [100.0 if i % 3 else 40.0 for i in range(n)]
    brake = [False if i % 5 else True for i in range(n)]
    gear = [min(8, 3 + i // 8) for i in range(n)]
    return pd.DataFrame({
        "Time": time, "Distance": distance, "Speed": speed,
        "Throttle": throttle, "Brake": brake, "nGear": gear,
    })


class FakeLap(dict):
    """Minimal stand-in for a fastf1.core.Lap (itself a pandas Series).

    Supports the two access patterns analysis.py relies on —
    lap["LapTime"] / lap.get("Compound", default) — both of which
    `dict` already provides for free, with no need to mock the full
    FastF1 Lap class.
    """

    def __init__(self, lap_time_seconds=90.0, compound="MEDIUM", lap_number=1):
        super().__init__({
            "LapTime": pd.Timedelta(seconds=lap_time_seconds) if lap_time_seconds is not None else pd.NaT,
            "Compound": compound,
            "LapNumber": lap_number,
        })


class FakeLaps(pd.DataFrame):
    """A tiny pandas.DataFrame subclass implementing just enough of
    fastf1.core.Laps' API (pick_drivers / pick_driver / pick_fastest)
    to test utils.analysis's lap-selection logic without importing
    fastf1 or touching the network.
    """

    _metadata = []

    @property
    def _constructor(self):
        return FakeLaps

    def pick_drivers(self, driver_code):
        return self[self["Driver"] == driver_code]

    def pick_driver(self, driver_code):
        """FastF1 < 3.4 compatibility alias, mirroring the real API."""
        return self.pick_drivers(driver_code)

    def pick_fastest(self):
        valid = self.dropna(subset=["LapTime"])
        if valid.empty:
            return None
        return valid.loc[valid["LapTime"].idxmin()]


class FakeSession:
    """Minimal stand-in for a fastf1.core.Session — just the `.laps`
    attribute that get_fastest_lap() needs.
    """

    def __init__(self, laps_df: pd.DataFrame):
        self.laps = FakeLaps(laps_df)


@pytest.fixture
def telemetry_df():
    return make_telemetry()


@pytest.fixture
def fake_lap():
    return FakeLap(lap_time_seconds=92.190, compound="SOFT", lap_number=15)


@pytest.fixture
def fake_session_factory():
    """Returns a factory so each test can build a session with whatever
    lap rows (including LapTime in seconds, converted safely) it needs.
    """
    def _make(driver, lap_times_seconds, **extra_columns):
        data = {
            "Driver": [driver] * len(lap_times_seconds),
            "LapTime": _seconds_to_timedelta_series(lap_times_seconds),
        }
        data.update(extra_columns)
        return FakeSession(pd.DataFrame(data))
    return _make
