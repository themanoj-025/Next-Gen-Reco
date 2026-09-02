import pytest

pytestmark = pytest.mark.unit

"""Unit tests for Next-Gen-Reco: recommender core, features, and data loader."""



# ── Core Mixin Pure Methods ─────────────────────────────────────────────────


class TestCoreMixinHelpers:
    """Tests for pure helper methods on CoreMixin (no data loading)."""

    def test_normalize_title(self) -> None:
        from app.recommender_pkg.core import CoreMixin

        # We can't instantiate CoreMixin without data, so test the method directly
        # by calling it as an unbound method with a mock self
        class MockCore:
            pass

        mock = MockCore()
        assert CoreMixin._normalize_title(mock, "The Matrix!") == "the matrix"
        assert CoreMixin._normalize_title(mock, "  Hello World  ") == "hello world"
        assert CoreMixin._normalize_title(mock, "Star Wars: Episode IV") == "star wars episode iv"

    def test_tokenize(self) -> None:
        from app.recommender_pkg.core import CoreMixin

        class MockCore:
            pass

        mock = MockCore()
        tokens = CoreMixin._tokenize(mock, "The Quick Brown Fox")
        assert tokens == ["the", "quick", "brown", "fox"]

    def test_tokenize_filters_short_tokens(self) -> None:
        from app.recommender_pkg.core import CoreMixin

        class MockCore:
            pass

        mock = MockCore()
        tokens = CoreMixin._tokenize(mock, "A I am OK")
        assert "a" not in tokens
        assert "i" not in tokens
        assert "am" in tokens
        assert "ok" in tokens

    def test_query_edit_distance_exact(self) -> None:
        from app.recommender_pkg.core import CoreMixin

        class MockCore:
            def _normalize_title(self, title) -> None:
                return CoreMixin._normalize_title(self, title)

        mock = MockCore()
        dist = CoreMixin._query_edit_distance(mock, "the matrix", "The Matrix")
        assert dist == 0

    def test_query_edit_distance_typo(self) -> None:
        from app.recommender_pkg.core import CoreMixin

        class MockCore:
            def _normalize_title(self, title) -> None:
                return CoreMixin._normalize_title(self, title)

        mock = MockCore()
        dist = CoreMixin._query_edit_distance(mock, "the matrx", "The Matrix")
        assert dist == 1

    def test_query_edit_distance_empty(self) -> None:
        from app.recommender_pkg.core import CoreMixin

        class MockCore:
            def _normalize_title(self, title) -> None:
                return CoreMixin._normalize_title(self, title)

        mock = MockCore()
        assert CoreMixin._query_edit_distance(mock, "", "The Matrix") == 99
        assert CoreMixin._query_edit_distance(mock, "matrix", "") == 99


# ── Features Mixin Pure Methods ─────────────────────────────────────────────


class TestFeaturesMixin:
    """Tests for feature mixin methods."""

    def test_import(self) -> None:
        from app.recommender_pkg.features import FeaturesMixin

        assert hasattr(FeaturesMixin, "get_movies_by_decade")
        assert hasattr(FeaturesMixin, "find_movies_combo")
        assert hasattr(FeaturesMixin, "movie_night_generator")


# ── Data Loader ─────────────────────────────────────────────────────────────


class TestDataLoader:
    """Tests for data loading utilities."""

    def test_import(self) -> None:
        from app.data.loader import _load_user_data, _save_user_data

        assert callable(_load_user_data)
        assert callable(_save_user_data)

    def test_user_data_file_path(self) -> None:
        from app.data.loader import USER_DATA_FILE

        assert USER_DATA_FILE.name == ".movie_user_data.json"
