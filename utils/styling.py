"""
utils/styling.py
------------------
Custom CSS injected into the Streamlit app for a modern, F1-branded
look, plus a small reusable footer component.

A note on relying on custom CSS: Streamlit doesn't expose most of its
internal DOM structure as a stable public API, so selectors like
`div[data-testid="stMetric"]` below are technically undocumented
implementation details that *could* change in a future Streamlit
release. To reduce that risk, base color theming is also declared in
.streamlit/config.toml (Streamlit's actual public theming API), and
this file is limited to visual polish that config.toml can't express
(gradients, card borders, tab styling, the footer).
"""

import streamlit as st

from config import (
    COLOR_BACKGROUND, COLOR_SURFACE, COLOR_PRIMARY, COLOR_SECONDARY,
    COLOR_TEXT, COLOR_MUTED,
)


def inject_custom_css() -> None:
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Titillium+Web:wght@400;600;700;900&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Titillium Web', 'Segoe UI', sans-serif;
        }}

        .stApp {{
            background-color: {COLOR_BACKGROUND};
            color: {COLOR_TEXT};
        }}

        .app-header {{
            padding: 1.75rem 2rem;
            margin-bottom: 1.5rem;
            border-radius: 14px;
            background: linear-gradient(135deg, {COLOR_SURFACE} 0%, #1F2530 100%);
            border-left: 6px solid {COLOR_PRIMARY};
            box-shadow: 0 4px 18px rgba(0, 0, 0, 0.35);
        }}
        .app-header h1 {{
            margin: 0;
            font-size: 2.1rem;
            font-weight: 900;
            letter-spacing: -0.5px;
        }}
        .app-header p {{
            margin: 0.35rem 0 0 0;
            color: {COLOR_MUTED};
            font-size: 1.02rem;
        }}

        section[data-testid="stSidebar"] {{
            background-color: {COLOR_SURFACE};
            border-right: 1px solid #2A2F3A;
        }}

        div[data-testid="stMetric"] {{
            background-color: {COLOR_SURFACE};
            border: 1px solid #2A2F3A;
            border-radius: 12px;
            padding: 1rem 1rem 0.75rem 1rem;
            transition: border-color 0.15s ease-in-out;
        }}
        div[data-testid="stMetric"]:hover {{
            border-color: {COLOR_PRIMARY};
        }}

        button[kind="primary"] {{
            background-color: {COLOR_PRIMARY} !important;
            border: none !important;
            font-weight: 700 !important;
        }}

        .stTabs [data-baseweb="tab-list"] {{
            gap: 4px;
        }}
        .stTabs [data-baseweb="tab"] {{
            background-color: {COLOR_SURFACE};
            border-radius: 8px 8px 0 0;
            padding: 0.5rem 1.25rem;
            font-weight: 600;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {COLOR_PRIMARY} !important;
            color: white !important;
        }}

        .app-footer {{
            margin-top: 2.5rem;
            padding: 1.25rem 0 0.5rem 0;
            border-top: 1px solid #2A2F3A;
            color: {COLOR_MUTED};
            font-size: 0.85rem;
            text-align: center;
        }}
        .app-footer a {{
            color: {COLOR_SECONDARY};
            text-decoration: none;
        }}
        .app-footer a:hover {{
            text-decoration: underline;
        }}

        ::-webkit-scrollbar {{ height: 8px; width: 8px; }}
        ::-webkit-scrollbar-thumb {{ background: #3A3F4A; border-radius: 4px; }}
    </style>
    """, unsafe_allow_html=True)


def render_footer() -> None:
    """A small, consistent footer shown at the bottom of every page state
    (including the "no session loaded yet" screen), attributing the data
    source and linking back to the project — the kind of finishing touch
    that separates a polished portfolio piece from a bare prototype.
    """
    st.markdown(f"""
    <div class="app-footer">
        Built with Streamlit, Plotly &amp; <a href="https://docs.fastf1.dev/" target="_blank">FastF1</a>
        · Timing &amp; telemetry data © Formula 1 / FIA, accessed via the official live timing API
        · <a href="https://github.com/" target="_blank">View source on GitHub</a>
    </div>
    """, unsafe_allow_html=True)
