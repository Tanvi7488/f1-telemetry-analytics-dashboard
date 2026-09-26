"""
tests package.

Having this __init__.py present (combined with pytest.ini's
`pythonpath = .`) ensures the project root is importable during test
collection, so `from utils.analysis import ...` and `from config import
...` resolve the same way inside tests as they do when running the
real app with `streamlit run app.py`.
"""
