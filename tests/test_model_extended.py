"""Tests for model.py — extended coverage for untested functions."""
import os

import numpy as np
import pandas as pd
import pytest

from app.model import (

pytestmark = pytest.mark.slow
    load_model,
    load_movies,
    load_ratings_sample,
    predict_rating,
    save_model,
)

# ─── Fixtures ───────────────────────────────────────────────────────


@pytest.fixture
def sample_movies_csv(tmp_path):
    """Create a minimal movies.csv for testing."""
    csv = tmp_path / "movies.csv"
    csv.write_text(
        "movieId,title,genres\n"
        "1,Toy Story (1995),Adventure|Animation|Children|Comedy|Fantasy\n"
        "2,Jumanji (1995),Adventure|Children|Fantasy\n"
        "3,Grumpier Old Men (1995),Comedy|Romance\n"
        "4,Waiting to Exhale (1995),Comedy|Drama|Romance\n"
        "5,Father of the Bride Part II (1995),Comedy\n"
    )
    return str(csv)


@pytest.fixture
def sample_ratings_csv(tmp_path):
    """Create a minimal ratings.csv for testing."""
    csv = tmp_path / "ratings.csv"
    csv.write_text(
        "userId,movieId,rating,timestamp\n"
        "1,1,4.0,964982703\n"
        "1,3,4.0,964981247\n"
        "2,1,4.0,964982224\n"
        "2,2,4.0,964981247\n"
        "3,1,5.0,964982703\n"
        "3,2,3.0,964981247\n"
        "3,3,4.0,964981247\n"
        "4,1,3.0,964982703\n"
        "4,2,4.0,964981247\n"
        "5,1,5.0,964982703\n"
    )
    return str(csv)


@pytest.fixture
def sample_model_result():
    """Create a model result dict with picklable objects."""
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler

    # Use real sklearn objects (picklable)
    rf = RandomForestRegressor(n_estimators=10, random_state=42)
    scaler = StandardScaler()
    # Fit on dummy data
    X_dummy = np.random.rand(10, 4)
    scaler.fit(X_dummy)
    rf.fit(X_dummy, np.random.rand(10))

    return {
        "best_model": rf,
        "best_model_name": "RandomForest",
        "rf_model": rf,
        "xgb_model": None,
        "scaler": scaler,
        "feature_cols": ["genre_action", "genre_comedy", "year", "rating_count"],
        "num_cols": ["year", "rating_count"],
        "metrics": {"rmse": 0.5, "mae": 0.3, "r2": 0.8},
        "importance": pd.DataFrame({"feature": ["year", "rating_count"], "importance": [0.6, 0.4]}),
        "merged_data": pd.DataFrame(),
        "rf_params": {"n_estimators": 100},
    }


# ─── load_ratings_sample ────────────────────────────────────────────


class TestLoadRatingsSample:
    """Tests for load_ratings_sample function."""

    def test_returns_dataframe(self, sample_ratings_csv):
        result = load_ratings_sample(sample_ratings_csv, n=5)
        assert isinstance(result, pd.DataFrame)

    def test_sample_size(self, sample_ratings_csv):
        result = load_ratings_sample(sample_ratings_csv, n=3)
        assert len(result) <= 3

    def test_has_required_columns(self, sample_ratings_csv):
        result = load_ratings_sample(sample_ratings_csv, n=10)
        assert "userId" in result.columns
        assert "movieId" in result.columns
        assert "rating" in result.columns

    def test_returns_all_when_n_larger(self, sample_ratings_csv):
        result = load_ratings_sample(sample_ratings_csv, n=100)
        assert len(result) == 10  # only 10 rows in CSV


# ─── save_model ──────────────────────────────────────────────────────


class TestSaveModel:
    """Tests for save_model function."""

    def test_creates_directory(self, sample_model_result, tmp_path):
        save_dir = str(tmp_path / "test_model")
        result_path = save_model(sample_model_result, name="test", dir_path=save_dir)
        assert os.path.exists(result_path)
        assert os.path.isdir(result_path)

    def test_creates_model_file(self, sample_model_result, tmp_path):
        save_dir = str(tmp_path / "test_model")
        result_path = save_model(sample_model_result, name="test", dir_path=save_dir)
        assert os.path.exists(os.path.join(result_path, "model.joblib"))

    def test_creates_meta_file(self, sample_model_result, tmp_path):
        save_dir = str(tmp_path / "test_model")
        result_path = save_model(sample_model_result, name="test", dir_path=save_dir)
        assert os.path.exists(os.path.join(result_path, "meta.joblib"))

    def test_returns_path_string(self, sample_model_result, tmp_path):
        save_dir = str(tmp_path / "test_model")
        result_path = save_model(sample_model_result, name="test", dir_path=save_dir)
        assert isinstance(result_path, str)


# ─── load_model ──────────────────────────────────────────────────────


