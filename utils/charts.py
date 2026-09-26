"""
utils/charts.py
-----------------
Plotly figure builders. Every function here returns a go.Figure so
app.py can simply call st.plotly_chart(...) on the result.

Keeping chart construction separate from data analysis (analysis.py)
and layout (app.py) follows a clean separation of concerns — each
file has exactly one reason to change.

Every builder below defensively checks for empty/missing data and
returns a styled "no data available" placeholder figure instead of
letting Plotly raise on an empty DataFrame or a missing column. This
matters in practice: a driver can have a fastest lap on record but
incomplete telemetry (e.g. a lap logged right at a session-ending
red flag), and the dashboard should degrade gracefully rather than
crash the whole page over one driver's gap in data.
"""

import pandas as pd
import plotly.graph_objects as go

from config import PLOTLY_TEMPLATE, DRIVER_COLOR_1, DRIVER_COLOR_2, COLOR_SURFACE, COLOR_TEXT, COLOR_MUTED


def _base_layout(fig: go.Figure, title: str, x_title: str, y_title: str) -> go.Figure:
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title=title,
        xaxis_title=x_title,
        yaxis_title=y_title,
        plot_bgcolor=COLOR_SURFACE,
        paper_bgcolor=COLOR_SURFACE,
        font=dict(color=COLOR_TEXT),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=20, t=60, b=40),
        hovermode="x unified",
    )
    return fig


def _empty_figure(title: str) -> go.Figure:
    """A styled placeholder chart for when there's genuinely no data to
    plot. Showing this instead of letting Plotly error out on an empty
    DataFrame keeps the dashboard usable even when one driver's data
    is incomplete.
    """
    fig = go.Figure()
    fig.add_annotation(
        text="No telemetry data available for this selection",
        showarrow=False, font=dict(size=14, color=COLOR_MUTED),
        xref="paper", yref="paper", x=0.5, y=0.5,
    )
    return _base_layout(fig, title, "", "")


def plot_speed_trace(telemetry: pd.DataFrame, driver_code: str, color: str = DRIVER_COLOR_1) -> go.Figure:
    """Speed (km/h) vs. distance for a single driver's fastest lap."""
    title = f"Speed Trace — {driver_code}"
    if telemetry.empty or "Distance" not in telemetry or "Speed" not in telemetry:
        return _empty_figure(title)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=telemetry["Distance"], y=telemetry["Speed"],
        mode="lines", name=driver_code, line=dict(color=color, width=2.5),
    ))
    return _base_layout(fig, title, "Distance (m)", "Speed (km/h)")


def plot_speed_comparison(tel_a: pd.DataFrame, tel_b: pd.DataFrame, driver_a: str, driver_b: str) -> go.Figure:
    """Overlay two drivers' speed traces on the same distance axis."""
    title = f"Speed Comparison — {driver_a} vs {driver_b}"
    if tel_a.empty or tel_b.empty or "Distance" not in tel_a or "Distance" not in tel_b:
        return _empty_figure(title)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=tel_a["Distance"], y=tel_a["Speed"], mode="lines",
        name=driver_a, line=dict(color=DRIVER_COLOR_1, width=2.5),
    ))
    fig.add_trace(go.Scatter(
        x=tel_b["Distance"], y=tel_b["Speed"], mode="lines",
        name=driver_b, line=dict(color=DRIVER_COLOR_2, width=2.5),
    ))
    return _base_layout(fig, title, "Distance (m)", "Speed (km/h)")


def plot_delta_time(delta_df: pd.DataFrame, driver_a: str, driver_b: str) -> go.Figure:
    """Plot the cumulative time delta between two drivers across the lap.

    Area above zero = driver A losing time relative to driver B at that
    point on track, and vice versa below zero.
    """
    title = f"Time Delta — {driver_a} vs {driver_b}"
    if delta_df.empty or "Distance" not in delta_df or "Delta" not in delta_df:
        return _empty_figure(title)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=delta_df["Distance"], y=delta_df["Delta"],
        mode="lines", name=f"{driver_a} vs {driver_b}",
        line=dict(color="#FFD700", width=2),
        fill="tozeroy",
    ))
    fig.add_hline(y=0, line_dash="dash", line_color=COLOR_TEXT, opacity=0.4)
    return _base_layout(
        fig,
        f"Time Delta — positive = {driver_a} slower than {driver_b}",
        "Distance (m)", "Delta (s)"
    )


