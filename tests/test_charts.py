"""
tests/test_charts.py
----------------------
Light smoke tests for utils/charts.py — verifying each builder returns
a well-formed Plotly Figure with the expected trace count, and that
the "empty data" edge case degrades to a placeholder figure instead of
raising. These deliberately do NOT assert on exact colors, fonts, or
pixel layout, which would make the suite brittle against harmless
styling tweaks — the traces/structure are what matter functionally.
"""

import pandas as pd
import plotly.graph_objects as go

from utils.charts import (
    plot_speed_trace,
    plot_speed_comparison,
    plot_delta_time,
    plot_throttle_brake,
    plot_gear_map,
    plot_avg_speed_bar,
    plot_top_speed_bar,
    plot_lap_time_ranking,
)


def _telemetry():
    return pd.DataFrame({
        "Distance": [0, 100, 200],
        "Speed": [200, 250, 220],
        "Throttle": [100, 80, 100],
        "Brake": [False, True, False],
        "nGear": [6, 4, 6],
    })


def test_plot_speed_trace_returns_one_trace():
    fig = plot_speed_trace(_telemetry(), "VER")
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1


def test_plot_speed_trace_empty_data_does_not_raise():
    fig = plot_speed_trace(pd.DataFrame(), "VER")
    assert isinstance(fig, go.Figure)


def test_plot_speed_comparison_returns_two_traces():
    fig = plot_speed_comparison(_telemetry(), _telemetry(), "VER", "HAM")
    assert len(fig.data) == 2


def test_plot_speed_comparison_missing_data_does_not_raise():
    fig = plot_speed_comparison(pd.DataFrame(), _telemetry(), "VER", "HAM")
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 0  # placeholder figure, no traces


def test_plot_delta_time_includes_zero_reference_line():
    delta_df = pd.DataFrame({"Distance": [0, 100, 200], "Delta": [0.0, 0.2, -0.1]})
    fig = plot_delta_time(delta_df, "VER", "HAM")
    assert len(fig.layout.shapes) >= 1  # the dashed zero-reference line


def test_plot_throttle_brake_returns_two_traces():
    fig = plot_throttle_brake(_telemetry(), "VER")
    assert len(fig.data) == 2


def test_plot_gear_map_returns_one_trace():
    fig = plot_gear_map(_telemetry(), "VER")
    assert len(fig.data) == 1


def test_plot_avg_speed_bar_empty_data_does_not_raise():
    fig = plot_avg_speed_bar(pd.DataFrame())
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 0


def test_plot_top_speed_bar_returns_bar_trace():
    summary_df = pd.DataFrame({"driver": ["VER", "HAM"], "top_speed": [330.5, 325.1]})
    fig = plot_top_speed_bar(summary_df)
    assert len(fig.data) == 1


def test_plot_lap_time_ranking_orders_fastest_first():
    summary_df = pd.DataFrame({
        "driver": ["HAM", "VER"],
        "lap_time_seconds": [91.2, 89.5],
        "lap_time": ["1:31.200", "1:29.500"],
    })
    fig = plot_lap_time_ranking(summary_df)
    # Underlying trace data should be sorted ascending by lap_time_seconds
    assert list(fig.data[0].x) == [89.5, 91.2]
