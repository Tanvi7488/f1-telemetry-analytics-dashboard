# Project Status — F1 Telemetry Analytics Dashboard

*Last updated as part of a full production-readiness audit.*

This document is a snapshot of the project's current state, intended for
anyone reviewing the codebase quickly (a recruiter, an interviewer, or a
future contributor) without reading every file.

---

## Architecture Overview

The app follows a **layered architecture** with a strict one-way dependency
flow: `app.py` (UI) → `utils/analysis.py` (business logic) → `utils/data_loader.py`
(external API access). No layer reaches back "up" into the layer above it.

```
┌────────────────────────────────────────────────────────────────┐
│  app.py  (Streamlit UI)                                        │
│  - Sidebar: season / Grand Prix / session-type selection        │
│  - 4 tabs, each rendering charts + metrics                      │
│  - Owns st.session_state, error display, loading indicators     │
└───────────────────────────┬──────────────────────────────────┘
                             │ calls
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌───────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ data_loader.py │  │   analysis.py     │  │   charts.py       │
│ FastF1 session │  │  fastest laps,    │  │  Plotly figure    │
│ loading,       │  │  averages, deltas │  │  builders          │
│ schedules,     │  │  (pure funcs +    │  │  (defensive on     │
│ error wrapping │  │   FastF1 glue)     │  │   empty data)      │
└───────┬────────┘  └──────────────────┘  └──────────────────┘
        │
        ▼
┌────────────────┐   ┌─────────────┐   ┌──────────────┐
│  fastf1 (3rd    │   │  logger.py  │   │  styling.py  │
│  party library)│   │  centralized│   │  CSS + footer │
└────────────────┘   │  logging     │   └──────────────┘
                      └─────────────┘
```

**Key architectural decision — pure vs. orchestration functions.**
`utils/analysis.py` is split into:
- *Pure functions* with no FastF1/Streamlit/network dependency
  (`format_timedelta`, `format_speed`, `compute_average_speed_from_telemetry`,
  `compute_delta_time`, `build_lap_summary`, `_filter_valid_laps`) — these
  take plain pandas/NumPy input and are unit tested directly.
- *Orchestration functions* (`get_fastest_lap`, `summarize_lap`,
  `compare_two_drivers`, `get_all_drivers_fastest_summary`) that call FastF1
  and delegate computation to the pure functions above.

This split is why the test suite runs with **zero network access** — the
logic that's actually worth testing has no external dependency to mock.

**Error-handling strategy.** All FastF1-facing exceptions are normalized in
`data_loader.py` into a single `DataLoadError` with a human-readable message.
`app.py` therefore only needs one `except DataLoadError` clause per call site
to handle any FastF1 failure mode (network issue, missing session, malformed
data) consistently. Every exception is also logged via `utils/logger.py` so
the technical detail isn't lost, just hidden from the end user.

---

## Features Implemented

| Feature | Status | Notes |
|---|---|---|
| Driver selection | ✅ Complete | Dropdown shown with code + full name, used consistently across all 4 tabs |
| Race/session selection | ✅ Complete | Season → Grand Prix → Session Type (Race/Quali/Sprint/Practice) |
| Fastest lap analysis | ✅ Complete | Lap time, top speed, avg speed, compound, speed/throttle/brake/gear traces |
| Average speed analysis | ✅ Complete | Leaderboard across all drivers, with a progress bar during computation |
| Driver comparison | ✅ Complete | Speed overlay + distance-aligned time-delta trace |
| Lap time evolution | ✅ Complete | Per-driver pace trend across the full session |
| Interactive charts | ✅ Complete | All Plotly, zoom/hover/pan enabled by default |
| Modern UI | ✅ Complete | Dark F1-branded theme, card metrics, styled tabs, Google Font, footer |
| Error handling | ✅ Complete | Every FastF1 call site wrapped; friendly messages; no raw tracebacks shown to users |
| Loading indicators | ✅ Complete | Spinners on session load and telemetry fetch; live progress bar on the leaderboard |
| Automated tests | ✅ Complete | 30+ unit/smoke tests across `test_analysis.py` and `test_charts.py`, no network required |
| Deployment config | ✅ Complete | `Dockerfile` + `.dockerignore` (with healthcheck), Streamlit Cloud instructions, `.streamlit/config.toml` |

---

## Known Limitations

These are deliberate, documented scope boundaries — not oversights:

1. **"Average speed" is per fastest-lap, not session-wide.** Tab 2's average
   speed is computed on each driver's single fastest lap, not averaged
   across every lap of the race. A true session-wide figure would require a
   separate aggregation across all of a driver's laps.
2. **No Safety Car / VSC / Red Flag exclusion.** `_filter_valid_laps()`
   excludes laps FastF1 marks `Deleted` or not `IsAccurate`, but does not
   cross-reference track-status messages to exclude laps set under caution
   periods. Low practical impact (drivers rarely set their actual fastest
   lap under yellow), but not rigorously guaranteed.
3. **Single-session scope.** No comparison across two different races or
   seasons — each tab operates on one currently-loaded session.
4. **Styling relies partly on undocumented Streamlit internals.**
   `utils/styling.py` uses `data-testid` CSS selectors that are not part of
   Streamlit's public API and could break in a future Streamlit release.
   Base color theming is duplicated in `.streamlit/config.toml` (the
   supported theming API) as a more resilient fallback.
5. **No CI pipeline configured.** The test suite runs cleanly with `pytest`
   locally or in any CI system, but no `.github/workflows/` file ships yet.
6. **Screenshots section in README is a template.** It documents how to
   capture screenshots rather than shipping placeholder images — deliberate,
   to avoid faking visual "evidence" of a UI the reader hasn't seen run.
7. **pandas is pinned below 3.0.** During development, a pandas 3.x build
   available in the test environment was found to mis-parse certain
   `pd.to_timedelta(list, unit="s")` calls on whole-number float input. The
   app itself never constructs timedeltas this way (FastF1 supplies them
   directly), but the test fixtures originally did, and the pin is kept as a
   defensive measure until pandas 3.x compatibility is explicitly verified.

---

## Future Improvements

Roughly ordered by value-to-effort ratio for someone extending this project:

1. **Session-wide average speed metric** — compute average speed across all
   of a driver's laps, not just the fastest one, and show both figures.
2. **Track-status-aware lap filtering** — join `session.track_status`
   against each lap's time window to exclude Safety Car / VSC / Red Flag
   laps from "fastest lap" selection with full rigor.
3. **Track map visualization** — X/Y telemetry plotted as a track outline,
   color-coded by speed or gear.
4. **Tire strategy / pit-stop timeline view** — visualize each driver's
   stint lengths and compound choices across a race.
5. **Sector-by-sector comparison** — extend the delta-time concept to show
   which of the three sectors a time gain/loss came from, not just the
   full-lap trace.
6. **CI pipeline** — a GitHub Actions workflow running `pytest` on every
   push/PR.
7. **Export functionality** — download any chart as PNG or the summary
   table as CSV directly from the UI.
8. **Weather overlay** — correlate track/air temperature with lap time.
9. **Results/standings page** — surface `session.results` (finishing order,
   points, gaps) as a fifth tab.
