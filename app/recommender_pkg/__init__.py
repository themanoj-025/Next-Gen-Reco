"""Recommender package — assembles MovieRecommender from mixins.

Re-exports ``MovieRecommender`` so ``from app.recommender import MovieRecommender``
continues to work unchanged.
"""

from __future__ import annotations

from app.recommender_pkg.core import CoreMixin
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


__all__ = ["MovieRecommender"]
