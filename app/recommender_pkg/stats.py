"""Recommender — Movie statistics mixin."""

from __future__ import annotations

from typing import Any


class StatsMixin:
    """Movie statistics and trivia."""

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
                    sum(1 for p in all_popularities if p < popularity) / len(all_popularities)
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
