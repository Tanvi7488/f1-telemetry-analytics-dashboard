# Interview Prep — F1 Telemetry Analytics Dashboard

20 questions an interviewer might ask about this specific project, with
answers grounded in actual decisions made while building it. Practice
saying these in your own words — don't memorize verbatim.

---

### 1. Walk me through the architecture of this project.

It's a layered architecture with a strict one-way dependency flow:
`app.py` (Streamlit UI) calls into `utils/analysis.py` (business logic),
which in turn calls `utils/data_loader.py` (the only file that talks to
FastF1). No layer reaches back up into the layer above it. That
one-way flow is what makes the business logic testable without spinning
up a UI or hitting the network — `analysis.py` and `charts.py` have no
Streamlit or FastF1 imports at all for their core functions.

### 2. Why did you split `analysis.py` into "pure" and "orchestration" functions?

Testability. Functions like `compute_delta_time` and
`build_lap_summary` take plain pandas DataFrames as input and return a
value — no FastF1 session, no network call. That means I can unit test
the actual business logic (the math, the formatting, the filtering
rules) with small synthetic fixtures. The orchestration functions
(`get_fastest_lap`, `summarize_lap`) are thin — they just fetch data
from FastF1 and hand it to the pure functions. This split is the reason
the test suite runs in under a second with zero network access.

### 3. How does your test suite avoid needing real FastF1 data or network access?

Two ways. First, most of the interesting logic lives in pure functions
that take plain DataFrames — no FastF1 object needed at all. Second,
for the parts that do need to interact with something FastF1-shaped
(like picking a driver's fastest lap), I built small test doubles in
`conftest.py` — a `FakeLaps` class that's a pandas DataFrame subclass
implementing just `pick_drivers()` and `pick_fastest()`, and a
`FakeSession` wrapping it. They implement only the exact interface my
code actually calls, not the full FastF1 API.

### 4. What was the hardest bug you found in this project, and how did you find it?

A Streamlit state-management bug: I computed a "requested session key"
from the current dropdown selections but never actually compared it
against the previously loaded session's key — I only checked whether
anything had been loaded at all. So changing the Grand Prix dropdown
without clicking "Load Session" silently kept showing stale data. I
found it by manually tracing the reload condition line by line during a
self-review, not by a test catching it — which is itself a lesson: I
added a `selection_changed` check afterward, and it's the kind of bug
that's easy to miss because it "works" as long as you always click the
button during testing.

### 5. You mention a "time-weighted average speed." What does that mean and why not just average the numbers?

Telemetry samples aren't evenly spaced by distance — a car generates
more data points per meter in a slow corner than on a straight, because
FastF1 samples by time, not distance. If you take a plain mean of the
Speed column, slow corners get over-represented relative to how long
the car actually spent there. Weighting each speed sample by the time
elapsed since the last one (a trapezoidal integration) gives a
physically correct average: total distance covered divided by total
time, decomposed sample-by-sample.

### 6. How do you handle errors from the FastF1 API?

Every FastF1-facing function in `data_loader.py` wraps its call in a
try/except and, on failure, raises one custom exception —
`DataLoadError` — with a human-readable message. The full technical
exception is still logged via a centralized logger, but the UI layer
only ever needs to catch one exception type to show a friendly message
for any of FastF1's many possible failure modes (network errors,
missing sessions, malformed data).

### 7. Why a custom exception instead of just catching `Exception` everywhere?

Catching bare `Exception` in the UI layer would also hide real bugs in
my own code — a typo, a `None` I forgot to check — behind the same
generic "something went wrong" message as a legitimate network failure.
By only catching `DataLoadError` at most call sites, an unexpected bug
in my own logic still surfaces (I do have a broader `except Exception`
fallback in `app.py`, but it logs the full exception and is a
deliberate last resort, not the primary error path).

### 8. What's `_filter_valid_laps` and why does it matter for an F1-specific project?

FastF1 flags laps as `Deleted` (race control deleted it, usually for a
track-limits violation) or not `IsAccurate` (FastF1's own telemetry
consistency check). Before picking a "fastest lap," I filter those out
— otherwise a deleted lap could be reported as a driver's official
fastest time, which would be factually wrong in F1 terms. If filtering
would remove every lap in a session (an edge case, but real — e.g. a
heavily red-flagged session), I fall back to the unfiltered set rather
than showing no data at all.

### 9. What are the known limitations of this project? Why didn't you fix them?

Two big ones: "average speed" is computed on each driver's single
fastest lap, not averaged across the whole session — the UI has a
caption clarifying this, but a true session-wide metric would need a
separate aggregation. And lap-validity filtering doesn't exclude laps
set under Safety Car or Virtual Safety Car conditions, because that
would require joining track-status messages against each lap's time
window — a meaningfully bigger feature. I documented both in
`PROJECT_STATUS.md` rather than either hiding them or scope-creeping
the project trying to fix everything at once.

### 10. How would you extend this to compare a driver's pace across two different races?

