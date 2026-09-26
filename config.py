"""
config.py
---------
Central configuration for the F1 Telemetry Analytics Dashboard.

Keeping all constants in one place makes the app easy to re-theme,
re-brand, or point at a different cache location without hunting
through business logic scattered across files.
"""

import os

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")

# --------------------------------------------------------------------------
# App metadata
# --------------------------------------------------------------------------
APP_TITLE = "F1 Telemetry Analytics Dashboard"
APP_ICON = "🏎️"
APP_SUBTITLE = "Fastest laps, speed traces & head-to-head driver comparison, powered by FastF1"

# --------------------------------------------------------------------------
# Data defaults
# --------------------------------------------------------------------------
MIN_SEASON = 2018          # FastF1 telemetry is reliable from ~2018 onward
DEFAULT_SEASON = 2023      # A safe, data-complete default season

SESSION_TYPES = {
    "Race": "R",
    "Qualifying": "Q",
    "Sprint": "S",
    "Sprint Qualifying": "SQ",
    "Practice 1": "FP1",
    "Practice 2": "FP2",
    "Practice 3": "FP3",
}

# --------------------------------------------------------------------------
# Theme / colors (used by both custom CSS and Plotly charts)
# --------------------------------------------------------------------------
COLOR_BACKGROUND = "#0E1117"
COLOR_SURFACE = "#161B22"
COLOR_PRIMARY = "#E10600"     # F1 red
COLOR_SECONDARY = "#00D2BE"   # Teal accent
COLOR_TEXT = "#F5F5F5"
COLOR_MUTED = "#8B949E"

DRIVER_COLOR_1 = "#E10600"
DRIVER_COLOR_2 = "#1E90FF"

PLOTLY_TEMPLATE = "plotly_dark"