class TestLoadModel:
    """Tests for load_model function."""

    def test_loads_saved_model(self, sample_model_result, tmp_path):
        save_dir = str(tmp_path / "test_model")
        save_model(sample_model_result, name="test", dir_path=save_dir)
        loaded = load_model(name="test", dir_path=save_dir)
        assert isinstance(loaded, dict)
        assert "best_model" in loaded
        assert "scaler" in loaded
        assert "feature_cols" in loaded

    def test_loads_metadata(self, sample_model_result, tmp_path):
        save_dir = str(tmp_path / "test_model")
        save_model(sample_model_result, name="test", dir_path=save_dir)
        loaded = load_model(name="test", dir_path=save_dir)
        assert "metrics" in loaded
        assert "importance" in loaded

    def test_missing_model_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_model(name="nonexistent", dir_path=str(tmp_path))

    def test_feature_cols_preserved(self, sample_model_result, tmp_path):
        save_dir = str(tmp_path / "test_model")
        save_model(sample_model_result, name="test", dir_path=save_dir)
        loaded = load_model(name="test", dir_path=save_dir)
        assert loaded["feature_cols"] == sample_model_result["feature_cols"]


# ─── predict_rating ──────────────────────────────────────────────────


class TestPredictRating:
    """Tests for predict_rating function."""

    def _make_model(self):
        """Create a model+scaler pair with matching feature shapes.

        predict_rating builds a DataFrame with feature_cols + 3 derived
        columns (genre_count, title_length, title_words), so the model
        must be trained on the full expanded set.
        """
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.preprocessing import StandardScaler


        feature_cols = ["genre_action", "genre_comedy", "year", "rating_count"]
        num_cols = ["year", "rating_count"]
        # All columns predict_rating will produce
        all_model_cols = feature_cols + ["genre_count", "title_length", "title_words"]
        rf = RandomForestRegressor(n_estimators=10, random_state=42)
        scaler = StandardScaler()
        # Fit scaler on 2 numeric columns (matching num_cols)
        scaler.fit(np.random.rand(10, 2))
        # Fit model on all 7 columns the function will produce
        rf.fit(np.random.rand(10, len(all_model_cols)), np.random.rand(10))
        return rf, scaler, feature_cols, num_cols

    def test_returns_float(self):
        rf, scaler, feature_cols, num_cols = self._make_model()
        movie_row = pd.Series({"movieId": 1, "genre_list": ["Action", "Comedy"], "year": 2000, "rating_count": 100})
        result = predict_rating(movie_row, rf, scaler, feature_cols, num_cols)
        assert isinstance(result, float)

    def test_returns_value_in_range(self):
        rf, scaler, feature_cols, num_cols = self._make_model()
        movie_row = pd.Series({"movieId": 1, "genre_list": ["Action", "Comedy"], "year": 2000, "rating_count": 100})
        result = predict_rating(movie_row, rf, scaler, feature_cols, num_cols)
        assert 0.0 <= result <= 5.0

    def test_empty_genre_list(self):
        rf, scaler, feature_cols, num_cols = self._make_model()
        movie_row = pd.Series({"movieId": 1, "genre_list": [], "year": 2000, "rating_count": 100})
        result = predict_rating(movie_row, rf, scaler, feature_cols, num_cols)
        assert isinstance(result, float)

    def test_none_year(self):
        rf, scaler, feature_cols, num_cols = self._make_model()
        movie_row = pd.Series({"movieId": 1, "genre_list": ["Action"], "year": None, "rating_count": 50})
        result = predict_rating(movie_row, rf, scaler, feature_cols, num_cols)
        assert isinstance(result, float)

    def test_with_tag_pivot(self):
        rf, scaler, feature_cols, num_cols = self._make_model()
        movie_row = pd.Series({"movieId": 1, "genre_list": ["Action"], "year": 2000, "rating_count": 50})
        tag_pivot = pd.DataFrame({"movieId": [1], "genre_action": [0.5], "genre_comedy": [0.2]})
        result = predict_rating(movie_row, rf, scaler, feature_cols, num_cols, tag_pivot=tag_pivot)
        assert isinstance(result, float)


# ─── load_movies ─────────────────────────────────────────────────────


class TestLoadMoviesExtended:
    """Extended tests for load_movies function."""

    def test_returns_dataframe(self, sample_movies_csv):
        result = load_movies(sample_movies_csv)
        assert isinstance(result, pd.DataFrame)

    def test_has_expected_columns(self, sample_movies_csv):
        result = load_movies(sample_movies_csv)
        assert "movieId" in result.columns
        assert "title" in result.columns
        assert "genres" in result.columns

    def test_extracts_year(self, sample_movies_csv):
        result = load_movies(sample_movies_csv)
        assert "year" in result.columns
        assert result["year"].notna().any()

    def test_creates_genre_count(self, sample_movies_csv):
        result = load_movies(sample_movies_csv)
        assert "genre_count" in result.columns
