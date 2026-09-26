"""
app.py
-------
Entry point for the F1 Telemetry Analytics Dashboard.

Run with:  streamlit run app.py

Layout:
  Sidebar  -> season / Grand Prix / session-type selection, load button
  Tab 1    -> Fastest Lap Analysis (single driver deep dive)
  Tab 2    -> Average Speed Analysis (all-driver leaderboard)
  Tab 3    -> Driver Comparison (head-to-head overlay + delta time)
  Tab 4    -> Lap Times Overview (race pace evolution)

This file is intentionally thin: it wires user selections to functions
in utils/data_loader.py, utils/analysis.py and utils/charts.py, and
handles rendering + error messaging. Almost no analysis logic lives
here — that separation is what keeps the business logic unit-testable
independently of Streamlit (see tests/test_analysis.py).
"""

from datetime import datetime

import streamlit as st

from config import APP_TITLE, APP_ICON, APP_SUBTITLE, DEFAULT_SEASON, SESSION_TYPES
from utils.data_loader import (
    setup_cache, get_available_seasons, get_event_names,
    load_session, get_driver_list, get_driver_full_name, DataLoadError,
)
from utils.analysis import (
    summarize_lap, get_lap_telemetry, get_fastest_lap,
    get_all_drivers_fastest_summary, compare_two_drivers,
    format_timedelta, format_speed,
)
from utils.charts import (
    plot_speed_trace, plot_throttle_brake, plot_gear_map,
    plot_avg_speed_bar, plot_top_speed_bar, plot_lap_time_ranking,
    plot_speed_comparison, plot_delta_time, plot_lap_times_over_race,
)
from utils.styling import inject_custom_css, render_footer
from utils.logger import get_logger

logger = get_logger(__name__)


# ==========================================================================
# Page setup
# ==========================================================================
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_custom_css()
setup_cache()

st.markdown(f"""
<div class="app-header">
    <h1>{APP_ICON} {APP_TITLE}</h1>
    <p>{APP_SUBTITLE}</p>
</div>
""", unsafe_allow_html=True)


# ==========================================================================
# Sidebar — season / Grand Prix / session-type selection
# ==========================================================================
with st.sidebar:
    st.markdown("### 🏁 Session Selection")

    current_year = datetime.now().year
    seasons = get_available_seasons(current_year)
    default_index = seasons.index(DEFAULT_SEASON) if DEFAULT_SEASON in seasons else 0
    season = st.selectbox("Season", seasons, index=default_index)

    # Fetching the calendar can fail (season not yet announced, a
    # transient network hiccup, etc.) — show a friendly message instead
    # of letting a raw exception crash the sidebar.
    try:
        event_names = get_event_names(season)
    except DataLoadError as exc:
        st.error(f"⚠️ {exc}")
        st.stop()
    except Exception as exc:
        logger.error("Unexpected error fetching schedule for %s: %s", season, exc)
        st.error("⚠️ Something went wrong fetching the race calendar. Please try again.")
        st.stop()

    if not event_names:
        st.warning(f"No events found for {season}.")
        st.stop()

    event = st.selectbox("Grand Prix", event_names)
    session_label = st.selectbox("Session Type", list(SESSION_TYPES.keys()), index=0)
    session_code = SESSION_TYPES[session_label]

    load_clicked = st.button("🔄 Load Session", use_container_width=True, type="primary")

    st.markdown("---")
    st.caption(
        "Data is provided by the FastF1 library, which pulls timing "
        "and telemetry from the official F1 live timing API. The first "
        "load of a session can take 20–60 seconds while it downloads "
        "and caches data locally; subsequent loads are near-instant."
    )

# ==========================================================================
# Session state management
# ==========================================================================
# The loaded FastF1 Session is kept in st.session_state so switching
# tabs (which reruns this whole script, as every Streamlit interaction
# does) doesn't re-download data every time.
#
# `requested_key` captures the user's CURRENT dropdown selections.
# Comparing it against the LAST LOADED key is what correctly detects
# "the user changed a dropdown but hasn't clicked Load Session yet".
# (A previous version of this app computed this key but never actually
# compared it against session_key, so changing a dropdown without
# clicking the button silently kept showing stale data — that bug is
# fixed by the `selection_changed` check below.)
if "session_key" not in st.session_state:
    st.session_state.session_key = None
    st.session_state.session_obj = None

