"""Recommender — Search mixin: advanced search, suggestions."""

from __future__ import annotations

import re
from typing import Any

import numpy as np
import pandas as pd


class SearchMixin:
    """Search methods for movie discovery."""

    def _exact_search(self, q_lower: str) -> list[tuple[float, int]]:
        """Fast path: check for exact matches using pandas vectorized string ops."""
        # Exact match
        exact_mask = self.movies["title"].str.lower() == q_lower
        if exact_mask.any():
            return [(100.0, row["movieId"]) for _, row in self.movies[exact_mask].iterrows()]

        # Starts with
        start_mask = self.movies["title"].str.lower().str.startswith(q_lower)
        if start_mask.any():
            return [(80.0, row["movieId"]) for _, row in self.movies[start_mask].iterrows()]

        # Contains
        contains_mask = (
            self.movies["title"].str.lower().str.contains(q_lower, na=False, regex=False)
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
                fast_results.sort(key=lambda x: (-x[0], -self.movies_by_id[x[1]].get("year", 0)))
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
            filtered["title"].str.lower().str.contains(q_first_word, na=False, regex=False)
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
                    1 for t in q_tokens if any(t == tt or tt.startswith(t) for tt in title_tokens)
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
                    info["predicted_rating"] is None or info["predicted_rating"] < rating_min
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
                if any(t == tt or tt.startswith(t) or t.startswith(tt) for tt in title_tokens)
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
