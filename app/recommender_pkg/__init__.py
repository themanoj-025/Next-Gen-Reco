"""Recommender package — assembles MovieRecommender from mixins.

Re-exports ``MovieRecommender`` so ``from app.recommender import MovieRecommender``
continues to work unchanged.
"""

from __future__ import annotations

from typing import Any

from app.recommender_pkg.core import (
    CoreMixin,
    _CACHE_DIR,
    _GENRE_CACHE_PATH,
    _MOVIES_CACHE_PATH,
    _check_cache_valid,
    _predict_model_result,
    _predict_movies_by_id,
    _predict_tag_pivot,
    _prediction_cache,
)
from app.recommender_pkg.enrichment import EnrichmentMixin
from app.recommender_pkg.explain import ExplainMixin
from app.recommender_pkg.features import FeaturesMixin
from app.recommender_pkg.recommend import RecommendMixin
from app.recommender_pkg.search import SearchMixin
from app.recommender_pkg.stats import StatsMixin


class MovieRecommender(
    CoreMixin,
    SearchMixin,
    RecommendMixin,
    FeaturesMixin,
    StatsMixin,
    EnrichmentMixin,
    ExplainMixin,
):
    """Content-based movie recommender using hybrid similarity scoring.

    Composed from focused mixin modules for maintainability.
    """

    pass


__all__ = ["MovieRecommender"]
