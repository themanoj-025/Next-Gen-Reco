"""
Shared fixtures for Next-Gen-Reco pytest suite.

Loads the MovieRecommender once per session (expensive — ~87K movies + model).
Individual tests that need a lighter setup use their own fixtures.
"""

import pytest


@pytest.fixture(scope="module")
def recommender() -> None:
    """Load MovieRecommender once for the entire test module.

    This is expensive (~1-3s) but avoids reloading 87K movies per test.
    """
    from app.recommender import MovieRecommender

    return MovieRecommender(model_name="v1_test")


@pytest.fixture(scope="module")
def movies_df() -> None:
    """Load the raw movies DataFrame once."""
    from app.model import load_movies

    return load_movies()


@pytest.fixture(scope="module")
def model_result() -> None:
    """Load the trained model once."""
    from app.model import load_model

    return load_model(name="v1_test")