Right now everything operates on one loaded `Session` object at a time.
I'd add a second `st.session_state` slot for a "session B," extend the
comparison functions in `analysis.py` to accept two session objects
instead of one, and adjust the UI to let the user pick a season/event
for each side. The pure functions (`compute_delta_time`, etc.) wouldn't
need to change at all — they already just take telemetry DataFrames,
regardless of which session those came from.

### 11. Why Streamlit instead of Flask/Django + a JS frontend?

For a data-analysis tool like this, Streamlit lets me go from a pandas
DataFrame to an interactive, shareable web page without writing any
JavaScript or building a separate API layer — the whole UI is just
Python. That's the right tradeoff for a focused analytics dashboard.
It's not the right choice if I needed complex client-side interactivity,
multi-user real-time collaboration, or fine-grained control over the
DOM — for those, a proper frontend framework would be worth the extra
complexity.

### 12. How does Streamlit's caching work, and where did you use it?

`st.cache_data` caches a function's return value based on its
arguments, and is meant for serializable data — I use it for season
lists and race schedules. `st.cache_resource` is for objects that
shouldn't be re-created or serialized, like the FastF1 `Session` object
itself, which holds file handles and internal state. Using
`cache_data` on the raw Session would either fail or force an expensive
re-serialization on every access; `cache_resource` keeps one instance
alive across reruns.

### 13. Streamlit reruns the whole script on every interaction — how did that affect your design?

It means every `with tab:` block executes on every rerun regardless of
which tab is visually active, not just the one the user's looking at.
Early on, this meant selecting a different driver in one tab silently
triggered the expensive leaderboard computation in another tab, on
every interaction. I mitigated it by keeping the loaded session in
`st.session_state` so at least the expensive network calls only happen
once, and by giving the leaderboard tab a visible progress bar so the
cost, when it does happen, isn't presented as a silent freeze. A more
complete fix would restructure some of this around `st.fragment` for
partial reruns, which I've noted as a possible improvement.

### 14. Why did you cap pandas below version 3.0 in requirements.txt?

While building the test fixtures, I found that `pd.to_timedelta(list,
unit="s")` mis-parsed whole-number float values as nanoseconds instead
of seconds on a pandas 3.x build available in my dev environment — a
real, reproducible parsing quirk. My actual application code never
constructs timedeltas that way (FastF1 supplies them directly), but I
capped the dependency defensively since the project was built and
tested against pandas 2.x, and I hadn't verified compatibility with 3.x.

### 15. How did you verify your code works without being able to install the real dependencies at some point?

I statically parsed every file's imports with Python's `ast` module and
cross-checked them against `requirements.txt` and the local file
structure. For the test suite and the app itself, I built minimal
stand-ins for `plotly`, `streamlit`, and `fastf1` that implement only
the exact functions and methods my code actually calls, then ran the
real, unmodified source files against those stand-ins. That's not a
substitute for the real integration test, but it caught real issues —
like a `Compound` column holding NaN rather than being absent — that
plain syntax-checking wouldn't have caught.

### 16. What would you do differently if you started this project over?

I'd design the "pure function vs. orchestration function" split in
`analysis.py` from the start rather than refactoring into it partway
through. The original version fetched telemetry twice for the same lap
(once for top speed, once for average speed) and had a subtle NaN
formatting bug — both were direct consequences of not having that
separation early, since there was no natural seam to unit test against
until I created one.

### 17. How would you scale this if it needed to support many concurrent users?

FastF1's local disk cache is per-instance, so on something like
Streamlit Community Cloud with an ephemeral filesystem, every new
instance re-downloads data other instances already fetched. I'd move
the cache to a shared store (Redis or S3) keyed by session identifier,
so all instances benefit from one download. I'd also look at
`st.cache_resource`'s memory limits under concurrent sessions, since
each loaded FastF1 `Session` object holds a meaningful amount of
telemetry in memory.

### 18. Why FastF1 specifically, and what are its limitations?

FastF1 is the most complete open-source Python library for official F1
timing and telemetry data — it handles the parsing of F1's live-timing
feed format, which isn't otherwise documented. Its main limitation for
this project is that "official classification" data (`session.results`)
isn't always populated for practice sessions, so I added a fallback
that derives the driver list from the lap table instead when needed.

### 19. How would you add automated CI to this project?

A GitHub Actions workflow triggered on push/PR: check out the repo,
set up Python, `pip install -r requirements-dev.txt`, then run `pytest`.
Since the test suite has zero network dependency by design, it's
already CI-safe — the only work is writing the YAML. I'd also add a
linting step (`ruff` or `flake8`) and could add the `pytest-cov`
coverage report as a required check.

### 20. What's one thing you'd point to as evidence of good engineering practice in this project, beyond "it works"?

The error-handling boundary: every FastF1 failure mode gets normalized
into one exception type with a friendly message, logged in full detail
separately from what the user sees. That's a small decision, but it's
the difference between a demo that only handles the happy path and
something that behaves predictably when a session doesn't exist, the
network hiccups, or a lap has incomplete telemetry — which, working
with a real third-party data source, happens constantly in practice.
