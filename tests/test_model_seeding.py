"""Reproducibility regression tests for the RF + XGBoost ensemble.

``train_model`` must be deterministic for a fixed ``random_state``: the
split, RandomForest, XGBoost, and numpy/python RNGs are all seeded, so two
runs with the same seed produce bit-identical predictions and metrics, while
a different seed changes them.

Uses small synthetic CSVs + ``use_tuning=False`` so the whole file runs in
well under a second (marked ``unit``).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

pytestmark = pytest.mark.unit


@pytest.fixture
def train_paths(tmp_path) -> tuple[str, str]:
    """Synthetic movies + ratings CSVs (30 movies, 300 ratings)."""
    rng = np.random.default_rng(0)
    genres = ["Action", "Comedy", "Drama", "Romance", "Thriller"]
    movies = pd.DataFrame(
        {
            "movieId": range(1, 31),
            "title": [f"Movie {i} ({1990 + i})" for i in range(1, 31)],
            "genres": [genres[i % len(genres)] for i in range(30)],
        }
    )
    ratings = pd.DataFrame(
        {
            "userId": rng.integers(1, 11, size=300),
            "movieId": rng.integers(1, 31, size=300),
            "rating": rng.uniform(0.5, 5.0, size=300).round(1),
        }
    )
    movies_path = tmp_path / "movies.csv"
    ratings_path = tmp_path / "ratings.csv"
    movies.to_csv(movies_path, index=False)
    ratings.to_csv(ratings_path, index=False)
    return str(movies_path), str(ratings_path)


def _train(train_paths, seed: int) -> dict:
    from app.model import train_model

    movies_path, ratings_path = train_paths
    return train_model(
        movies_path=movies_path,
        ratings_path=ratings_path,
        use_tags=False,
        use_tuning=False,
        random_state=seed,
    )


class TestSeedReproducibility:
    """Same seed -> bit-identical model; different seed -> different model."""

    def test_same_seed_gives_identical_predictions(self, train_paths) -> None:
        r1 = _train(train_paths, seed=42)
        r2 = _train(train_paths, seed=42)

        X = r1["merged_data"][r1["feature_cols"]]
        X2 = r2["merged_data"][r2["feature_cols"]]
        np.testing.assert_array_equal(
            r1["rf_model"].predict(X),
            r2["rf_model"].predict(X2),
        )
        if r1["xgb_model"] is not None and r2["xgb_model"] is not None:
            np.testing.assert_array_equal(
                r1["xgb_model"].predict(X),
                r2["xgb_model"].predict(X2),
            )

    def test_same_seed_gives_identical_metrics(self, train_paths) -> None:
        r1 = _train(train_paths, seed=42)
        r2 = _train(train_paths, seed=42)
        assert r1["metrics"] == r2["metrics"]

    def test_same_seed_gives_identical_split(self, train_paths) -> None:
        r1 = _train(train_paths, seed=42)
        r2 = _train(train_paths, seed=42)
        assert list(r1["merged_data"].index) == list(r2["merged_data"].index)
        assert r1["metrics"]["train_samples"] == r2["metrics"]["train_samples"]
        assert r1["metrics"]["test_samples"] == r2["metrics"]["test_samples"]

    def test_different_seed_changes_predictions(self, train_paths) -> None:
        r1 = _train(train_paths, seed=42)
        r2 = _train(train_paths, seed=7)

        # Different seed -> different bootstrap/subsample draw -> at least
        # one prediction differs (allow exact equality only if identical).
        X = r1["merged_data"][r1["feature_cols"]]
        X2 = r2["merged_data"][r2["feature_cols"]]
        p1 = r1["rf_model"].predict(X)
        p2 = r2["rf_model"].predict(X2)
        assert not np.array_equal(p1, p2)

    def test_random_state_recorded_in_result(self, train_paths) -> None:
        result = _train(train_paths, seed=123)
        assert result["random_state"] == 123

    def test_rf_and_xgb_receive_seed(self, train_paths) -> None:
        result = _train(train_paths, seed=42)
        assert result["rf_model"].random_state == 42
        if result["xgb_model"] is not None:
            assert result["xgb_model"].random_state == 42

    def test_numpy_global_seeded(self, train_paths) -> None:
        """train_model seeds np.random — a draw after training is repeatable."""
        _train(train_paths, seed=42)
        first = np.random.rand(3)
        _train(train_paths, seed=42)
        second = np.random.rand(3)
        np.testing.assert_array_equal(first, second)


class TestSavedModelSeed:
    """The seed survives save/load so a reloaded model documents its seed."""

    def test_save_and_load_preserves_random_state(self, train_paths, tmp_path) -> None:
        from app.model import load_model, save_model

        result = _train(train_paths, seed=42)
        save_model(result, name="seed_test", dir_path=str(tmp_path))
        loaded = load_model(name="seed_test", dir_path=str(tmp_path))
        assert loaded["random_state"] == 42
        assert loaded["best_model_name"] == result["best_model_name"]