requested_key = (season, event, session_code)
selection_changed = st.session_state.session_key not in (None, requested_key)

if selection_changed and not load_clicked:
    st.info(
        f"You've selected **{event} {season} — {session_label}**, but a different "
        "session is currently loaded below. Click **🔄 Load Session** in the "
        "sidebar to update the dashboard."
    )

if load_clicked or st.session_state.session_key is None:
    with st.spinner(f"Loading {event} {season} — {session_label}..."):
        try:
            st.session_state.session_obj = load_session(season, event, session_code)
            st.session_state.session_key = requested_key
        except DataLoadError as exc:
            st.error(f"⚠️ {exc}")
            st.stop()
        except Exception as exc:
            logger.error("Unexpected error loading session: %s", exc)
            st.error(
                "⚠️ An unexpected error occurred while loading this session. "
                "Please try a different season, event, or session type."
            )
            st.stop()

session = st.session_state.session_obj

if session is None:
    st.info("👈 Select a season, Grand Prix, and session, then click **Load Session** to begin.")
    render_footer()
    st.stop()

drivers = get_driver_list(session)
if not drivers:
    st.warning("No driver data found for this session.")
    render_footer()
    st.stop()

loaded_season, loaded_event, loaded_code = st.session_state.session_key
loaded_label = next((label for label, code in SESSION_TYPES.items() if code == loaded_code), loaded_code)
st.success(f"Loaded: **{loaded_event} {loaded_season} — {loaded_label}** ({len(drivers)} drivers)")


# ==========================================================================
# Tabs
# ==========================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "🏎️ Fastest Lap Analysis",
    "⚡ Average Speed Analysis",
    "🆚 Driver Comparison",
    "📈 Lap Times Overview",
])

# ---------------- Tab 1: Fastest Lap Analysis ----------------
with tab1:
    st.subheader("Fastest Lap Analysis")
    driver = st.selectbox(
        "Select Driver",
        drivers,
        format_func=lambda d: f"{d} — {get_driver_full_name(session, d)}",
        key="fastest_lap_driver",
    )

    try:
        summary = summarize_lap(session, driver)
    except Exception as exc:
        logger.error("Fastest lap analysis failed for %s: %s", driver, exc)
        st.error("⚠️ Couldn't analyze this driver's fastest lap. Try a different driver or session.")
        summary = None

    if summary is None:
        st.warning(f"No valid lap data available for {driver} in this session.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Fastest Lap", summary.lap_time)
        col2.metric("Top Speed", format_speed(summary.top_speed))
        col3.metric("Avg. Speed", format_speed(summary.avg_speed))
        col4.metric("Tire Compound", summary.compound)

        with st.spinner("Rendering telemetry..."):
            try:
                lap = get_fastest_lap(session, driver)
                telemetry = get_lap_telemetry(lap)
            except Exception as exc:
                logger.error("Telemetry fetch failed for %s: %s", driver, exc)
                st.error("⚠️ Couldn't load telemetry for this lap.")
                telemetry = None

        if telemetry is not None:
            st.plotly_chart(plot_speed_trace(telemetry, driver), use_container_width=True)

            col_a, col_b = st.columns(2)
            with col_a:
                st.plotly_chart(plot_throttle_brake(telemetry, driver), use_container_width=True)
            with col_b:
                st.plotly_chart(plot_gear_map(telemetry, driver), use_container_width=True)

