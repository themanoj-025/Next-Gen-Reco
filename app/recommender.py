"""
MovieLens Content-Based Recommendation Engine
==============================================
Recommends similar movies using a hybrid approach:
  - Genre cosine similarity (primary, computed on-the-fly)
  - Tag Jaccard similarity (computed on-demand)
  - Year proximity
  - Predicted rating boost (computed only for top candidates)

Usage:
    from recommender import MovieRecommender
    rec = MovieRecommender()
    recommendations = rec.recommend(movie_id=1, n=10)
"""

import re
import warnings
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

from app._paths import CACHE_DIR, DATA_DIR, PROJECT_ROOT
from app.enrichment import NDEnrichment
from app.model import load_model, load_movies, load_tags, predict_rating

_LOG_PREFIX = "[Recommender]"

# ── Cache helpers ─────────────────────────────────────────────────────────────

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


# ── Recommender Class ─────────────────────────────────────────────────────────


class MovieRecommender:
    """Content-based movie recommender using hybrid similarity scoring.

    Performance: genre similarity is computed on-the-fly (fast, ~20 columns).
    Tag similarity is Jaccard on-demand for top candidates only.
    Rating predictions only computed for top candidates.
    """

    def __init__(
        self,
        model_name: str = "v1_test",
        model_dir: str | None = None,
        top_tags: int = 100,
    ):
        if model_dir is None:
            model_dir = str(PROJECT_ROOT / "models")
        # Load movies — load_movies() already computes year, genre_list, etc.
        self.movies = load_movies()
        self.movies["year"] = self.movies["year"].fillna(0).astype(float)

        # Try loading genre vectors from cache
        movies_csv_path = str(DATA_DIR / "movies.csv")
        if _check_cache_valid(_GENRE_CACHE_PATH, movies_csv_path):
            try:
                data = np.load(_GENRE_CACHE_PATH, allow_pickle=True)
                self._genre_vectors = data["vectors"]
                self._genre_norms = data["norms"]
                self.genre_cols = list(data["cols"])
                # Rebuild genre_dummies from vectors (needed by some methods)
                self.genre_dummies = pd.DataFrame(
                    self._genre_vectors,
                    columns=self.genre_cols,
                    index=self.movies.index,
                ).astype(int)
                print(
                    f"{_LOG_PREFIX} Loaded genre vectors from cache ({len(self.genre_cols)} cols)"
                )
            except Exception as e:
                print(f"{_LOG_PREFIX} Genre cache load failed ({e}), rebuilding")
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
            print(f"{_LOG_PREFIX} Model not found. Predictions will be basic.")
        except Exception as e:
            print(
                f"{_LOG_PREFIX} Model failed to load ({e}). Predictions will be basic."
            )

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
                print(
                    f"{_LOG_PREFIX} ND enrichment loaded: {n_meta} metadata, {n_cast} cast, {n_rev} review sets"
                )
                print(f"{_LOG_PREFIX}   {n_dir} directors, {n_act} actors indexed")
            else:
                print(f"{_LOG_PREFIX} ND enrichment loaded but no data matched")
                self.enrichment = None
        except Exception as e:
            print(f"{_LOG_PREFIX} ND enrichment failed to load: {e}")
            self.enrichment = None

        # Build movie lookup by ID
        self.movies_by_id: dict[int, pd.Series] = {
            row["movieId"]: row for _, row in self.movies.iterrows()
        }

        # Year stats for year proximity scoring
        years = self.movies["year"]
        self.year_mean = years.mean()
        self.year_std = max(years.std(), 1.0)

    def _build_genre_vectors(self):
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
                cols=np.array(self.genre_cols, dtype=object),
            )
            print(f"{_LOG_PREFIX} Saved genre vectors to cache")
        except Exception as e:
            print(f"{_LOG_PREFIX} Warning: could not save genre cache ({e})")

    def _build_tag_lookup(self):
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

    def _precompute_title_tokens(self):
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
        except Exception:
            return None

    @lru_cache(maxsize=2048)
    def _predict_cached(self, movie_id_key: int) -> float | None:
        """Cached prediction by movie ID. The key is movieId.

        We pass movieId as the argument (not the full row) so
        lru_cache can hash it. The actual row is looked up internally.
        """
        if self.model_result is None:
            return None
        try:
            row = self.movies_by_id.get(movie_id_key)
            if row is None:
                return None
            return predict_rating(
                row,
                self.model_result["best_model"],
                self.model_result["scaler"],
                self.model_result["feature_cols"],
                self.model_result["num_cols"],
                tag_pivot=self.tag_pivot,
                rating_count=50.0,
            )
        except Exception:
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
            mask &= self.movies["genres"].str.contains(
                genre_filter, na=False, regex=False
            )

        if year_min or year_max:
            yr = self.movies["year"]
            valid_year = yr > 0
            if year_min:
                mask &= valid_year & (yr >= year_min)
            if year_max:
                mask &= valid_year & (yr <= year_max)

        return self.movies[mask]

    def _exact_search(self, q_lower: str) -> list[tuple[float, int]]:
        """Fast path: check for exact matches using pandas vectorized string ops."""
        # Exact match
        exact_mask = self.movies["title"].str.lower() == q_lower
        if exact_mask.any():
            return [
                (100.0, row["movieId"]) for _, row in self.movies[exact_mask].iterrows()
            ]

        # Starts with
        start_mask = self.movies["title"].str.lower().str.startswith(q_lower)
        if start_mask.any():
            return [
                (80.0, row["movieId"]) for _, row in self.movies[start_mask].iterrows()
            ]

        # Contains
        contains_mask = (
            self.movies["title"]
            .str.lower()
            .str.contains(q_lower, na=False, regex=False)
        )
        if contains_mask.any():
            candidates = self.movies[contains_mask]
            scored = []
            for _, row in candidates.iterrows():
                title_lower = str(row["title"]).lower()
                score = 60.0 + (1.0 - len(title_lower) / 200.0) * 10.0
                scored.append((score, row["movieId"]))
            return scored

        return []  # No quick matches — fall through to full scoring

    def search_movies_advanced(
        self,
        query: str,
        limit: int = 20,
        genre_filter: str | None = None,
        year_min: int | None = None,
        year_max: int | None = None,
        rating_min: float | None = None,
    ) -> list[dict[str, Any]]:
        """Advanced search with token-based scoring, fuzzy fallback,
        acronym matching, and optional filters (genre, year range, rating).

        Performance: uses pandas vectorized ops for pre-filtering before
        the Python scoring loop. Exact/substring matches are handled via
        fast vectorized path. Full scoring only runs on remaining candidates.

        Ranking (higher is better):
          1. Exact title match (1:1)
          2. All query words appear in title (in any order)
          3. Some query words match title tokens
          4. Acronym match (e.g. "TS" -> "Toy Story")
          5. Fuzzy / edit-distance fallback for typos
        """
        q = query.strip()
        if not q or len(q) < 2:
            return []

        q_lower = q.lower()
        q_tokens = self._tokenize(q)

        # ── Step 1: Vectorized pre-filter ────────────────────────────────
        filtered = self._prefilter_movies(genre_filter, year_min, year_max)
        if len(filtered) == 0:
            return []

        # ── Step 2: Fast exact / substring path ──────────────────────────
        has_filters = bool(genre_filter or year_min or year_max)

        if not has_filters:
            # Try fast vectorized exact/starts-with/contains
            fast_results = self._exact_search(q_lower)
            if fast_results:
                # Sort by score desc, then year
                fast_results.sort(
                    key=lambda x: (-x[0], -self.movies_by_id[x[1]].get("year", 0))
                )
                results = []
                for s, mid in fast_results[:limit]:
                    info = self.get_movie_info(mid)
                    if info:
                        if rating_min is not None and (
                            info["predicted_rating"] is None
                            or info["predicted_rating"] < rating_min
                        ):
                            continue
                        info["_search_score"] = s
                        results.append(info)
                        if len(results) >= limit:
                            break
                return results

        # ── Step 3: Full scoring on filtered set ─────────────────────────
        # Quick bail-out: check if ANY movie contains the query at all
        q_first_word = q_tokens[0] if q_tokens else q_lower
        any_match_mask = (
            filtered["title"]
            .str.lower()
            .str.contains(q_first_word, na=False, regex=False)
        )
        if not any_match_mask.any():
            # No movie contains even the first query word — return empty fast
            return []

        # Limit to most popular movies (by rating_count) when no filters applied
        if not has_filters and "rating_count" in filtered.columns:
            filtered = filtered.nlargest(min(20000, len(filtered)), "rating_count")
        elif len(filtered) > 30000:
            filtered = filtered.head(30000)

        scored: list[tuple[float, int]] = []

        # Pre-compute lowercase titles for the filtered set
        title_cache = {}
        for _, row in filtered.iterrows():
            mid = row["movieId"]
            title_cache[mid] = str(row["title"])

        for mid, title in title_cache.items():
            title_lower = title.lower()
            score = 0.0

            # 1. Exact match (case-insensitive)
            if q_lower == title_lower:
                score = 100.0
            # 2. Title starts with query
            elif title_lower.startswith(q_lower):
                score = 80.0
            # 3. Query is contained in title
            elif q_lower in title_lower:
                score = 60.0 + (1.0 - len(title_lower) / 200.0) * 10.0
            # 4. Token-based: all query words present in title (any order)
            elif q_tokens:
                title_tokens = self._tokenize(title)
                matched = sum(
                    1
                    for t in q_tokens
                    if any(t == tt or tt.startswith(t) for tt in title_tokens)
                )
                if matched == len(q_tokens):
                    title_token_set = set(title_tokens)
                    query_token_set = set(q_tokens)
                    overlap = len(title_token_set & query_token_set)
                    score = 50.0 + overlap * 5.0
                elif matched > 0:
                    score = 20.0 + matched * 8.0

            # 5. Acronym match
            if score < 30.0 and len(q) >= 2 and len(q) <= 6:
                q_upper = q.upper()
                acronym = "".join(
                    w[0].upper() for w in title.split() if w[0].isalpha() and len(w) > 1
                )
                if acronym and (acronym == q_upper or acronym.startswith(q_upper)):
                    score = max(score, 45.0)

            # 6. Partial word match
            if score < 20.0 and len(q) >= 3:
                title_words = re.split(r"[\s\W]+", title_lower)
                for word in title_words:
                    if len(word) >= len(q) and word.startswith(q_lower):
                        score = max(score, 15.0)
                        break
                    if len(q) >= len(word) + 2 and q_lower.startswith(word):
                        score = max(score, 12.0)
                        break

            # 7. Fuzzy / edit-distance fallback for typos
            if score < 10.0 and len(q) >= 4:
                dist = self._query_edit_distance(q, title)
                max_dist = max(2, len(q) // 3)
                if dist <= max_dist:
                    score = max(score, 8.0 - dist * 1.5)

            if score > 0:
                scored.append((score, mid))

        # Sort by score descending, then by year descending
        scored.sort(key=lambda x: (-x[0], -self.movies_by_id[x[1]].get("year", 0)))

        # Apply rating_min filter after scoring
        results = []
        for s, mid in scored[:limit]:
            info = self.get_movie_info(mid)
            if info:
                if rating_min is not None and (
                    info["predicted_rating"] is None
                    or info["predicted_rating"] < rating_min
                ):
                    continue
                info["_search_score"] = s
                results.append(info)
                if len(results) >= limit:
                    break

        return results

    def search_suggestions(self, query: str) -> list[str]:
        """Generate 'Did you mean?' suggestions for a failed query.

        Uses token-level matching and fuzzy distance to find close titles.
        Only checks a sample of movies (most popular by rating_count) to
        keep it fast.
        """
        q = query.strip().lower()
        if len(q) < 3:
            return []

        q_tokens = self._tokenize(q)
        suggestions: list[tuple[float, str]] = []

        # Only check most popular movies for suggestions (faster)
        candidates = (
            self.movies.nlargest(3000, "rating_count")
            if "rating_count" in self.movies.columns
            else self.movies.head(3000)
        )

        for _, row in candidates.iterrows():
            title = str(row["title"])
            title.lower()

            # Check for token overlap (some words match)
            title_tokens = self._tokenize(title)
            common = sum(
                1
                for t in q_tokens
                if any(
                    t == tt or tt.startswith(t) or t.startswith(tt)
                    for tt in title_tokens
                )
            )
            if common > 0 and common < len(q_tokens):
                score = common / len(q_tokens) * 50.0
            else:
                # Check edit distance
                dist = self._query_edit_distance(q, title)
                max_dist = max(2, len(q) // 3)
                if dist <= max_dist:
                    score = max(0, 30.0 - dist * 5.0)
                else:
                    continue

            suggestions.append((score, title))

        suggestions.sort(key=lambda x: -x[0])
        seen = set()
        uniq = []
        for _, title in suggestions:
            if title not in seen:
                seen.add(title)
                uniq.append(title)
                if len(uniq) >= 3:
                    break
        return uniq

    def search_movies(self, query: str, limit: int = 50) -> list[dict[str, Any]]:
        """Search movies by title keyword (fast string matching).

        Uses token-based matching for better relevance. Falls back to
        the legacy substring method for backward compatibility.
        """
        q = query.lower().strip()
        if not q or len(q) < 2:
            return []

        # Try advanced search first
        advanced = self.search_movies_advanced(query, limit=limit)
        if advanced:
            return advanced

        return []

    def recommend(
        self,
        movie_id: int,
        n: int = 12,
        genre_weight: float = 0.50,
        tag_weight: float = 0.20,
        year_weight: float = 0.10,
        rating_weight: float = 0.20,
        diversify: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Recommend similar movies using hybrid scoring.

        Performance:
        - Genre similarity: vectorized O(N) dot product (very fast)
        - Tag similarity: computed on-demand for top candidates only
        - Rating predictions: computed on-demand for top candidates only

        Parameters
        ----------
        movie_id : int
            Movie to find recommendations for.
        n : int
            Number of recommendations to return.
        genre_weight, tag_weight, year_weight, rating_weight : float
            Weights for each similarity component.
        diversify : bool
            If True, penalize over-similar genre matches.

        Returns
        -------
        list of dicts
        """
        idx = self._get_movie_idx(movie_id)
        if idx is None:
            return []

        movie_row = self.movies_by_id[movie_id]
        n_candidates = max(n * 10, 200)

        # ── Fast pass: compute genre + year scores (vectorized, all movies) ───
        genre_scores = self._genre_similarity_to(movie_id)

        # Year proximity (vectorized)
        year_scores = np.zeros(len(self.movies), dtype=np.float32)
        target_year = movie_row["year"]
        if target_year and target_year > 0:
            years = self.movies["year"].values
            year_diff = np.abs(years - target_year)
            year_scores = np.exp(-0.5 * (year_diff / 15.0) ** 2)

        # Quick hybrid (genre + year only) to pre-filter
        quick_score = genre_weight * genre_scores + year_weight * year_scores
        quick_score[idx] = -1.0  # exclude self

        # Get top candidates
        candidate_indices = np.argsort(quick_score)[::-1][:n_candidates]

        # ── For candidates only: compute tag + rating scores ──────────────
        candidate_scores = []
        for ci in candidate_indices:
            other_row = self.movies.iloc[ci]
            other_id = other_row["movieId"]

            # Tag similarity (Jaccard, on-demand)
            tag_sim = 0.0
            if tag_weight > 0 and len(self._tag_lookup) > 0:
                tag_sim = self._jaccard_similarity(movie_id, other_id)

            # Predicted rating (only for final scoring)
            pred = None
            rating_score = 0.0
            if rating_weight > 0:
                pred = self._predict_rating_safe(other_row)
                rating_score = (pred - 0.5) / 4.5 if pred is not None else 0.0

            # Full hybrid score
            hybrid = (
                genre_weight * float(genre_scores[ci])
                + tag_weight * tag_sim
                + year_weight * float(year_scores[ci])
                + rating_weight * rating_score
            )

            # Diversity penalty
            if diversify:
                overlap = float(genre_scores[ci])
                hybrid *= 1.0 - 0.25 * overlap

            candidate_scores.append(
                (
                    hybrid,
                    ci,
                    other_row,
                    other_id,
                    tag_sim,
                    float(genre_scores[ci]),
                    float(year_scores[ci]),
                    pred,
                )
            )

        # Sort by hybrid score
        candidate_scores.sort(key=lambda x: x[0], reverse=True)

        results = []
        for (
            hybrid,
            ci,
            other_row,
            other_id,
            tag_sim,
            g_sim,
            y_sim,
            pred,
        ) in candidate_scores[:n]:
            results.append(
                {
                    "movieId": int(other_id),
                    "title": other_row["title"],
                    "year": int(other_row["year"]) if other_row["year"] else None,
                    "genres": other_row["genre_list"],
                    "genres_str": other_row["genres"],
                    "similarity": float(round(hybrid, 4)),
                    "predicted_rating": pred,
                    "genre_similarity": float(round(g_sim, 4)),
                    "tag_similarity": float(round(tag_sim, 4)),
                    "year_proximity": float(round(y_sim, 4)),
                }
            )

        return results

    # ── New Feature: Get Movies by Decade ────────────────────────────────

    def get_movies_by_decade(
        self,
        decade: int,
        min_rating_count: int = 50,
        limit: int = 20,
    ) -> dict:
        """Get top movies from a specific decade (e.g. 1990s).

        Returns a dict with:
          - decade: int
          - count: total movies from that decade
          - top_movies: list of movie info dicts sorted by predicted rating
          - genre_distribution: dict of genre -> count
          - decade_label: str like "1990s"
        """
        dec_start = decade
        dec_end = decade + 9

        mask = (
            (self.movies["year"] >= dec_start)
            & (self.movies["year"] <= dec_end)
            & (self.movies["year"] > 0)
        )
        decade_movies = self.movies[mask].copy()

        # Genre distribution
        genre_dist: dict[str, int] = {}
        for glist in decade_movies["genre_list"]:
            for g in glist:
                genre_dist[g] = genre_dist.get(g, 0) + 1

        # Sort genre dist
        genre_dist = dict(sorted(genre_dist.items(), key=lambda x: -x[1])[:15])

        # Predict for most popular movies
        if "rating_count" in decade_movies.columns:
            candidates = decade_movies.nlargest(
                min(500, len(decade_movies)), "rating_count"
            )
        else:
            candidates = decade_movies.head(500)

        scored = []
        for _, row in candidates.iterrows():
            mid = row["movieId"]
            pred = self._predict_cached(mid)
            if pred is not None:
                scored.append((pred, mid))

        scored.sort(key=lambda x: x[0], reverse=True)

        top_movies = []
        for pred, mid in scored[:limit]:
            info = self.get_movie_info(mid)
            if info:
                info["predicted_rating"] = pred
                # Enrich with ND data
                info = self.enrich_movie_info(info)
                top_movies.append(info)

        return {
            "decade": decade,
            "decade_label": f"{decade}s",
            "count": len(decade_movies),
            "top_movies": top_movies,
            "genre_distribution": genre_dist,
        }

    # ── New Feature: Combo Finder ────────────────────────────────────────

    def find_movies_combo(
        self,
        *,
        genre: str | None = None,
        year_min: int | None = None,
        year_max: int | None = None,
        director: str | None = None,
        actor: str | None = None,
        rating_min: float | None = None,
        sort_by: str = "predicted_rating",  # "predicted_rating", "year", "popularity"
        limit: int = 20,
    ) -> list[dict]:
        """Advanced multi-criteria movie search combining filters.

        Parameters can be combined arbitrarily — e.g.
        genre="Action", year_min=1990, year_max=1999, director="James Cameron"

        Returns list of movie info dicts matching ALL criteria.
        """
        # Start with all movies
        mask = pd.Series([True] * len(self.movies), index=self.movies.index)

        # Genre filter (vectorized)
        if genre:
            mask &= self.movies["genres"].str.contains(genre, na=False, regex=False)

        # Year filter
        yr = self.movies["year"]
        valid_year = yr > 0
        if year_min:
            mask &= valid_year & (yr >= year_min)
        if year_max:
            mask &= valid_year & (yr <= year_max)

        filtered = self.movies[mask]

        if len(filtered) == 0:
            return []

        # Apply ND enrichment filters (director/actor)
        if director or actor:
            enrichment_filtered = []
            for _, row in filtered.iterrows():
                mid = row["movieId"]
                enrich = self.get_enriched_cast(mid)
                if enrich is None:
                    continue
                if director and enrich.get("director", "").lower() != director.lower():
                    continue
                if actor:
                    actor_lower = actor.lower()
                    if not any(
                        actor_lower == a.lower() for a in enrich.get("actors", [])
                    ):
                        continue
                enrichment_filtered.append(mid)
            filtered = filtered[filtered["movieId"].isin(enrichment_filtered)]
            if len(filtered) == 0:
                return []

        # Predict ratings for top candidates
        if "rating_count" in filtered.columns:
            candidates = filtered.nlargest(min(500, len(filtered)), "rating_count")
        else:
            candidates = filtered.head(500)

        scored = []
        for _, row in candidates.iterrows():
            mid = row["movieId"]
            pred = self._predict_cached(mid)
            if pred is not None:
                if rating_min is not None and pred < rating_min:
                    continue
                info = self.get_movie_info(mid)
                if info:
                    info["predicted_rating"] = pred
                    info = self.enrich_movie_info(info)
                    scored.append(info)

        # Sort
        if sort_by == "year":
            scored.sort(key=lambda x: x.get("year", 0) or 0, reverse=True)
        elif sort_by == "popularity":
            scored.sort(key=lambda x: x.get("popularity", 0) or 0, reverse=True)
        else:  # predicted_rating
            scored.sort(key=lambda x: x.get("predicted_rating", 0) or 0, reverse=True)

        return scored[:limit]

    # ── New Feature: Movie Night Generator ───────────────────────────────

    def movie_night_generator(
        self,
        *,
        genre: str | None = None,
        max_runtime_minutes: int = 240,
        movie_count: int = 3,
        min_year: int = 1990,
        max_year: int = 2026,
        prefer_action: bool = False,
    ) -> list[dict]:
        """Generate a movie marathon lineup.

        Picks movies that fit within the total runtime budget and match
        the requested criteria.

        Parameters
        ----------
        genre : str, optional
            Preferred genre for all movies.
        max_runtime_minutes : int
            Total runtime budget for all movies combined.
        movie_count : int
            Number of movies to include (1-5).
        min_year, max_year : int
            Year range for movies.
        prefer_action : bool
            If True, favors higher-energy/action movies.

        Returns
        -------
        list of movie info dicts, up to movie_count items.
        """
        movie_count = min(max(movie_count, 1), 5)

        # Filter movies
        mask = (
            (self.movies["year"] >= min_year)
            & (self.movies["year"] <= max_year)
            & (self.movies["year"] > 0)
        )

        if genre:
            # Use regex mode so pipe-delimited genres like "Action|Thriller" match individual genres
            mask &= self.movies["genres"].str.contains(genre, na=False, regex=True)

        candidates = self.movies[mask]

        if len(candidates) == 0:
            return []

        # Get runtime data from ND enrichment where available,
        # otherwise use a default estimate
        scored = []
        for _, row in candidates.iterrows():
            mid = row["movieId"]
            pred = self._predict_cached(mid)
            if pred is None:
                continue

            # Try to get runtime from enrichment
            meta = self.get_enriched_metadata(mid)
            runtime = None
            if meta:
                runtime = meta.get("runtime")

            scored.append(
                {
                    "movie_id": mid,
                    "predicted_rating": pred,
                    "runtime": runtime,
                    "title": row["title"],
                    "year": int(row["year"]) if row["year"] else 0,
                    "genres": row["genre_list"],
                }
            )

        if not scored:
            return []

        # Sort by predicted rating
        scored.sort(key=lambda x: x["predicted_rating"], reverse=True)

        # Greedy knapsack-style selection: pick best movies that fit
        selected = []
        remaining_budget = max_runtime_minutes

        for movie in scored:
            if len(selected) >= movie_count:
                break

            runtime = movie["runtime"]
            if runtime and runtime > 0:
                if runtime <= remaining_budget:
                    selected.append(movie)
                    remaining_budget -= runtime
            else:
                # If no runtime data, assume ~120 min and pick anyway
                if remaining_budget >= 90:
                    selected.append(movie)
                    remaining_budget -= 120
                elif len(selected) < movie_count:
                    # Pick it even if we don't know the runtime
                    selected.append(movie)

        # Build result
        results = []
        for movie in selected:
            info = self.get_movie_info(movie["movie_id"])
            if info:
                info["predicted_rating"] = movie["predicted_rating"]
                info = self.enrich_movie_info(info)
                results.append(info)

        return results

    # ── New Feature: Enhanced Movie Stats ────────────────────────────────

    def get_movie_stats(self, movie_id: int) -> dict:
        """Get interesting stats and trivia for a movie."""
        info = self.get_movie_info(movie_id)
        if info is None:
            return {}

        info = self.enrich_movie_info(info)
        stats = {
            "title": info["title"],
            "year": info.get("year"),
            "genres": info.get("genres", []),
            "predicted_rating": info.get("predicted_rating"),
        }

        # Budget / Revenue stats
        budget = info.get("budget")
        revenue = info.get("revenue")
        if budget and budget > 0 and revenue and revenue > 0:
            stats["roi"] = revenue / budget
            stats["profit"] = revenue - budget
        if budget and budget > 0:
            stats["budget"] = budget
        if revenue and revenue > 0:
            stats["revenue"] = revenue

        # Runtime stats
        runtime = info.get("runtime")
        if runtime and runtime > 0:
            stats["runtime"] = runtime
            # Compare to average
            avg_runtime = self.movies_with_runtime_avg()
            if avg_runtime:
                diff = runtime - avg_runtime
                stats["runtime_diff"] = int(diff)

        # Popularity percentile (from enrichment data — compare against known values)
        popularity = info.get("popularity")
        if popularity and popularity > 0 and self.enrichment is not None:
            # Compute percentile against all TMDB-enriched popularities
            all_popularities = [
                m.get("popularity", 0)
                for m in self.enrichment._metadata_map.values()
                if m.get("popularity") and m["popularity"] > 0
            ]
            if all_popularities:
                pct = (
                    sum(1 for p in all_popularities if p < popularity)
                    / len(all_popularities)
                ) * 100
                stats["popularity_percentile"] = round(pct, 1)

        # Vote average from TMDB
        vote_avg = info.get("vote_average")
        if vote_avg:
            stats["vote_average"] = vote_avg

        # Genre count (rarity)
        genre_count = len(info.get("genres", []))
        stats["genre_count"] = genre_count
        avg_genre_count = self.movies["genre_list"].apply(len).mean()
        stats["genre_count_vs_avg"] = round(genre_count - avg_genre_count, 1)

        # Director info
        director = info.get("director", "")
        if director:
            dir_movies = self.get_movies_by_director(director)
            stats["director"] = director
            stats["director_movie_count"] = len(dir_movies)

        return stats

    def movies_with_runtime_avg(self) -> float | None:
        """Get average runtime across all movies with ND enrichment data.

        Cached on first call for performance.
        """
        if self.enrichment is None:
            return None
        if hasattr(self, "_avg_runtime_cache"):
            return self._avg_runtime_cache
        runtimes = []
        for meta in self.enrichment._metadata_map.values():
            if meta.get("runtime") and meta["runtime"] > 0:
                runtimes.append(meta["runtime"])
        if runtimes:
            self._avg_runtime_cache = sum(runtimes) / len(runtimes)
            return self._avg_runtime_cache
        self._avg_runtime_cache = None
        return None

    # ── ND enrichment methods ────────────────────────────────────────────

    def get_enriched_metadata(self, movie_id: int) -> dict[str, Any] | None:
        """Get TMDB-enriched metadata for a movie (overview, budget, runtime, etc.)."""
        if self.enrichment is None:
            return None
        return self.enrichment.get_metadata(movie_id)

    def get_enriched_cast(self, movie_id: int) -> dict[str, Any] | None:
        """Get director and actor info for a movie."""
        if self.enrichment is None:
            return None
        return self.enrichment.get_cast(movie_id)

    def get_enriched_reviews(self, movie_id: int) -> list[str] | None:
        """Get user review texts for a movie."""
        if self.enrichment is None:
            return None
        return self.enrichment.get_reviews(movie_id)

    def get_movies_by_director(self, director: str) -> list[int]:
        """Get list of movieIds directed by a given person."""
        if self.enrichment is None:
            return []
        return self.enrichment.get_movies_by_director(director)

    def get_movies_by_actor(self, actor: str) -> list[int]:
        """Get list of movieIds featuring a given actor."""
        if self.enrichment is None:
            return []
        return self.enrichment.get_movies_by_actor(actor)

    def enrich_movie_info(self, info: dict[str, Any]) -> dict[str, Any]:
        """Enrich movie info dict with ND folder data (metadata, cast, reviews)."""
        mid = info["movieId"]
        meta = self.get_enriched_metadata(mid)
        cast = self.get_enriched_cast(mid)
        reviews = self.get_enriched_reviews(mid)

        enriched = dict(info)
        if meta:
            enriched["overview"] = meta.get("overview", "")
            enriched["tagline"] = meta.get("tagline", "")
            enriched["runtime"] = meta.get("runtime")
            enriched["budget"] = meta.get("budget")
            enriched["revenue"] = meta.get("revenue")
            enriched["vote_average"] = meta.get("vote_average")
            enriched["popularity"] = meta.get("popularity")
            enriched["original_language"] = meta.get("original_language", "")
            enriched["keywords"] = meta.get("keywords", "")
            enriched["production_companies"] = meta.get("production_companies", "")
            enriched["release_date"] = meta.get("release_date", "")

        if cast:
            enriched["director"] = cast.get("director", "")
            enriched["actors"] = cast.get("actors", [])

        if reviews:
            enriched["user_reviews"] = reviews
            # Append review text to the overview/description so reviews show as part of description
            existing_overview = enriched.get("overview", "") or ""
            # Take first 10 unique reviews to keep it concise
            seen = set()
            unique_reviews = []
            for r in reviews:
                r_clean = r.strip()
                key = r_clean.lower()[:60]
                if key not in seen and len(unique_reviews) < 10:
                    seen.add(key)
                    unique_reviews.append(r_clean)
            if unique_reviews:
                review_section = (
                    "<br><br>📝 <strong>What users are saying:</strong><br>"
                    + "<br>".join(f"• \u201c{r}\u201d" for r in unique_reviews)
                )
                enriched["overview"] = existing_overview + review_section

        return enriched

    def get_feature_breakdown(self, movie_id: int) -> dict[str, Any] | None:
        """Get feature importance breakdown for a movie's prediction."""
        if movie_id not in self.movies_by_id or self.model_result is None:
            return None

        row = self.movies_by_id[movie_id]
        movie_info = self.get_movie_info(movie_id)
        if movie_info is None:
            return None

        pred = movie_info["predicted_rating"]
        if pred is None:
            return None

        try:
            explanation = self._explain_prediction(
                row,
                pred,
                self.model_result["best_model"],
                self.model_result["scaler"],
                self.model_result["feature_cols"],
                self.model_result["num_cols"],
                self.model_result["importance"],
            )
            return {"prediction": pred, "explanation": explanation}
        except Exception as e:
            return {"prediction": pred, "explanation": None, "error": str(e)}

    def _explain_prediction(
        self,
        movie_row: pd.Series,
        prediction: float,
        model,
        scaler,
        feature_cols: list[str],
        num_cols: list[str],
        importance_df: pd.DataFrame,
    ) -> str:
        """Build a feature-contribution explanation for a prediction."""
        present_num = [c for c in num_cols if c in feature_cols]
        genre_list = movie_row["genre_list"]

        def _build_raw() -> pd.DataFrame:
            f = pd.DataFrame([0.0] * len(feature_cols), index=feature_cols).T
            for g in genre_list:
                if g in f.columns:
                    f.at[0, g] = 1.0
            if self.tag_pivot is not None and len(self.tag_pivot) > 0:
                mt = self.tag_pivot[self.tag_pivot["movieId"] == movie_row["movieId"]]
                if len(mt) > 0:
                    for c in self.tag_pivot.columns:
                        if c != "movieId" and c in f.columns:
                            try:
                                f.at[0, c] = float(mt.iloc[0][c])
                            except (ValueError, KeyError):
                                pass
            f.at[0, "genre_count"] = len(genre_list)
            f.at[0, "title_length"] = len(str(movie_row.get("title", "")))
            f.at[0, "title_words"] = len(str(movie_row.get("title", "")).split())
            f.at[0, "rating_count"] = 50.0
            yv = movie_row.get("year", 2000)
            if pd.isna(yv) or yv == 0:
                yv = 2000
            f.at[0, "year"] = yv
            return f

        feats_raw = _build_raw()
        feats_scaled = feats_raw.copy()
        if present_num:
            feats_scaled[present_num] = scaler.transform(feats_scaled[present_num])

        full_pred = float(model.predict(feats_scaled)[0])

        contributions = []
        for feat_name in importance_df["feature"].head(30).tolist():
            if feat_name not in feats_raw.columns:
                continue
            is_active = abs(feats_raw.at[0, feat_name]) > 0.01
            if not is_active and feat_name not in present_num:
                continue
            feats_copy = feats_raw.copy()
            feats_copy.at[0, feat_name] = 0.0
            if feat_name in genre_list:
                feats_copy.at[0, "genre_count"] = max(
                    0, feats_raw.at[0, "genre_count"] - 1
                )
            if present_num:
                feats_copy[present_num] = scaler.transform(feats_copy[present_num])
            pred_without = float(model.predict(feats_copy)[0])
            effect = full_pred - pred_without
            contributions.append((feat_name, effect))

        contributions = [(n, v) for n, v in contributions if abs(v) > 0.001]
        contributions.sort(key=lambda x: abs(x[1]), reverse=True)

        lines = []
        lines.append(f"  Predicted rating: {prediction:.2f} / 5.0")
        lines.append("  Assumed rating count: 50")
        lines.append("")
        lines.append("  Top contributing features:")
        for feat_name, effect in contributions[:12]:
            display_name = feat_name.replace("tag_", "tag:")
            bar_len = min(int(abs(effect) / 0.5 * 30), 30)
            bar_str = "#" * bar_len + "." * (30 - bar_len)
            direction = "+" if effect > 0 else "-"
            lines.append(
                f"    {direction} {display_name:<30s} {bar_str}  {effect:+.4f}"
            )

        lines.append("")
        lines.append(f"    (Baseline prediction: {full_pred:.4f})")
        return "\n".join(lines)

    def get_top_picks(
        self,
        genre: str | None = None,
        n: int = 20,
        min_year: int = 1990,
    ) -> list[dict[str, Any]]:
        """Get top predicted picks globally or filtered by genre."""
        candidates = self.movies

        if genre:
            mask = candidates["genres"].str.contains(genre, na=False, case=False)
            candidates = candidates[mask]

        if min_year:
            candidates = candidates[candidates["year"] >= min_year]

        # Predict ratings for top candidates (max 500 for speed)
        # Sort by rating_count (popularity proxy) to get better samples
        candidates = (
            candidates.sort_values("rating_count", ascending=False)
            if "rating_count" in candidates.columns
            else candidates
        )
        sample = candidates.head(500)
        scored = []
        for _, row in sample.iterrows():
            mid = row["movieId"]
            pred = self._predict_cached(mid)
            if pred is not None:
                scored.append((pred, mid))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for pred, mid in scored[:n]:
            info = self.get_movie_info(mid)
            if info:
                results.append({**info, "predicted_rating": pred})

        return results


# ── Quick test ────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    print("Testing MovieRecommender...")
    rec = MovieRecommender()

    # Test search
    print("\n--- Search 'toy story' ---")
    results = rec.search_movies("toy story", limit=5)
    for r in results:
        print(f"  [{r['movieId']}] {r['title']}  (pred: {r['predicted_rating']})")

    if results:
        mid = results[0]["movieId"]
        print(f"\n--- Recommend for movie {mid} ---")
        recs = rec.recommend(mid, n=8)
        for r in recs:
            genres = ", ".join(r["genres"][:3])
            print(
                f"  [{r['movieId']}] {r['title']}  sim={r['similarity']:.3f}  pred={r['predicted_rating']}  [{genres}]"
            )

        print(f"\n--- Feature breakdown for {mid} ---")
        fb = rec.get_feature_breakdown(mid)
        if fb and fb.get("explanation"):
            print(fb["explanation"])
        else:
            print("  (not available)")

    print("\n[OK] Recommender test complete!")
