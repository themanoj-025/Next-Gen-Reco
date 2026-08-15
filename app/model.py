"""
MovieLens Rating Predictor — ML Model (Improved)
=================================================
Random Forest + XGBoost regressors trained on MovieLens 32M dataset.
Features: genres (one-hot), tags (top 100), derived stats (genre count,
title length), rating_count, and release year.
"""

import os
import re
import time
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

from app._paths import CACHE_DIR, DATA_DIR, MODELS_DIR

# ── Cache helpers ──────────────────────────────────────────────────────────────

_CACHE_DIR = CACHE_DIR


def _cache_path(name: str) -> Path:
    """Get path to a cache file."""
    _CACHE_DIR.mkdir(exist_ok=True)
    return _CACHE_DIR / name


def _is_cache_valid(cache_path: str | Path, *source_paths: str | Path) -> bool:
    """Check if cache is newer than all source files."""
    cp = Path(cache_path)
    if not cp.exists():
        return False
    cache_mtime = cp.stat().st_mtime
    for sp in source_paths:
        p = Path(sp)
        if p.exists() and p.stat().st_mtime > cache_mtime:
            return False
    return True


# ── Helpers ───────────────────────────────────────────────────────────────────


def _extract_year(title: str) -> float | None:
    m = re.search(r"\((\d{4})\)", title)
    return float(m.group(1)) if m else None


# ── Data loading ──────────────────────────────────────────────────────────────


def load_movies(path: str | None = None) -> pd.DataFrame:
    """Load movies CSV and add derived features."""
    if path is None:
        path = str(DATA_DIR / "movies.csv")
    df = pd.read_csv(path)
    df["year"] = df["title"].apply(_extract_year)
    df["genre_list"] = df["genres"].str.split("|")
    df["genre_count"] = df["genre_list"].apply(len)
    df["title_length"] = df["title"].str.len()
    df["title_words"] = df["title"].str.split(r"\s+").apply(len)
    return df


def load_ratings_sample(path: str | None = None, n: int = 500_000) -> pd.DataFrame:
    """Load a sample of ratings (default 500K)."""
    if path is None:
        path = str(DATA_DIR / "ratings.csv")
    return pd.read_csv(
        path,
        nrows=n,
        dtype={"userId": "int32", "movieId": "int32", "rating": "float32"},
    )


def load_tags(path: str | None = None, top_k: int = 100) -> pd.DataFrame:
    """Load tags CSV and return top-K most frequent tags per movie as one-hot features.

    Results are cached to disk (as pickle) for fast subsequent loads.
    Cache is invalidated when the source CSV changes.
    """
    if path is None:
        path = str(DATA_DIR / "tags.csv")
    cache_file = _cache_path(f"tag_pivot_top{top_k}.pkl")

    # Try loading from cache first
    if _is_cache_valid(cache_file, path):
        try:
            df = pd.read_pickle(cache_file)
            print(f"  Loaded tag pivot from cache ({len(df)} rows)")
            return df
        except Exception:
            pass

    tags = pd.read_csv(
        path, dtype={"userId": "int32", "movieId": "int32", "tag": "object"}
    )

    # Find the top K most common tags overall
    top_tags = (
        tags["tag"].str.lower().str.strip().value_counts().head(top_k).index.tolist()
    )

    # Filter to only those tags
    tags = tags[tags["tag"].str.lower().str.strip().isin(top_tags)].copy()
    tags["tag"] = tags["tag"].str.lower().str.strip()

    # One tag per movie (keep first occurrence per movie)
    tags = tags.drop_duplicates(subset=["movieId", "tag"])

    # Pivot to one-hot: movieId x tag
    tag_pivot = pd.crosstab(tags["movieId"], tags["tag"])
    # Rename columns to avoid collisions
    tag_pivot.columns = [f"tag_{col.replace(' ', '_')}" for col in tag_pivot.columns]
    tag_pivot = tag_pivot.reset_index()
    tag_pivot = tag_pivot.astype(
        {c: "int8" for c in tag_pivot.columns if c != "movieId"}
    )

    # Save to cache
    try:
        tag_pivot.to_pickle(cache_file)
        print("  Saved tag pivot to cache")
    except Exception as e:
        print(f"  Warning: could not save tag cache ({e})")

    return tag_pivot


# ── Model training ────────────────────────────────────────────────────────────


