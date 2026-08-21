"""
Shared fixtures for Next-Gen-Reco pytest suite.

Loads the MovieRecommender once per session (expensive — ~87K movies + model).
Individual tests that need a lighter setup use their own fixtures.
"""

import sys
from pathlib import Path

import pytest

# Ensure project root is on sys.path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


@pytest.fixture(scope="module")
def recommender():
    """Load MovieRecommender once for the entire test module.

    This is expensive (~1-3s) but avoids reloading 87K movies per test.
    """
    from app.recommender import MovieRecommender

    return MovieRecommender(model_name="v1_test")


@pytest.fixture(scope="module")
def movies_df():
    """Load the raw movies DataFrame once."""
    from app.model import load_movies

    return load_movies()


@pytest.fixture(scope="module")
def model_result():
    """Load the trained model once."""
    from app.model import load_model

    return load_model(name="v1_test")
