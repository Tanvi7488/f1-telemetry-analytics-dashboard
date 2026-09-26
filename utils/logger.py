"""
utils/logger.py
-----------------
A tiny, centralized logging setup.

The app deliberately does NOT show raw exceptions or tracebacks to end
users — that's a poor, unprofessional experience and can leak internal
details. Instead, every module logs full technical detail here (visible
in the terminal, or your hosting platform's log viewer), while the UI
layer (app.py) shows a short, friendly message. This mirrors how a real
production service separates "what the developer needs to see" from
"what the user needs to see."
"""

import logging
import sys

_CONFIGURED = False


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger, configuring the root handler once
    no matter how many modules call this at import time.
    """
    global _CONFIGURED
    if not _CONFIGURED:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            stream=sys.stdout,
        )
        _CONFIGURED = True
    return logging.getLogger(name)