def _build_features(
    movies: pd.DataFrame,
    ratings_sample: pd.DataFrame,
    tag_pivot: pd.DataFrame | None = None,
) -> tuple:
    """
    Build feature matrix X and target y from loaded data.
    Returns (X, y, feature_cols, num_cols, merged_df).
    """
    # Aggregate ratings per movie
    movie_stats = (
        ratings_sample.groupby("movieId")
        .agg(
            avg_rating=("rating", "mean"),
            rating_count=("rating", "count"),
        )
        .reset_index()
    )

    # Merge movies with their rating stats
    mf = movies.merge(movie_stats, on="movieId", how="inner")

    # One-hot encode genres
    genre_dummies = mf["genres"].str.get_dummies(sep="|")
    if "(no genres listed)" in genre_dummies.columns:
        genre_dummies = genre_dummies.drop(columns=["(no genres listed)"])
    mf = pd.concat([mf, genre_dummies], axis=1)

    # Merge tag features if provided
    if tag_pivot is not None and len(tag_pivot) > 0:
        mf = mf.merge(tag_pivot, on="movieId", how="left")
        # Fill NaN tags with 0
        tag_cols = [c for c in tag_pivot.columns if c != "movieId"]
        for c in tag_cols:
            if c in mf.columns:
                mf[c] = mf[c].fillna(0).astype("int8")
    else:
        tag_cols = []

    # Define feature columns
    genre_cols = list(genre_dummies.columns)
    derived_cols = ["genre_count", "title_length", "title_words"]
    stats_cols = ["rating_count"]
    year_cols = ["year"]

    num_cols = derived_cols + stats_cols + year_cols
    feature_cols = genre_cols + tag_cols + num_cols
    all_cols = [c for c in feature_cols if c in mf.columns]

    X = mf[all_cols].copy()
    y = mf["avg_rating"].copy()

    # Drop NaN rows
    mask = X.notna().all(axis=1)
    X = X[mask]
    y = y[mask]

    return X, y, all_cols, num_cols, mf


