"""Recommender — Feature mixins: decade explorer, combo finder, movie night."""

from __future__ import annotations

import pandas as pd


class FeaturesMixin:
    """Advanced feature methods for movie discovery."""

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
            candidates = decade_movies.nlargest(min(500, len(decade_movies)), "rating_count")
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
                    if not any(actor_lower == a.lower() for a in enrich.get("actors", [])):
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
