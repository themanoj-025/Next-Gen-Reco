"""Shared utilities for Next-Gen-Reco.

Small helpers referenced across application modules. The module-level
``logger`` is imported by ``model.py`` and ``main_model.py`` (structured
logging was introduced repo-wide in place of ``print()``); keep it here so
those modules import cleanly.
"""

import logging

logger = logging.getLogger("app.utils")