def train_model(
    movies_path: str | None = None,
    ratings_path: str | None = None,
    tags_path: str | None = None,
    sample_size: int = 500_000,
    top_tags: int = 100,
    use_tags: bool = True,
    use_tuning: bool = True,
    save_path: str | None = None,
    random_state: int = 42,
):
    """
    Train Random Forest + XGBoost models to predict average movie ratings.

    Features
    --------
    - Genre one-hot encoding (20+ genre columns)
    - Top-K most frequent user tags as one-hot features (if use_tags=True)
    - Derived: genre_count, title_length, title_words
    - Rating stats: rating_count
    - Release year

    Parameters
    ----------
    save_path : str or None
        If provided, save the trained model to this directory name under models/.
        E.g. save_path="v1" saves to models/v1/

    Returns
    -------
    dict with keys:
        best_model    - best trained model (RF or XGBoost)
        best_model_name - name of the best model
        rf_model      - trained RandomForestRegressor
        xgb_model     - trained XGBRegressor (or None if unavailable)
        scaler        - fitted StandardScaler
        feature_cols  - list of all feature column names
        num_cols      - list of numeric feature column names
        metrics       - dict with RMSE, MAE, R2 for each model
        importance    - DataFrame of feature importances (best model)
        merged_data   - DataFrame used for training
        rf_params     - best RF params (if tuning used)
    """
    if movies_path is None:
        movies_path = str(DATA_DIR / "movies.csv")
    if ratings_path is None:
        ratings_path = str(DATA_DIR / "ratings.csv")
    if tags_path is None:
        tags_path = str(DATA_DIR / "tags.csv")
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler

    print("Loading data...")
    movies = load_movies(movies_path)
    ratings = load_ratings_sample(ratings_path, n=sample_size)
    print(f"  Movies: {len(movies):,}  |  Ratings: {len(ratings):,}")

    tag_pivot = None
    if use_tags:
        print("Loading tags...")
        tag_pivot = load_tags(tags_path, top_k=top_tags)
        print(f"  Tags: {len(tag_pivot):,} movies with {top_tags} tag features")

    print("Building features...")
    X, y, feature_cols, num_cols, mf = _build_features(movies, ratings, tag_pivot)
    print(f"  Features: {len(feature_cols)}  |  Samples: {len(X):,}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state
    )

    # Scale numeric features
    num_cols_present = [c for c in num_cols if c in X_train.columns]
    scaler = StandardScaler()
    X_train_scaled = X_train.copy()
    X_test_scaled = X_test.copy()
    X_train_scaled[num_cols_present] = scaler.fit_transform(X_train[num_cols_present])
    X_test_scaled[num_cols_present] = scaler.transform(X_test[num_cols_present])

    metrics = {}
    rf_model = None
    xgb_model = None
    best_model = None
    best_name = ""
    rf_params = None

    # ── Random Forest ────────────────────────────────────────────────────
    print("\n1. Training Random Forest...")
    rf_start = time.time()

    if use_tuning:
        print("   Hyperparameter tuning with GridSearchCV...")
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.model_selection import GridSearchCV

        rf_param_grid = {
            "n_estimators": [100, 200, 300],
            "max_depth": [10, 15, 20, None],
            "min_samples_split": [2, 5, 10],
        }
        rf_base = RandomForestRegressor(random_state=random_state, n_jobs=-1, verbose=0)
        rf_grid = GridSearchCV(
            rf_base,
            rf_param_grid,
            cv=3,
            scoring="neg_mean_squared_error",
            n_jobs=-1,
            verbose=0,
        )
        rf_grid.fit(X_train_scaled, y_train)
        rf_model = rf_grid.best_estimator_
        rf_params = rf_grid.best_params_
        print(f"   Best params: {rf_params}")
    else:
        from sklearn.ensemble import RandomForestRegressor

        rf_model = RandomForestRegressor(
            n_estimators=200,
            max_depth=15,
            random_state=random_state,
            n_jobs=-1,
            verbose=0,
        )
        rf_model.fit(X_train_scaled, y_train)
        rf_params = None

    y_pred_rf = rf_model.predict(X_test_scaled)
    rf_metrics = {
        "RMSE": float(np.sqrt(mean_squared_error(y_test, y_pred_rf))),
        "MAE": float(mean_absolute_error(y_test, y_pred_rf)),
        "R2": float(r2_score(y_test, y_pred_rf)),
    }
    metrics["RandomForest"] = rf_metrics
    print(
        f"   RF - R^2: {rf_metrics['R2']:.4f}  RMSE: {rf_metrics['RMSE']:.4f}  "
        f"MAE: {rf_metrics['MAE']:.4f}  ({time.time() - rf_start:.1f}s)"
    )

    best_model = rf_model
    best_name = "RandomForest"

    # ── XGBoost ──────────────────────────────────────────────────────────
    try:
        import xgboost as xgb

        print("\n2. Training XGBoost...")
        xgb_start = time.time()

        if use_tuning:
            xgb_param_grid = {
                "n_estimators": [100, 200],
                "max_depth": [4, 6, 8],
                "learning_rate": [0.05, 0.1],
                "subsample": [0.8, 1.0],
            }
            from sklearn.model_selection import GridSearchCV

            xgb_base = xgb.XGBRegressor(
                random_state=random_state, n_jobs=-1, verbosity=0
            )
            xgb_grid = GridSearchCV(
                xgb_base,
                xgb_param_grid,
                cv=3,
                scoring="neg_mean_squared_error",
                n_jobs=-1,
                verbose=0,
            )
            xgb_grid.fit(X_train_scaled, y_train)
            xgb_model = xgb_grid.best_estimator_
            print(f"   Best params: {xgb_grid.best_params_}")
        else:
            xgb_model = xgb.XGBRegressor(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                random_state=random_state,
                n_jobs=-1,
                verbosity=0,
            )
            xgb_model.fit(X_train_scaled, y_train)

        y_pred_xgb = xgb_model.predict(X_test_scaled)
        xgb_metrics = {
            "RMSE": float(np.sqrt(mean_squared_error(y_test, y_pred_xgb))),
            "MAE": float(mean_absolute_error(y_test, y_pred_xgb)),
            "R2": float(r2_score(y_test, y_pred_xgb)),
        }
        metrics["XGBoost"] = xgb_metrics
        print(
            f"   XGB - R^2: {xgb_metrics['R2']:.4f}  RMSE: {xgb_metrics['RMSE']:.4f}  "
            f"MAE: {xgb_metrics['MAE']:.4f}  ({time.time() - xgb_start:.1f}s)"
        )

        # Pick the best model
        if xgb_metrics["R2"] > rf_metrics["R2"]:
            best_model = xgb_model
            best_name = "XGBoost"
    except ImportError:
        print("\n2. XGBoost not available — skipping.")

    # Feature importance from best model
    if hasattr(best_model, "feature_importances_"):
        imp = pd.DataFrame(
            {
                "feature": feature_cols,
                "importance": best_model.feature_importances_,
            }
        )
    else:
        # Fallback: use RF importance
        imp = pd.DataFrame(
            {
                "feature": feature_cols,
                "importance": rf_model.feature_importances_,
            }
        )

    imp = imp.sort_values("importance", ascending=False).reset_index(drop=True)

    # Overall metrics
    overall_metrics = {
        "train_samples": X_train_scaled.shape[0],
        "test_samples": X_test_scaled.shape[0],
        "feature_count": len(feature_cols),
    }
    overall_metrics.update(metrics)

    result = {
        "best_model": best_model,
        "best_model_name": best_name,
        "rf_model": rf_model,
        "xgb_model": xgb_model,
        "scaler": scaler,
        "feature_cols": feature_cols,
        "num_cols": num_cols_present,
        "metrics": overall_metrics,
        "importance": imp,
        "merged_data": mf,
        "rf_params": rf_params,
    }

    if save_path is not None:
        save_model(result, name=save_path)

    return result


