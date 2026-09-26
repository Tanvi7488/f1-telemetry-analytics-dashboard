"""
utils package
-------------
Groups the app's non-UI logic into three focused modules:

  data_loader.py  -> talks to FastF1 (cache setup, sessions, schedules)
  analysis.py     -> pure data analysis (fastest laps, speeds, deltas)
  charts.py       -> builds Plotly figures from analysis output
  styling.py      -> custom CSS for the Streamlit UI

This separation keeps app.py thin: it only wires selections to
function calls and renders the results.
"""
