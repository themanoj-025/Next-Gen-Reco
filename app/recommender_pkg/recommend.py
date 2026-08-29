"""Recommender — Core recommendation engine."""

from __future__ import annotations

from typing import Any

import numpy as np


class RecommendMixin:
    """Hybrid recommendation scoring."""

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