def plot_throttle_brake(telemetry: pd.DataFrame, driver_code: str) -> go.Figure:
    """Throttle % and brake status stacked over distance."""
    title = f"Throttle & Brake — {driver_code}"
    if telemetry.empty or "Throttle" not in telemetry or "Brake" not in telemetry:
        return _empty_figure(title)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=telemetry["Distance"], y=telemetry["Throttle"],
        mode="lines", name="Throttle (%)", line=dict(color="#2ECC71", width=2),
    ))
    fig.add_trace(go.Scatter(
        x=telemetry["Distance"], y=telemetry["Brake"].astype(int) * 100,
        mode="lines", name="Brake", line=dict(color="#E10600", width=2, dash="dot"),
        fill="tozeroy", opacity=0.3,
    ))
    return _base_layout(fig, title, "Distance (m)", "%")


def plot_gear_map(telemetry: pd.DataFrame, driver_code: str) -> go.Figure:
    """Gear number vs. distance — shows shift points around the lap."""
    title = f"Gear Map — {driver_code}"
    if telemetry.empty or "nGear" not in telemetry:
        return _empty_figure(title)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=telemetry["Distance"], y=telemetry["nGear"],
        mode="lines", name="Gear", line=dict(color="#9B59B6", width=2, shape="hv"),
    ))
    fig.update_yaxes(dtick=1)
    return _base_layout(fig, title, "Distance (m)", "Gear")


def plot_avg_speed_bar(summary_df: pd.DataFrame) -> go.Figure:
    """Bar chart ranking drivers by average speed on their fastest lap."""
    title = "Average Speed by Driver (Fastest Lap)"
    if summary_df.empty:
        return _empty_figure(title)
    fig = go.Figure(go.Bar(
        x=summary_df["driver"], y=summary_df["avg_speed"],
        marker_color=DRIVER_COLOR_1,
        text=summary_df["avg_speed"].round(1),
        textposition="outside",
    ))
    return _base_layout(fig, title, "Driver", "Avg. Speed (km/h)")


def plot_top_speed_bar(summary_df: pd.DataFrame) -> go.Figure:
    """Bar chart ranking drivers by top speed reached on their fastest lap."""
    title = "Top Speed by Driver (Fastest Lap)"
    if summary_df.empty:
        return _empty_figure(title)
    fig = go.Figure(go.Bar(
        x=summary_df["driver"], y=summary_df["top_speed"],
        marker_color=DRIVER_COLOR_2,
        text=summary_df["top_speed"].round(1),
        textposition="outside",
    ))
    return _base_layout(fig, title, "Driver", "Top Speed (km/h)")


def plot_lap_time_ranking(summary_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart of fastest lap times, quickest at the top."""
    title = "Fastest Lap Ranking"
    if summary_df.empty:
        return _empty_figure(title)
    df = summary_df.sort_values("lap_time_seconds", ascending=True)
    fig = go.Figure(go.Bar(
        x=df["lap_time_seconds"], y=df["driver"],
        orientation="h",
        marker_color=DRIVER_COLOR_1,
        text=df["lap_time"],
        textposition="outside",
    ))
    fig.update_yaxes(autorange="reversed")
    return _base_layout(fig, title, "Lap Time (s)", "Driver")


def plot_lap_times_over_race(laps: pd.DataFrame, driver_code: str) -> go.Figure:
    """Line chart of lap time evolution across a race/session for one driver.
    Useful for spotting pit stops, tire degradation, and pace drop-off.
    """
    title = f"Lap Time Evolution — {driver_code}"
    try:
        driver_laps = laps.pick_drivers(driver_code) if hasattr(laps, "pick_drivers") else laps.pick_driver(driver_code)
    except Exception:
        return _empty_figure(title)

    if "LapTime" not in driver_laps.columns:
        return _empty_figure(title)
    driver_laps = driver_laps.dropna(subset=["LapTime"])
    if driver_laps.empty:
        return _empty_figure(title)

    seconds = driver_laps["LapTime"].dt.total_seconds()
    fig = go.Figure(go.Scatter(
        x=driver_laps["LapNumber"], y=seconds,
        mode="lines+markers", name=driver_code,
        line=dict(color=DRIVER_COLOR_1, width=2),
        marker=dict(size=6),
    ))
    return _base_layout(fig, title, "Lap Number", "Lap Time (s)")
