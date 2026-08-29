"""Tests for Next-Gen-Reco model module — year extraction, data loading, feature engineering."""

import pandas as pd
import pytest


class TestExtractYear:
    """Tests for year extraction from movie titles."""

    def test_extracts_year_from_parentheses(self):
        from app.model import _extract_year

        assert _extract_year("Toy Story (1995)") == 1995.0

    def test_returns_none_for_no_year(self):
        from app.model import _extract_year

        assert _extract_year("No Year Here") is None

    def test_extracts_year_from_complex_title(self):
        from app.model import _extract_year

        assert _extract_year("The Matrix (1999) [Some Tag]") == 1999.0

    def test_extracts_four_digit_year(self):
        from app.model import _extract_year

        assert _extract_year("Movie (2024)") == 2024.0

    def test_returns_none_for_empty_string(self):
        from app.model import _extract_year

        assert _extract_year("") is None

    def test_handles_year_outside_parens(self):
        """Year not in parentheses should return None."""
        from app.model import _extract_year

        assert _extract_year("Movie 1995") is None


class TestCachePath:
    """Tests for cache path generation."""

    def test_returns_path_object(self):
        from pathlib import Path

        from app.model import _cache_path

        result = _cache_path("test_cache.pkl")
        assert isinstance(result, Path)

    def test_uses_cache_dir(self):
        from app.model import _CACHE_DIR, _cache_path

        result = _cache_path("test.pkl")
        assert str(_CACHE_DIR) in str(result)


class TestIsCacheValid:
    """Tests for cache freshness validation."""

    def test_nonexistent_cache_returns_false(self, tmp_path):
        from app.model import _is_cache_valid

        fake_path = tmp_path / "nonexistent.pkl"
        assert _is_cache_valid(fake_path) is False

    def test_cache_newer_than_source_returns_true(self, tmp_path):
        import time

        from app.model import _is_cache_valid

        cache = tmp_path / "cache.pkl"
        source = tmp_path / "source.csv"
        cache.write_text("cached")
        time.sleep(0.01)
        source.write_text("source")
        # Cache is older than source
        assert _is_cache_valid(cache, source) is False

    def test_cache_newer_than_all_sources(self, tmp_path):
        import time

        from app.model import _is_cache_valid

        source1 = tmp_path / "s1.csv"
        source2 = tmp_path / "s2.csv"
        source1.write_text("a")
        source2.write_text("b")
        time.sleep(0.01)
        cache = tmp_path / "cache.pkl"
        cache.write_text("cached")
        assert _is_cache_valid(cache, source1, source2) is True

    def test_missing_source_ignored(self, tmp_path):
        from app.model import _is_cache_valid

        cache = tmp_path / "cache.pkl"
        cache.write_text("cached")
        nonexistent = tmp_path / "nope.csv"
        assert _is_cache_valid(cache, nonexistent) is True


class TestLoadMovies:
    """Tests for movie data loading (requires test data fixture)."""

    @pytest.fixture
    def sample_movies_csv(self, tmp_path):
        """Create a minimal movies.csv for testing."""
        csv_content = (
            "movieId,title,genres\n"
            '1,"Toy Story (1995)",Adventure|Animation|Children|Comedy|Fantasy\n'
            '2,"Jumanji (1995)",Adventure|Children|Fantasy\n'
            '3,"Grumpier Old Men (1995)",Comedy|Romance\n'
            '4,"Waiting to Exhale (1995)",Comedy|Drama|Romance\n'
            '5,"Father of the Bride Part II (1995)",Comedy\n'
        )
        csv_path = tmp_path / "movies.csv"
        csv_path.write_text(csv_content)
        return str(csv_path)

    def test_load_movies_returns_dataframe(self, sample_movies_csv):
        from app.model import load_movies

        df = load_movies(sample_movies_csv)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5

    def test_load_movies_extracts_year(self, sample_movies_csv):
        from app.model import load_movies

        df = load_movies(sample_movies_csv)
        assert "year" in df.columns
        assert df.iloc[0]["year"] == 1995.0

    def test_load_movies_creates_genre_list(self, sample_movies_csv):
        from app.model import load_movies

        df = load_movies(sample_movies_csv)
        assert "genre_list" in df.columns
        assert isinstance(df.iloc[0]["genre_list"], list)
        assert "Adventure" in df.iloc[0]["genre_list"]

    def test_load_movies_computes_derived_features(self, sample_movies_csv):
        from app.model import load_movies

        df = load_movies(sample_movies_csv)
        assert "genre_count" in df.columns
        assert "title_length" in df.columns
        assert "title_words" in df.columns
        assert df.iloc[0]["genre_count"] == 5  # Toy Story has 5 genres


class TestBuildFeatures:
    """Tests for feature matrix construction."""

    @pytest.fixture
    def sample_data(self, tmp_path):
        """Create minimal movies and ratings data."""
        movies_csv = tmp_path / "movies.csv"
        movies_csv.write_text(
            "movieId,title,genres\n"
            '1,"Movie A (2000)",Action|Drama\n'
            '2,"Movie B (2001)",Comedy\n'
            '3,"Movie C (2002)",Action|Comedy\n'
        )
        ratings_csv = tmp_path / "ratings.csv"
        ratings_csv.write_text(
            "userId,movieId,rating\n"
            "1,1,4.0\n"
            "1,2,3.0\n"
            "2,1,5.0\n"
            "2,3,4.0\n"
            "3,2,2.0\n"
            "3,3,5.0\n"
        )
        return str(movies_csv), str(ratings_csv)

    def test_build_features_returns_tuple(self, sample_data):
        from app.model import _build_features, load_movies

        movies_path, ratings_path = sample_data
        movies = load_movies(movies_path)
        ratings = pd.read_csv(ratings_path)
        X, y, feature_cols, num_cols, mf = _build_features(movies, ratings)
        assert isinstance(X, pd.DataFrame)
        assert isinstance(y, pd.Series)
        assert len(X) == len(y)
        assert len(feature_cols) > 0

    def test_build_features_has_genre_columns(self, sample_data):
        from app.model import _build_features, load_movies

        movies_path, ratings_path = sample_data
        movies = load_movies(movies_path)
        ratings = pd.read_csv(ratings_path)
        X, y, feature_cols, num_cols, mf = _build_features(movies, ratings)
        genre_cols = [c for c in feature_cols if c in ("Action", "Comedy", "Drama")]
        assert len(genre_cols) >= 2


class TestLoadTags:
    """Tests for tag loading and pivot creation."""

    @pytest.fixture
    def sample_tags_csv(self, tmp_path):
        csv_content = (
            "userId,movieId,tag\n"
            "1,1,action\n"
            "1,1,adventure\n"
            "2,1,action\n"
            "2,2,comedy\n"
            "3,1,drama\n"
            "3,2,comedy\n"
        )
        csv_path = tmp_path / "tags.csv"
        csv_path.write_text(csv_content)
        return str(csv_path)

    def test_load_tags_returns_dataframe(self, sample_tags_csv):
        from app.model import load_tags

        df = load_tags(sample_tags_csv, top_k=10)
        assert isinstance(df, pd.DataFrame)
        assert "movieId" in df.columns

    def test_load_tags_has_tag_columns(self, sample_tags_csv):
        from app.model import load_tags

        df = load_tags(sample_tags_csv, top_k=10)
        tag_cols = [c for c in df.columns if c.startswith("tag_")]
        assert len(tag_cols) > 0