# ── Model persistence ──────────────────────────────────────────────────────────


DEFAULT_MODEL_DIR = str(MODELS_DIR)


def save_model(
    result: dict, name: str = "best", dir_path: str = DEFAULT_MODEL_DIR
) -> str:
    """
    Save a trained model result dict to disk using joblib.

    Saves two files:
      {dir_path}/{name}/model.joblib   — model, scaler, feature_cols, num_cols
      {dir_path}/{name}/meta.joblib     — everything else (metrics, importance, etc.)

    Returns the full path to the saved model directory.
    """
    os.makedirs(os.path.join(dir_path, name), exist_ok=True)

    model_path = os.path.join(dir_path, name, "model.joblib")
    meta_path = os.path.join(dir_path, name, "meta.joblib")

    # Core prediction artifacts
    core = {
        "best_model": result["best_model"],
        "scaler": result["scaler"],
        "feature_cols": result["feature_cols"],
        "num_cols": result["num_cols"],
    }
    joblib.dump(core, model_path)

    # Everything else for display / analysis
    meta = {
        "best_model_name": result["best_model_name"],
        "rf_model": result.get("rf_model"),
        "xgb_model": result.get("xgb_model"),
        "metrics": result["metrics"],
        "importance": result["importance"],
        "rf_params": result.get("rf_params"),
    }
    joblib.dump(meta, meta_path)

    print(f"  Model saved to {model_path}")
    print(f"  Metadata saved to {meta_path}")
    return os.path.join(dir_path, name)


def load_model(name: str = "best", dir_path: str = DEFAULT_MODEL_DIR) -> dict:
    """
    Load a previously saved model from disk.

    Gracefully handles missing optional dependencies (e.g. xgboost) so the
    core prediction pipeline still works even if meta data can't be loaded.

    Returns a dict compatible with what train_model() returns.
    """
    model_path = os.path.join(dir_path, name, "model.joblib")
    meta_path = os.path.join(dir_path, name, "meta.joblib")

    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model not found at '{os.path.join(dir_path, name)}'. "
            f"Train and save a model first with: python model.py --save"
        )

    core = joblib.load(model_path)

    # Load meta separately — it may contain optional dependency objects
    # (e.g. XGBRegressor) that can fail if xgboost is not installed.
    meta = {}
    if os.path.exists(meta_path):
        try:
            meta = joblib.load(meta_path)
        except (ModuleNotFoundError, Exception) as e:
            print(f"  Warning: Could not load metadata ({e}). Running without extras.")

    result = {**core, **meta}
    if "best_model_name" not in result:
        result["best_model_name"] = "RandomForest"
        print(
            "  (defaulted best_model_name to RandomForest since meta was unavailable)"
        )

    print(f"  Loaded model '{name}' from {model_path}")
    return result


# ── Prediction ────────────────────────────────────────────────────────────────


