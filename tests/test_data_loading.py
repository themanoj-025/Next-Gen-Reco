"""
Tests for app/model.py — data loading, feature engineering, and prediction.

Covers:
  - _extract_year() parsing
  - load_movies() DataFrame shape and derived columns
  - load_tags() pivot structure
  - load_model() bundle loading
  - predict_rating() output range
"""

import numpy as np
import pandas as pd

# ── _extract_year ─────────────────────────────────────────────────────────────


class TestExtractYear:
    """Tests for the year extraction helper."""

    def test_extracts_year_from_parentheses(self):
        from app.model import _extract_year

        assert _extract_year("Toy Story (1995)") == 1995.0

    def test_extracts_year_with_special_chars(self):
        from app.model import _extract_year

        assert _extract_year("The Matrix (1999)") == 1999.0

    def test_returns_none_when_no_year(self):
        from app.model import _extract_year

        assert _extract_year("No Year Here") is None

    def test_returns_none_for_empty_string(self):
        from app.model import _extract_year

        assert _extract_year("") is None

    def test_extracts_year_from_long_title(self):
        from app.model import _extract_year

        result = _extract_year("Star Wars: Episode IV - A New Hope (1977)")
        assert result == 1977.0

    def test_handles_year_in_middle(self):
        from app.model import _extract_year

        # regex looks for (YYYY) anywhere, returns first match
        result = _extract_year("Movie (1999) Sequel")
        assert result == 1999.0


# ── load_movies ───────────────────────────────────────────────────────────────


class TestLoadMovies:
    """Tests for the movies CSV loader."""

    def test_returns_dataframe(self, movies_df):
        assert isinstance(movies_df, pd.DataFrame)

    def test_has_expected_columns(self, movies_df):
        expected = {"movieId", "title", "genres", "year", "genre_list", "genre_count", "title_length", "title_words"}
        assert expected.issubset(set(movies_df.columns))

    def test_non_empty(self, movies_df):
        assert len(movies_df) > 0

    def test_year_column_is_numeric(self, movies_df):
        # year can be NaN for movies without a year in the title
        valid_years = movies_df["year"].dropna()
        assert valid_years.dtype in (np.float64, np.float32, int)

    def test_genre_list_is_list(self, movies_df):
        sample = movies_df["genre_list"].iloc[0]
        assert isinstance(sample, list)

    def test_genre_count_matches_genre_list(self, movies_df):
        for _, row in movies_df.head(50).iterrows():
            assert row["genre_count"] == len(row["genre_list"])

    def test_title_length_is_positive(self, movies_df):
        assert (movies_df["title_length"] > 0).all()

    def test_title_words_is_positive(self, movies_df):
        assert (movies_df["title_words"] > 0).all()


# ── load_tags ─────────────────────────────────────────────────────────────────


class TestLoadTags:
    """Tests for the tags pivot table loader."""

    def test_returns_dataframe(self):
        from app.model import load_tags

        result = load_tags(top_k=10)
        assert isinstance(result, pd.DataFrame)

    def test_has_movieid_column(self):
        from app.model import load_tags

        result = load_tags(top_k=10)
        assert "movieId" in result.columns

    def test_tag_columns_are_int8(self):
        from app.model import load_tags

        result = load_tags(top_k=10)
        tag_cols = [c for c in result.columns if c != "movieId"]
        for col in tag_cols[:5]:
            assert result[col].dtype == np.int8

    def test_top_k_limits_columns(self):
        from app.model import load_tags

        result = load_tags(top_k=5)
        tag_cols = [c for c in result.columns if c != "movieId"]
        assert len(tag_cols) <= 5


# ── load_model ────────────────────────────────────────────────────────────────


class TestLoadModel:
    """Tests for the trained model bundle loader."""

    def test_returns_dict(self, model_result):
        assert isinstance(model_result, dict)

    def test_has_required_keys(self, model_result):
        required = {"best_model", "scaler", "feature_cols", "num_cols", "metrics", "importance"}
        assert required.issubset(set(model_result.keys()))

    def test_best_model_is_predictor(self, model_result):
        model = model_result["best_model"]
        assert hasattr(model, "predict")

    def test_feature_cols_is_nonempty_list(self, model_result):
        assert isinstance(model_result["feature_cols"], list)
        assert len(model_result["feature_cols"]) > 0

    def test_metrics_have_r2(self, model_result):
        metrics = model_result["metrics"]
        assert "RandomForest" in metrics
        assert "R2" in metrics["RandomForest"]


# ── predict_rating ────────────────────────────────────────────────────────────


class TestPredictRating:
    """Tests for the predict_rating function."""

    def test_prediction_is_float(self, model_result, movies_df):
        from app.model import predict_rating

        row = movies_df.iloc[0]
        pred = predict_rating(
            row,
            model_result["best_model"],
            model_result["scaler"],
            model_result["feature_cols"],
            model_result["num_cols"],
        )
        assert isinstance(pred, float)

    def test_prediction_in_valid_range(self, model_result, movies_df):
        from app.model import predict_rating

        row = movies_df.iloc[0]
        pred = predict_rating(
            row,
            model_result["best_model"],
            model_result["scaler"],
            model_result["feature_cols"],
            model_result["num_cols"],
        )
        # MovieLens ratings are 0.5-5.0, predictions should be in a reasonable range
        assert 0.0 <= pred <= 6.0

    def test_different_movies_give_different_predictions(self, model_result, movies_df):
        from app.model import predict_rating

        preds = []
        for i in range(min(5, len(movies_df))):
            row = movies_df.iloc[i]
            pred = predict_rating(
                row,
                model_result["best_model"],
                model_result["scaler"],
                model_result["feature_cols"],
                model_result["num_cols"],
            )
            preds.append(pred)
        # At least some predictions should differ
        assert len({round(p, 2) for p in preds}) > 1

    def test_rating_count_affects_prediction(self, model_result, movies_df):
        from app.model import predict_rating

        row = movies_df.iloc[0]
        pred_low = predict_rating(
            row,
            model_result["best_model"],
            model_result["scaler"],
            model_result["feature_cols"],
            model_result["num_cols"],
            rating_count=5.0,
        )
        pred_high = predict_rating(
            row,
            model_result["best_model"],
            model_result["scaler"],
            model_result["feature_cols"],
            model_result["num_cols"],
            rating_count=5000.0,
        )
        # Predictions should differ when rating_count changes
        assert pred_low != pred_high
