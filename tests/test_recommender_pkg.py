"""Tests for Next-Gen-Reco recommender_pkg sub-modules.

Tests cache validation, title normalization, and explain features.
"""

from pathlib import Path

import pandas as pd


class TestCacheValidation:
    """Test cache validity checking."""

    def test_cache_not_exists(self) -> None:
        from app.recommender_pkg.core import _check_cache_valid

        assert _check_cache_valid(Path("/nonexistent/cache.pkl")) is False

    def test_cache_exists_no_sources(self, tmp_path: Path) -> None:
        from app.recommender_pkg.core import _check_cache_valid

        cache = tmp_path / "cache.pkl"
        cache.touch()
        assert _check_cache_valid(cache) is True

    def test_cache_older_than_source(self, tmp_path: Path) -> None:
        from app.recommender_pkg.core import _check_cache_valid

        cache = tmp_path / "cache.pkl"
        cache.touch()
        source = tmp_path / "source.parquet"
        source.write_text("data")
        # Cache is older than source
        assert _check_cache_valid(cache, source) is False


class TestTitleNormalization:
    """Test movie title normalization."""

    def test_normalize_basic(self) -> None:
        from app.recommender_pkg.core import _normalize_title

        assert _normalize_title("Toy Story") == "toy story"

    def test_normalize_with_year(self) -> None:
        from app.recommender_pkg.core import _normalize_title

        result = _normalize_title("Toy Story (1995)")
        assert "1995" not in result

    def test_normalize_whitespace(self) -> None:
        from app.recommender_pkg.core import _normalize_title

        assert _normalize_title("  Toy Story  ") == "toy story"


class TestExplainMixin:
    """Test explanation features."""

    def test_get_feature_breakdown_returns_none_for_unknown(self) -> None:
        from app.recommender_pkg.explain import ExplainMixin

        mixin = ExplainMixin.__new__(ExplainMixin)
        mixin.movies_by_id = {}
        mixin.model_result = None
        assert mixin.get_feature_breakdown(999999) is None

    def test_get_feature_breakdown_returns_none_for_no_prediction(self) -> None:
        from app.recommender_pkg.explain import ExplainMixin

        mixin = ExplainMixin.__new__(ExplainMixin)
        mixin.movies_by_id = {1: pd.Series({"title": "Test"})}
        mixin.model_result = None
        assert mixin.get_feature_breakdown(1) is None