# ---------------- Tab 2: Average Speed Analysis ----------------
with tab2:
    st.subheader("Average Speed Analysis — All Drivers")

    progress = st.progress(0, text="Starting analysis...")

    def _update_progress(i, total, code):
        progress.progress(i / total, text=f"Analyzing {code} ({i}/{total})...")

    try:
        summary_df = get_all_drivers_fastest_summary(session, drivers, progress_callback=_update_progress)
    except Exception as exc:
        logger.error("Leaderboard computation failed: %s", exc)
        st.error("⚠️ Couldn't build the driver leaderboard for this session.")
        summary_df = None
    finally:
        progress.empty()

    if summary_df is None:
        pass  # error already shown above
    elif summary_df.empty:
        st.warning("No lap data available to summarize for this session.")
    else:
        skipped = len(drivers) - len(summary_df)
        if skipped:
            st.caption(f"ℹ️ {skipped} driver(s) skipped — no valid timed lap available (e.g. did not set a time).")

        st.caption(
            "Note: these figures are computed from each driver's single "
            "fastest lap, not averaged across the full session."
        )

        st.plotly_chart(plot_avg_speed_bar(summary_df), use_container_width=True)
        col_a, col_b = st.columns(2)
        with col_a:
            st.plotly_chart(plot_top_speed_bar(summary_df), use_container_width=True)
        with col_b:
            st.plotly_chart(plot_lap_time_ranking(summary_df), use_container_width=True)

        st.markdown("#### Full Data Table")
        display_df = summary_df.rename(columns={
            "driver": "Driver", "lap_time": "Lap Time", "top_speed": "Top Speed (km/h)",
            "avg_speed": "Avg Speed (km/h)", "compound": "Compound", "lap_number": "Lap #",
        }).drop(columns=["lap_time_seconds"])
        st.dataframe(display_df, use_container_width=True, hide_index=True)

# ---------------- Tab 3: Driver Comparison ----------------
with tab3:
    st.subheader("Head-to-Head Driver Comparison")
    col1, col2 = st.columns(2)
    with col1:
        driver_a = st.selectbox(
            "Driver A", drivers,
            format_func=lambda d: f"{d} — {get_driver_full_name(session, d)}",
            key="compare_driver_a",
        )
    with col2:
        remaining = [d for d in drivers if d != driver_a] or drivers
        driver_b = st.selectbox(
            "Driver B", remaining,
            format_func=lambda d: f"{d} — {get_driver_full_name(session, d)}",
            key="compare_driver_b",
        )

    if driver_a == driver_b:
        st.warning("Pick two different drivers to compare.")
    else:
        with st.spinner(f"Comparing {driver_a} vs {driver_b}..."):
            try:
                lap_a, lap_b, tel_a, tel_b, delta_df = compare_two_drivers(session, driver_a, driver_b)
            except Exception as exc:
                logger.error("Driver comparison failed (%s vs %s): %s", driver_a, driver_b, exc)
                st.error("⚠️ Couldn't compare these drivers. Try a different pair or session.")
                lap_a = lap_b = None
                tel_a = tel_b = delta_df = None

        if lap_a is None or lap_b is None or tel_a is None or tel_a.empty or tel_b.empty:
            st.warning("Telemetry not available for one or both drivers in this session.")
        else:
            col1, col2 = st.columns(2)
            # Fixed: previously showed the raw pandas Timedelta repr
            # (e.g. "0 days 00:01:32.190000") instead of the clean
            # M:SS.mmm format used everywhere else in the app.
            col1.metric(f"{driver_a} Fastest Lap", format_timedelta(lap_a["LapTime"]))
            col2.metric(f"{driver_b} Fastest Lap", format_timedelta(lap_b["LapTime"]))

            st.plotly_chart(plot_speed_comparison(tel_a, tel_b, driver_a, driver_b), use_container_width=True)
            st.plotly_chart(plot_delta_time(delta_df, driver_a, driver_b), use_container_width=True)

# ---------------- Tab 4: Lap Times Overview ----------------
with tab4:
    st.subheader("Lap Time Evolution")
    driver_evo = st.selectbox(
        "Select Driver",
        drivers,
        format_func=lambda d: f"{d} — {get_driver_full_name(session, d)}",
        key="evo_driver",
    )
    try:
        fig = plot_lap_times_over_race(session.laps, driver_evo)
    except Exception as exc:
        logger.error("Lap evolution chart failed for %s: %s", driver_evo, exc)
        st.error("⚠️ Couldn't build the lap-time chart for this driver.")
    else:
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "Spikes usually indicate a pit stop, traffic, or a yellow flag / "
            "safety car period. A gentle upward drift across a stint often "
            "points to tire degradation."
        )

render_footer()
