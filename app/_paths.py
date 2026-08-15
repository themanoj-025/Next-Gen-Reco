"""
Centralized project root resolution.

All modules should import PROJECT_ROOT from here instead of using
relative paths.  On Streamlit Cloud the working directory can vary,
so we anchor every path to the directory that contains this file's
grandparent (the repo root).
"""

from pathlib import Path

# app/_paths.py  ->  app/  ->  PROJECT_ROOT/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Convenience aliases used throughout the codebase
DATA_DIR = PROJECT_ROOT / "data"
ND_DIR = DATA_DIR / "ND"
MODELS_DIR = PROJECT_ROOT / "models"
CACHE_DIR = PROJECT_ROOT / ".cache"
STREAMLIT_DIR = PROJECT_ROOT / ".streamlit"
