Add dashboard screenshots to README
# 🏎️ F1 Telemetry Analytics Dashboard

An interactive Streamlit dashboard for exploring real Formula 1 telemetry —
fastest laps, speed traces, throttle/brake behavior, gear shifts, and
head-to-head driver comparisons.

## Dashboard Preview

### Main Dashboard
![Main Dashboard](screenshots/dashboard-home.png)

### Driver Comparison
![Driver Comparison](screenshots/driver-comparison.png)

### Lap Time Analysis
![Lap Time Analysis](screenshots/lap-times.png)

## Features

...
# 🏎️ F1 Telemetry Analytics Dashboard

An interactive Streamlit dashboard for exploring real Formula 1 telemetry —
fastest laps, speed traces, throttle/brake behavior, gear shifts, and
head-to-head driver comparisons — pulled from the official F1 timing API via
the [FastF1](https://docs.fastf1.dev/) library.

Built as a portfolio project to demonstrate: working with a real third-party
data API, clean multi-module Python architecture, defensive error handling,
a tested business-logic layer, data analysis with Pandas/NumPy, interactive
visualization with Plotly, and a polished Streamlit UI.

> 📌 See [`PROJECT_STATUS.md`](PROJECT_STATUS.md) for the current architecture
> summary, implemented features, known limitations, and planned improvements —
> useful if you're reviewing this repo for a class, portfolio, or interview.
>
> Also included: [`ARCHITECTURE.md`](ARCHITECTURE.md) (diagram + data flow),
> [`RESUME_BULLETS.md`](RESUME_BULLETS.md), and [`INTERVIEW_QA.md`](INTERVIEW_QA.md)
> (20 project-specific interview Q&As) — written for anyone using this repo
> as part of an internship application.

---

## Table of Contents

1. [Screenshots](#screenshots)
2. [Features](#features)
3. [Tech Stack](#tech-stack)
4. [Architecture Overview](#architecture-overview)
5. [Folder Structure](#folder-structure)
6. [File-by-File Explanation](#file-by-file-explanation)
7. [Installation](#installation)
8. [Running the App](#running-the-app)
9. [Running the Tests](#running-the-tests)
10. [Deployment](#deployment)
11. [Known Limitations](#known-limitations)
12. [Troubleshooting](#troubleshooting)
13. [License](#license)

---

## Screenshots

*Add screenshots here after running the app locally* — a quick way to
capture good ones:

1. Run `streamlit run app.py`, load a race (e.g. 2023 Monaco GP → Race).
2. Screenshot each tab: Fastest Lap Analysis, Average Speed Analysis, Driver
   Comparison, and Lap Times Overview.
3. Save them into a `screenshots/` folder at the project root and reference
   them here, e.g.:

   ```markdown
   ![Fastest Lap Analysis](screenshots/fastest-lap.png)
   ![Driver Comparison](screenshots/driver-comparison.png)
   ```

This section is intentionally left as a template — screenshots are most
convincing when they show *your own* run of the app, not a placeholder image.

---

## Features

| # | Feature | Where |
|---|---------|-------|
| 1 | **Driver selection** — pick any driver from the loaded session, shown with full name | Sidebar-driven, used in every tab |
| 2 | **Race selection** — choose season, Grand Prix, and session type (Race, Qualifying, Sprint, Practice) | Sidebar |
| 3 | **Fastest lap analysis** — lap time, top speed, average speed, tire compound, speed/throttle/brake/gear traces | Tab 1 |
| 4 | **Average speed analysis** — ranks every driver by average speed, top speed, and lap time (on their fastest lap) | Tab 2 |
| 5 | **Driver comparison** — overlays two drivers' speed traces and computes a distance-aligned time delta | Tab 3 |
| 6 | **Lap time evolution** — race-pace trend per driver across the full session, useful for spotting pit stops and tire wear | Tab 4 |
| 7 | **Interactive charts** — zoomable, hoverable Plotly charts throughout | All tabs |
| 8 | **Modern UI** — dark, F1-branded theme, card-style metrics, styled tabs, progress bars, and friendly error states | Whole app |
| 9 | **Robust error handling** — friendly messages instead of raw tracebacks anywhere FastF1 data can be missing, incomplete, or unreachable | Whole app |
| 10 | **Automated test suite** — unit + smoke tests for the analysis and charting logic, runnable with no network access | `tests/` |

---

## Tech Stack

- **Python 3.9+**
- **Streamlit** — web UI framework
- **Pandas / NumPy** — data wrangling and numeric analysis
- **Plotly** — interactive charting
- **FastF1** — official F1 timing/telemetry data access + local caching
- **pytest** — automated testing (dev dependency only)

---

## Architecture Overview

```
┌─────────────┐     picks season/GP/session      ┌───────────────────┐
│   Sidebar   │ ───────────────────────────────► │  data_loader.py   │
│  (app.py)   │                                    │  (FastF1 calls,   │
└─────────────┘                                    │   caching, errors) │
       │                                            └─────────┬─────────┘
       │ session object                                       │
       ▼                                                       ▼
┌─────────────┐     fastest laps, deltas,      ┌───────────────────┐
│  Tabs 1–4   │ ◄────────────────────────────  │   analysis.py      │
│  (app.py)   │     average speed, summaries   │  (pure logic +     │
└──────┬──────┘                                 │   FastF1 glue)      │
       │ figures                                └────────────────────┘
       ▼
┌─────────────┐
│  charts.py  │  (Plotly figure builders, defensive on empty data)
└─────────────┘
```

**Design principles applied:**

- **Separation of concerns.** `app.py` only wires UI selections to function
  calls and renders results — it contains almost no analysis logic itself.
- **Testability by construction.** `analysis.py` splits pure computation
  (no FastF1/network dependency — e.g. `compute_delta_time`,
  `build_lap_summary`) from thin orchestration functions that call FastF1.
  The pure functions are unit tested directly; the orchestration functions
  are tested with lightweight fake session/lap objects (see
  `tests/conftest.py`) rather than a live network call.
- **One error type at the UI boundary.** Every FastF1-facing function in
  `data_loader.py` translates FastF1's various possible exceptions into a
  single `DataLoadError` with a human-readable message, so `app.py` only
  needs one `except` clause to handle any of them gracefully.
- **Graceful degradation over hard failure.** Charts render a "no data
  available" placeholder instead of crashing on missing telemetry; the
  leaderboard skips drivers with no valid lap instead of failing the whole
  tab; lap-validity filtering falls back to the unfiltered set rather than
  returning nothing if every lap happens to be flagged.

---

## Folder Structure

```
f1-telemetry-dashboard/
├── app.py                    # Streamlit entry point — UI layout & wiring
├── config.py                 # App-wide constants (colors, defaults, session types)
├── requirements.txt          # Production Python dependencies
├── requirements-dev.txt      # + testing dependencies (pytest)
├── pytest.ini                # Pytest configuration (import path setup)
├── README.md                 # This file
├── PROJECT_STATUS.md         # Architecture/feature/limitation snapshot
├── LICENSE                   # MIT License
├── Dockerfile                # Production container image
├── .dockerignore             # Files excluded from the Docker build context
├── .gitignore                # Files excluded from version control
├── .streamlit/
│   └── config.toml            # Native Streamlit theme configuration
├── cache/                     # FastF1's local data cache (auto-populated)
│   └── .gitkeep
├── utils/                     # Non-UI application logic
│   ├── __init__.py
│   ├── data_loader.py          # FastF1 session/schedule loading + error handling
│   ├── analysis.py             # Fastest lap, average speed, comparison logic
│   ├── charts.py                # Plotly figure builders
│   ├── styling.py               # Custom CSS + footer component
│   └── logger.py                 # Centralized logging setup
└── tests/                      # Automated test suite (pytest)
    ├── __init__.py
    ├── conftest.py              # Shared fixtures + FastF1 test doubles
    ├── test_analysis.py         # Unit tests for utils/analysis.py
    └── test_charts.py            # Smoke tests for utils/charts.py
```

---

## File-by-File Explanation

### `app.py`
The Streamlit entry point and the only file that touches the UI layout. It
configures the page, injects styling, renders the sidebar (season → Grand
Prix → session type → Load Session), loads the FastF1 session (caching it in
`st.session_state`), and renders four tabs that call into `utils/analysis.py`
for numbers and `utils/charts.py` for figures. Every FastF1-facing call is
wrapped so a failure shows a short, friendly `st.error()` message instead of
crashing the page.

### `config.py`
A single source of truth for constants: file paths, app title/subtitle, the
earliest supported season, the mapping of human-readable session names
(`"Race"`) to FastF1's internal codes (`"R"`), and the color palette shared
by the CSS and the Plotly charts.

### `utils/data_loader.py`
The **only** file that calls FastF1 directly. Wraps every FastF1 call (event
schedule, session load, driver lookup) with error handling that raises a
single custom `DataLoadError` with a human-readable message on failure, and
logs the full technical exception via `utils/logger.py`. Also handles
Streamlit's two caching layers: `@st.cache_data` for serializable data
(schedules, season lists) and `@st.cache_resource` for the stateful FastF1
`Session` object.

### `utils/analysis.py`
Pure data-analysis functions, deliberately split into two layers:
- **Pure functions** (no FastF1/Streamlit imports) — `format_timedelta`,
  `format_speed`, `compute_average_speed_from_telemetry`,
  `compute_delta_time`, `build_lap_summary`, `_filter_valid_laps`. These take
  plain pandas/NumPy data and are fully unit tested with synthetic fixtures.
- **Orchestration functions** — `get_fastest_lap`, `summarize_lap`,
  `compare_two_drivers`, `get_all_drivers_fastest_summary` — glue the pure
  functions to the real FastF1 API, with `try/except` around every FastF1
  call so one driver's bad data can't take down the whole page.

Notable logic: `_filter_valid_laps()` excludes laps FastF1 flags as
`Deleted` (track-limits infringement) or not `IsAccurate`, before picking a
"fastest lap" — with a safe fallback to the unfiltered set if every lap in a
session happens to be flagged. `compute_average_speed_from_telemetry()` uses
a **time-weighted** average (not a naive mean), which avoids over-weighting
slow corners where telemetry samples are denser.

### `utils/charts.py`
Every chart is a `plotly.graph_objects.Figure` returned to `app.py` for
`st.plotly_chart()`. Every builder checks for empty/missing data first and
renders a styled "no data available" placeholder instead of raising — a
driver having a fastest lap on record but incomplete telemetry (e.g. a lap
logged right at a session-ending red flag) is a real scenario this handles
gracefully rather than crashing the tab.

### `utils/styling.py`
Injects custom CSS for the F1-branded dark theme (gradient header, card-style
metrics with hover states, styled tabs, a Google Font) and exposes
`render_footer()`, a small reusable footer shown on every page state. Base
color theming is *also* declared in `.streamlit/config.toml` — Streamlit's
actual public theming API — since the CSS selectors used here
(`data-testid="stMetric"`, etc.) are undocumented internals that could change
in a future Streamlit release.

### `utils/logger.py`
A minimal, centralized `logging` setup. The app never shows a raw traceback
to the user; instead, every module logs full technical detail here (visible
in your terminal or hosting platform's logs) while the UI shows a short,
friendly message.

### `tests/`
- `conftest.py` — shared fixtures and lightweight FastF1 test doubles
  (`FakeLap`, `FakeLaps`, `FakeSession`) that implement just enough of the
  real FastF1 API surface to test lap-selection logic with zero network
  access.
- `test_analysis.py` — unit tests for every pure function in `analysis.py`,
  plus integration-style tests for `get_fastest_lap()`'s deleted/inaccurate
  lap filtering using the fake session objects.
- `test_charts.py` — smoke tests confirming each chart builder returns the
  expected trace structure and handles empty data without raising.

### `requirements.txt` / `requirements-dev.txt`
Pinned dependency ranges for running the app, and (in `-dev`) for running the
test suite. `pandas` is capped below 3.0 — see the comment in the file for
why.

### `Dockerfile` / `.dockerignore`
A production container image with a `HEALTHCHECK`, layered so dependency
installation is cached separately from app code changes.

### `.streamlit/config.toml`
Native Streamlit theme (colors, dark mode) — the officially supported way to
theme a Streamlit app, used alongside the custom CSS in `styling.py`.

### `cache/`
Where FastF1 stores downloaded session data so it doesn't re-fetch from the
timing API on every run. Empty on a fresh clone (only `.gitkeep` is
committed) and populates automatically on first use.

---

## Installation

### Prerequisites
- Python 3.9 or newer
- pip
- An internet connection (FastF1 downloads data from the F1 timing API the
  first time each session is requested)

### Steps

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd f1-telemetry-dashboard

# 2. Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Running the App

```bash
streamlit run app.py
```

Streamlit prints a local URL (typically `http://localhost:8501`) — open it in
your browser. In the sidebar: pick a **Season**, **Grand Prix**, and
**Session Type**, then click **🔄 Load Session** and wait for the first-time
download (usually 20–60 seconds; instant on repeat loads thanks to the
cache). Then explore the four tabs.

---

## Running the Tests

```bash
pip install -r requirements-dev.txt
pytest
```

For a coverage report:

```bash
pytest --cov=utils --cov-report=term-missing
```

The test suite requires **no network access and no FastF1 data download** —
every test runs against small, synthetic fixtures (see `tests/conftest.py`),
so it's safe to run in CI.

---

## Deployment

### Option A: Streamlit Community Cloud (free, easiest)

1. Push this project to a GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with
   GitHub, click **New app**, select your repo/branch, and set the main file
   path to `app.py`.
3. Click **Deploy** — Streamlit Cloud installs `requirements.txt`
   automatically.
4. **Note on caching:** Streamlit Cloud's filesystem is ephemeral, so the
   FastF1 cache won't persist between deploys/restarts. This only affects
   speed, not correctness — FastF1 simply re-downloads on first use after a
   restart.

### Option B: Docker

```bash
docker build -t f1-dashboard .
docker run -p 8501:8501 f1-dashboard
```

The included `Dockerfile` installs dependencies in their own cached layer, so
rebuilding after an app-code-only change is fast. The container reports
healthy once Streamlit's `/_stcore/health` endpoint responds.

### Option C: A general-purpose host (Render, Railway, Fly.io, EC2, etc.)

Install dependencies from `requirements.txt`, then start with:

```bash
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

(replace `$PORT` with the port variable your host provides).

---

## Known Limitations

Documented here deliberately, rather than glossed over — being explicit
about scope is part of writing production-honest software:

- **"Average speed" is per fastest-lap, not per-session.** Tab 2 reports
  average speed on each driver's single fastest lap, not averaged across
  every lap of the race. A caption in the UI clarifies this; a true
  session-wide average would need a separate calculation across all laps.
- **Safety Car / VSC / Red Flag periods are not excluded from "fastest lap"
  selection.** `_filter_valid_laps()` excludes laps FastF1 flags as
  `Deleted` or not `IsAccurate`, but doesn't cross-reference track-status
  messages to exclude a lap set under caution. In practice this is rare for
  an actual *fastest* lap (drivers don't push under yellow), but it's a real
  gap for a fully rigorous analysis.
- **No session-to-session comparison.** Each tab operates on one loaded
  session at a time; comparing a driver's pace across two different races
  isn't supported.
- **Streamlit's undocumented CSS hooks.** Some visual polish in
  `styling.py` relies on Streamlit internals (`data-testid` attributes) that
  aren't part of Streamlit's public API and could change in a future release.
  Base color theming is duplicated in `.streamlit/config.toml` as a more
  resilient fallback.
- **No CI pipeline configured.** Tests are runnable locally/in any CI system
  via `pytest`, but no `.github/workflows/` file is included yet.

## Future Improvements

See [`PROJECT_STATUS.md`](PROJECT_STATUS.md) for the full list.

---

## Troubleshooting

- **"Couldn't load this session"** — Some sessions (very old ones, cancelled
  events) have incomplete data. Try a different session type or season.
- **First load is slow** — Expected; FastF1 is downloading and caching real
  telemetry. Repeat loads of the same session are fast.
- **`ModuleNotFoundError: No module named 'fastf1'`** — Activate your virtual
  environment and re-run `pip install -r requirements.txt`.
- **Empty driver list** — Early-weekend practice sessions occasionally have
  sparse data; try Qualifying or Race instead.
- **Tests fail with an import error** — Make sure you're running `pytest`
  from the project root (where `pytest.ini` lives), and that you installed
  `requirements-dev.txt`, not just `requirements.txt`.

---

## License

MIT — see [`LICENSE`](LICENSE).
