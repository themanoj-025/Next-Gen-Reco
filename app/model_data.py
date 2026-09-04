"""
MovieLens Rating Predictor — ML Model (Improved)
=================================================
Random Forest + XGBoost regressors trained on MovieLens 32M dataset.
Features: genres (one-hot), tags (top 100), derived stats (genre count,
title length), rating_count, and release year.
"""

import os
import pickle
import re
import time
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

from app._paths import CACHE_DIR, DATA_DIR, MODELS_DIR
from app.utils import logger

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
            logger.info(f"  Loaded tag pivot from cache ({len(df)} rows)")
            return df
        except (OSError, ValueError, KeyError):
            pass

    tags = pd.read_csv(path, dtype={"userId": "int32", "movieId": "int32", "tag": "object"})

    # Find the top K most common tags overall
    top_tags = tags["tag"].str.lower().str.strip().value_counts().head(top_k).index.tolist()

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
    tag_pivot = tag_pivot.astype({c: "int8" for c in tag_pivot.columns if c != "movieId"})

    # Save to cache
    try:
        tag_pivot.to_pickle(cache_file)
        logger.info("  Saved tag pivot to cache")
    except (OSError, pickle.PicklingError) as e:
        logger.warning(f"  Warning: could not save tag cache ({e})")

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


