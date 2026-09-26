"""
utils/data_loader.py
---------------------
All interaction with the FastF1 library lives here: cache setup,
season/event/session discovery, and session loading.

Isolating FastF1 calls in one module means:
  - app.py stays focused on UI/UX
  - Streamlit caching decorators are applied in exactly one place
  - if FastF1's API changes, only this file needs updating

Error-handling strategy
------------------------
Every function that talks to FastF1 (network + parsing) is wrapped so
that failures raise a single, custom `DataLoadError` with a
human-readable message, rather than letting FastF1's assorted internal
exceptions bubble straight into the UI. app.py only needs to know about
one exception type to show a friendly error message for any of them.
The full technical exception is always logged (see utils/logger.py) so
it's still available for debugging.
"""

import os

import fastf1
import pandas as pd
import streamlit as st

from config import CACHE_DIR, MIN_SEASON
from utils.logger import get_logger

logger = get_logger(__name__)


class DataLoadError(Exception):
    """Raised when FastF1 data can't be fetched or parsed.

    Wrapping FastF1's various exception types (network errors, missing
    data, malformed responses) in one custom exception lets app.py
    show a single, consistent, user-friendly error path instead of
    special-casing every possible failure FastF1 might raise.
    """


def setup_cache() -> None:
    """Create (if needed) and enable the local FastF1 cache directory.

    FastF1 caches raw session data on disk so repeat requests for the
    same session don't re-download from the timing API. This should be
    called once, before any other fastf1 call, at app startup.
    """
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        fastf1.Cache.enable_cache(CACHE_DIR)
    except OSError as exc:
        # The cache is a performance optimization, not a hard
        # requirement — log it and let the app continue without a
        # local cache rather than crashing on startup over what's
        # likely a filesystem permissions issue on the host.
        logger.warning("Could not enable FastF1 cache at %s: %s", CACHE_DIR, exc)


@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
def get_available_seasons(current_year: int) -> list[int]:
    """Return a descending list of seasons FastF1 has usable data for."""
    return list(range(current_year, MIN_SEASON - 1, -1))


@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
def get_event_schedule(year: int) -> pd.DataFrame:
    """Fetch the full race calendar for a given season.

    Returns a DataFrame with one row per Grand Prix weekend, including
    event name, location, and round number.
    """
    try:
        schedule = fastf1.get_event_schedule(year, include_testing=False)
    except Exception as exc:
        logger.error("Failed to fetch event schedule for %s: %s", year, exc)
        raise DataLoadError(
            f"Couldn't fetch the {year} race calendar. This usually means "
            "either the season hasn't been announced yet or the F1 data "
            "source is temporarily unavailable."
        ) from exc

    if schedule is None or schedule.empty:
        raise DataLoadError(f"No events found for the {year} season.")
    return schedule


def get_event_names(year: int) -> list[str]:
    """Convenience helper: just the human-readable event names for a season."""
    schedule = get_event_schedule(year)
    return schedule["EventName"].dropna().tolist()


@st.cache_resource(show_spinner="Loading session data from FastF1 (first load can take a minute)...")
def load_session(year: int, event_name: str, session_code: str):
    """Load and return a fully-populated FastF1 Session object.

    st.cache_resource is used (rather than cache_data) because a
    FastF1 Session is a stateful, non-serializable object — exactly
    the kind of thing that cache_resource is designed for. If loading
    raises, Streamlit does NOT cache the failure, so the next attempt
    (e.g. after the user picks a different session) tries again fresh.

    Parameters
    ----------
    year : int            e.g. 2023
    event_name : str      e.g. "Monaco Grand Prix"
    session_code : str    e.g. "R", "Q", "FP1"
    """
    try:
        session = fastf1.get_session(year, event_name, session_code)
        session.load(telemetry=True, laps=True, weather=False, messages=False)
    except Exception as exc:
        logger.error("Failed to load session %s %s %s: %s", year, event_name, session_code, exc)
        raise DataLoadError(
            f"Couldn't load {event_name} ({year}) — {session_code}. This "
            "session may not have taken place yet, may not have telemetry "
            "data available, or the F1 timing API may be temporarily "
            "unreachable. Try a different season, event, or session type."
        ) from exc

    if session.laps is None or session.laps.empty:
        raise DataLoadError(
            f"{event_name} ({year}) — {session_code} loaded, but contains no "
            "lap data. It may have been cancelled or not yet have taken place."
        )
    return session


def get_driver_list(session) -> list[str]:
    """Return the three-letter driver codes (e.g. VER, HAM) present in a
    session, ordered by their final classified position where available.
    """
    try:
        results = session.results.sort_values("Position")
        codes = results["Abbreviation"].dropna().tolist()
        if codes:
            return codes
    except Exception as exc:
        logger.info("Falling back to lap-derived driver list: %s", exc)

    # Fallback: pull unique codes straight from the laps table. This
    # covers session types (e.g. some practice sessions) where FastF1
    # doesn't populate an official classification.
    try:
        return sorted(session.laps["Driver"].dropna().unique().tolist())
    except Exception as exc:
        logger.error("Could not determine driver list: %s", exc)
        return []


def get_driver_full_name(session, driver_code: str) -> str:
    """Map a driver code like 'VER' to a display name like 'Max Verstappen'.
    Falls back to the code itself if the lookup fails for any reason —
    this is cosmetic, so a failure here should never break the page.
    """
    try:
        info = session.get_driver(driver_code)
        first = info.get("FirstName", "")
        last = info.get("LastName", "")
        full = f"{first} {last}".strip()
        return full if full else driver_code
    except Exception:
        return driver_code