def predict_rating(
    movie_row: pd.Series,
    model,
    scaler,
    feature_cols: list[str],
    num_cols: list[str],
    tag_pivot: pd.DataFrame | None = None,
    rating_count: float = 50.0,
) -> float:
    """Predict average rating for a single movie."""
    feats = pd.DataFrame([0.0] * len(feature_cols), index=feature_cols).T

    # Genre features
    for g in movie_row["genre_list"]:
        if g in feats.columns:
            feats.at[0, g] = 1.0

    # Tag features (if available)
    if tag_pivot is not None and len(tag_pivot) > 0:
        movie_tags = tag_pivot[tag_pivot["movieId"] == movie_row["movieId"]]
        if len(movie_tags) > 0:
            for c in tag_pivot.columns:
                if c != "movieId" and c in feats.columns:
                    try:
                        feats.at[0, c] = float(movie_tags.iloc[0][c])
                    except (ValueError, KeyError):
                        pass

    # Derived features
    feats.at[0, "genre_count"] = len(movie_row["genre_list"])
    feats.at[0, "title_length"] = len(str(movie_row.get("title", "")))
    feats.at[0, "title_words"] = len(str(movie_row.get("title", "")).split())

    # Numeric stats
    feats.at[0, "rating_count"] = rating_count

    # Year
    year_val = movie_row.get("year", 2000)
    if pd.isna(year_val):
        year_val = 2000
    feats.at[0, "year"] = year_val

    # Scale numeric cols
    present_num = [c for c in num_cols if c in feats.columns]
    feats[present_num] = scaler.transform(feats[present_num])

    return float(model.predict(feats)[0])


# ── CLI entry point ────────────────────────────────────────────────────────────


def main():
    """Train models and show comparison."""
    import sys

    args = [a.lower() for a in sys.argv[1:]]
    do_save = "--save" in args or "-s" in args
    load_name = None
    for a in args:
        if a.startswith("--load=") or a.startswith("-l="):
            load_name = a.split("=", 1)[1]

    print("=" * 55)
    print("  MovieLens Rating Predictor — Improved ML Model")
    print("=" * 55)

    if load_name:
        print(f"\nLoading saved model '{load_name}'...")
        result = load_model(name=load_name)
    else:
        result = train_model(
            sample_size=500_000,
            use_tags=True,
            top_tags=100,
            use_tuning=True,
            save_path="v1" if do_save else None,
        )

    metrics = result["metrics"]
    imp = result["importance"]
    best_name = result["best_model_name"]

    print(f"\n{'=' * 55}")
    print(f"  >> Best Model: {best_name}")
    print(f"{'=' * 55}")

    # Per-model comparison
    for model_name in ["RandomForest", "XGBoost"]:
        if model_name in metrics:
            m = metrics[model_name]
            print(f"  {model_name}:")
            print(f"    R^2:   {m['R2']:.4f}")
            print(f"    RMSE: {m['RMSE']:.4f}")
            print(f"    MAE:  {m['MAE']:.4f}")

    print(f"\n  Training samples: {metrics['train_samples']:,}")
    print(f"  Test samples:     {metrics['test_samples']:,}")
    print(f"  Features:         {metrics['feature_count']:,}")

    print(f"\n  Top 15 Features by Importance:\n  {'-' * 40}")
    for _, row in imp.head(15).iterrows():
        bar = "#" * int(row["importance"] * 200)
        print(f"  {row['feature']:<35s} {row['importance']:.4f} {bar}")

    # Example prediction
    movies_example = load_movies()
    if "Toy Story (1995)" in movies_example["title"].values:
        toy_story = movies_example[movies_example["title"] == "Toy Story (1995)"].iloc[
            0
        ]
        tag_pivot = load_tags(top_k=100)
        pred = predict_rating(
            toy_story,
            result["best_model"],
            result["scaler"],
            result["feature_cols"],
            result["num_cols"],
            tag_pivot=tag_pivot,
            rating_count=50.0,
        )
        print(f"\n{'=' * 55}")
        print("  Example: Toy Story (1995)")
        print(f"  Predicted avg rating: {pred:.2f} / 5.0")
        print(f"{'=' * 55}")

    # Improvement over baseline
    print("\n  Baseline (genre + year + count):     R^2 ~0.078")
    rf_r2 = metrics.get("RandomForest", {}).get("R2", 0)
    xgb_r2 = metrics.get("XGBoost", {}).get("R2", 0)
    best_r2 = max(rf_r2, xgb_r2)
    print(f"  Improved (tags + tuning + more features): R^2 ~{best_r2:.4f}")
    if best_r2 > 0.08:
        print(f"  Improvement: +{(best_r2 - 0.078) * 100:.1f}% explained variance")


if __name__ == "__main__":
    main()
