"""
Shared fixtures for Next-Gen-Reco pytest suite.

Loads the MovieRecommender once per session (expensive — ~87K movies + model).
Individual tests that need a lighter setup use their own fixtures.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    import pandas as pd

    from app.recommender import MovieRecommender


@pytest.fixture(scope="module")
def recommender() -> MovieRecommender:
    """Load MovieRecommender once for the entire test module.

    This is expensive (~1-3s) but avoids reloading 87K movies per test.
    """
    from app.recommender import MovieRecommender

    return MovieRecommender(model_name="v1_test")


@pytest.fixture(scope="module")
def movies_df() -> pd.DataFrame:
    """Load the raw movies DataFrame once."""
    from app.model import load_movies

    return load_movies()


@pytest.fixture(scope="module")
def model_result() -> dict:
    """Load the trained model once."""
    from app.model import load_model

    return load_model(name="v1_test")
