"""Recommender — Core: init, build vectors, similarity, movie info."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from app._paths import CACHE_DIR, DATA_DIR, PROJECT_ROOT
from app.enrichment import NDEnrichment
from app.model import load_model, load_movies, load_tags, predict_rating

_LOG_PREFIX = "[Recommender]"
logger = logging.getLogger(__name__)

# Cache paths
_CACHE_DIR = CACHE_DIR
_GENRE_CACHE_PATH = _CACHE_DIR / "genre_vectors.npz"
_MOVIES_CACHE_PATH = _CACHE_DIR / "movies_processed.parquet"


def _check_cache_valid(cache_path: Path, *source_paths: str | Path) -> bool:
    """Check if cache file is newer than all source files."""
    if not cache_path.exists():
        return False
    cache_mtime = cache_path.stat().st_mtime
    for sp in source_paths:
        p = Path(sp)
        if p.exists() and p.stat().st_mtime > cache_mtime:
            return False
    return True


# Module-level prediction cache
_predict_model_result: dict | None = None
_predict_movies_by_id: dict[int, pd.Series] = {}
_predict_tag_pivot: pd.DataFrame | None = None
_prediction_cache: dict[int, float | None] = {}


class CoreMixin:
    """Core methods: init, build, similarity, movie info."""

    def __init__(
        self,
        model_name: str = "v1_test",
        model_dir: str | None = None,
        top_tags: int = 100,
    ) -> None:
        if model_dir is None:
            model_dir = str(PROJECT_ROOT / "models")
        # Load movies — load_movies() already computes year, genre_list, etc.
        self.movies = load_movies()
        self.movies["year"] = self.movies["year"].fillna(0).astype(float)

        # Try loading genre vectors from cache
        movies_csv_path = str(DATA_DIR / "movies.csv")
        if _check_cache_valid(_GENRE_CACHE_PATH, movies_csv_path):
            try:
                data = np.load(_GENRE_CACHE_PATH, allow_pickle=False)
                self._genre_vectors = data["vectors"]
                self._genre_norms = data["norms"]
                self.genre_cols = [str(c) for c in data["cols"]]
                # Rebuild genre_dummies from vectors (needed by some methods)
                self.genre_dummies = pd.DataFrame(
                    self._genre_vectors,
                    columns=self.genre_cols,
                    index=self.movies.index,
                ).astype(int)
                logger.info(
                    "%s Loaded genre vectors from cache (%d cols)",
                    _LOG_PREFIX,
                    len(self.genre_cols),
                )
            except (OSError, ValueError, KeyError) as e:
                logger.warning("%s Genre cache load failed (%s), rebuilding", _LOG_PREFIX, e)
                self._build_genre_vectors()
        else:
            self._build_genre_vectors()

        # Load tags (for on-demand Jaccard similarity)
        self.top_tags = top_tags
        self.tag_pivot = load_tags(top_k=top_tags)

        if self.tag_pivot is not None and len(self.tag_pivot) > 0:
            self._build_tag_lookup()
        else:
            self._tag_lookup = {}
            self._tag_cols = []

        # Load model
        self.model_result = None
        self.model_name = model_name
        self.model_dir = model_dir
        try:
            self.model_result = load_model(name=model_name, dir_path=model_dir)
        except FileNotFoundError:
            logger.warning("%s Model not found. Predictions will be basic.", _LOG_PREFIX)
        except (OSError, ValueError, KeyError) as e:
            logger.error("%s Model failed to load (%s). Predictions will be basic.", _LOG_PREFIX, e)

        # Note: keeping tag_pivot for runtime predictions;

        # ── ND folder enrichment ─────────────────────────────────────
        try:
            self.enrichment = NDEnrichment(self.movies)
            if self.enrichment.is_loaded:
                n_meta = len(self.enrichment._metadata_map)
                n_cast = len(self.enrichment._cast_map)
                n_rev = len(self.enrichment._reviews_map)
                n_dir = len(self.enrichment._director_to_movies)
                n_act = len(self.enrichment._actor_to_movies)
                logger.info(
                    "%s ND enrichment loaded: %d metadata, %d cast, %d review sets",
                    _LOG_PREFIX,
                    n_meta,
                    n_cast,
                    n_rev,
                )
                logger.info("%s   %d directors, %d actors indexed", _LOG_PREFIX, n_dir, n_act)
            else:
                logger.warning("%s ND enrichment loaded but no data matched", _LOG_PREFIX)
                self.enrichment = None
        except (OSError, ValueError, KeyError) as e:
            logger.error("%s ND enrichment failed to load: %s", _LOG_PREFIX, e)
            self.enrichment = None

        # Build movie lookup by ID
        self.movies_by_id: dict[int, pd.Series] = {
            row["movieId"]: row for _, row in self.movies.iterrows()
        }

        # Year stats for year proximity scoring
        years = self.movies["year"]
        self.year_mean = years.mean()
        self.year_std = max(years.std(), 1.0)

        # Set module-level prediction cache data (avoids B019 memory leak)
        global _predict_model_result, _predict_movies_by_id, _predict_tag_pivot
        _predict_model_result = self.model_result
        _predict_movies_by_id = self.movies_by_id
        _predict_tag_pivot = self.tag_pivot
        _prediction_cache.clear()

    def _build_genre_vectors(self) -> None:
        """Build and cache genre one-hot matrix."""
        self.genre_dummies = self.movies["genres"].str.get_dummies(sep="|")
        if "(no genres listed)" in self.genre_dummies.columns:
            self.genre_dummies = self.genre_dummies.drop(columns=["(no genres listed)"])
        self.genre_cols = list(self.genre_dummies.columns)

        self._genre_vectors = self.genre_dummies.values.astype(np.float32)
        self._genre_norms = np.linalg.norm(self._genre_vectors, axis=1)
        self._genre_norms[self._genre_norms == 0] = 1.0

        # Save to cache
        try:
            _CACHE_DIR.mkdir(exist_ok=True)
            np.savez_compressed(
                _GENRE_CACHE_PATH,
                vectors=self._genre_vectors,
                norms=self._genre_norms,
                # Fixed-width unicode (not object dtype) so the cache loads
                # with allow_pickle=False — .npy object arrays require pickle.
                cols=np.array(self.genre_cols),
            )
            logger.info("%s Saved genre vectors to cache", _LOG_PREFIX)
        except (OSError, ValueError) as e:
            logger.warning("%s Warning: could not save genre cache (%s)", _LOG_PREFIX, e)

    def _build_tag_lookup(self) -> None:
        """Build a fast tag lookup: movieId -> set of tag column indices."""
        tag_cols = [c for c in self.tag_pivot.columns if c != "movieId"]
        self._tag_cols = tag_cols

        self._tag_lookup: dict[int, set[int]] = {}
        for _, row in self.tag_pivot.iterrows():
            mid = int(row["movieId"])
            tags = set()
            for j, col in enumerate(tag_cols):
                if row[col] > 0:
                    tags.add(j)
            if tags:
                self._tag_lookup[mid] = tags

    def _precompute_title_tokens(self) -> None:
        """Precompute lowercase tokens for every movie title for fast search."""
        titles = self.movies["title"].str.lower()
        self._title_tokens = titles.str.split(r"[\s\W]+")
        self._title_tokens.index = range(len(self._title_tokens))

    def _normalize_title(self, title: str) -> str:
        """Normalize a movie title for matching: lowercase, remove punctuation."""
        return re.sub(r"[^a-z0-9\s]", "", title.lower().strip())

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into words, filtering short tokens."""
        return [t for t in re.split(r"[\s\W]+", text.lower().strip()) if len(t) >= 2]

    def _query_edit_distance(self, query: str, title: str) -> int:
        """Compute Levenshtein distance between query and title start.

        Only considers the first len(query) characters of the title for
        a lightweight fuzzy match. Normalizes both first.
        """
        q = self._normalize_title(query)[:20]
        t = self._normalize_title(title)[: len(q) + 3]
        if not q or not t:
            return 99

        # Simple Levenshtein
        n, m = len(q), len(t)
        dp = list(range(m + 1))
        for i in range(1, n + 1):
            prev = dp[0]
            dp[0] = i
            for j in range(1, m + 1):
                temp = dp[j]
                cost = 0 if q[i - 1] == t[j - 1] else 1
                dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + cost)
                prev = temp
        return dp[m]

    def _genre_similarity_to(self, movie_id: int) -> np.ndarray:
        """Compute cosine similarity between a movie and all others.

        Efficient: vectorized dot product over the genre matrix.
        Returns array of shape (n_movies,) with similarity scores.
        """
        idx = self._get_movie_idx(movie_id)
        if idx is None:
            return np.zeros(len(self.movies), dtype=np.float32)

        target_vec = self._genre_vectors[idx]
        # Cosine similarity: dot / (norm1 * norm2)
        dots = self._genre_vectors @ target_vec
        sim = dots / (self._genre_norms * self._genre_norms[idx])
        return sim.astype(np.float32)

    def _jaccard_similarity(self, mid1: int, mid2: int) -> float:
        """Compute Jaccard similarity for two movie IDs using their tags."""
        tags1 = self._tag_lookup.get(mid1)
        tags2 = self._tag_lookup.get(mid2)
        if not tags1 or not tags2:
            return 0.0
        intersection = len(tags1 & tags2)
        union = len(tags1 | tags2)
        return intersection / union if union > 0 else 0.0

    def _get_movie_idx(self, movie_id: int) -> int | None:
        """Get matrix index for a movieId."""
        idx = self.movies.index[self.movies["movieId"] == movie_id].tolist()
        return idx[0] if idx else None

    def _predict_rating_safe(self, movie_row: pd.Series) -> float | None:
        """Predict rating with error handling. Results cached via LRU."""
        if self.model_result is None:
            return None
        try:
            mid = int(movie_row["movieId"])
            return self._predict_cached(mid)
        except (ValueError, KeyError, TypeError):
            return None

    @staticmethod
    def _predict_cached(movie_id_key: int) -> float | None:
        """Cached prediction by movie ID. Uses module-level dict cache."""
        if movie_id_key in _prediction_cache:
            return _prediction_cache[movie_id_key]
        if _predict_model_result is None:
            _prediction_cache[movie_id_key] = None
            return None
        try:
            row = _predict_movies_by_id.get(movie_id_key)
            if row is None:
                _prediction_cache[movie_id_key] = None
                return None
            result = predict_rating(
                row,
                _predict_model_result["best_model"],
                _predict_model_result["scaler"],
                _predict_model_result["feature_cols"],
                _predict_model_result["num_cols"],
                tag_pivot=_predict_tag_pivot,
                rating_count=50.0,
            )
            _prediction_cache[movie_id_key] = result
            return result
        except (ValueError, KeyError, TypeError):
            _prediction_cache[movie_id_key] = None
            return None

    def get_movie_info(self, movie_id: int) -> dict[str, Any] | None:
        """Get detailed info about a movie including predicted rating."""
        if movie_id not in self.movies_by_id:
            return None

        row = self.movies_by_id[movie_id]
        pred = self._predict_rating_safe(row)

        return {
            "movieId": movie_id,
            "title": row["title"],
            "year": int(row["year"]) if row["year"] else None,
            "genres": row["genre_list"],
            "genres_str": row["genres"],
            "predicted_rating": pred,
        }

    def _prefilter_movies(
        self,
        genre_filter: str | None = None,
        year_min: int | None = None,
        year_max: int | None = None,
    ) -> pd.DataFrame:
        """Pre-filter movies using vectorized pandas operations.

        Returns a filtered DataFrame with only matching rows. This is much
        faster than iterating all 87K rows and checking conditions in Python.
        """
        mask = pd.Series([True] * len(self.movies), index=self.movies.index)

        if genre_filter:
            mask &= self.movies["genres"].str.contains(genre_filter, na=False, regex=False)

        if year_min or year_max:
            yr = self.movies["year"]
            valid_year = yr > 0
            if year_min:
                mask &= valid_year & (yr >= year_min)
            if year_max:
                mask &= valid_year & (yr <= year_max)

        return self.movies[mask]
