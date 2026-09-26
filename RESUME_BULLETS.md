# Resume Bullet Points — F1 Telemetry Analytics Dashboard

Pick 2–4 that best match the role you're applying for. Swap in real
metrics (e.g. actual test count, actual coverage %) once you've run the
suite yourself.

## General Software Engineering Internship

- Built a full-stack F1 telemetry analytics dashboard in Python
  (Streamlit, Pandas, Plotly) that ingests real-time race data from a
  third-party API and renders interactive visualizations across 4
  analysis views.
- Designed a layered architecture (UI → business logic → external API)
  with a one-way dependency flow, enabling a 39-test automated suite to
  run against the business logic with zero network access or mocking
  of the UI framework.
- Wrote a defensive error-handling layer that normalizes a third-party
  library's varied exception types into a single custom exception,
  reducing UI-layer error handling to one consistent code path.
- Diagnosed and fixed a Streamlit state-management bug where dropdown
  changes silently failed to trigger a data reload, and a redundant
  API-call bug that doubled per-request data-fetch cost.
- Containerized the application with Docker (multi-layer caching,
  health checks) and configured CI-ready automated testing with pytest
  and fixture-based test doubles.

## Data / Analytics-Focused Roles

- Implemented a time-weighted average-speed algorithm using NumPy
  trapezoidal integration, correcting for sampling-density bias inherent
  in a naive mean of telemetry data.
- Built a distance-aligned time-delta computation (NumPy interpolation)
  to compare two drivers' lap telemetry — the same technique used in
  professional motorsport broadcast graphics.
- Applied domain-specific data-validity filtering (excluding
  deleted/track-limits and telemetry-inaccurate laps) before computing
  summary statistics, with a graceful fallback when filtering would
  otherwise remove all available data.

## Testing / Quality-Focused Roles

- Designed a test suite covering 39 unit and integration-style tests
  with zero network dependency, using lightweight hand-built test
  doubles (fake session/lap objects) that mirror the real third-party
  API's interface.
- Refactored a monolithic analysis function into pure, dependency-free
  functions plus thin orchestration wrappers specifically to make the
  business logic unit-testable in isolation from the UI framework and
  external API.

## One-liner (for a projects section / LinkedIn)

> F1 Telemetry Analytics Dashboard — Python/Streamlit/Plotly app for
> analyzing real Formula 1 lap and telemetry data via the FastF1 API,
> with a tested, layered architecture and Docker deployment.
> [github.com/yourusername/f1-telemetry-dashboard]
