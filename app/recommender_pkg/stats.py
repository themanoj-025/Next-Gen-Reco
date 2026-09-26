"""Recommender — Movie statistics mixin."""

from __future__ import annotations

from typing import Any, cast

from app.recommender_pkg.core import CoreMixin


class StatsMixin:
    """Movie statistics and trivia."""

    # Attributes provided by CoreMixin (RMR) — declared here so mypy resolves them
    # on concrete subclasses that only inherit StatsMixin (e.g. tests).
    movies: dict[str, object]
    enrichment: object
    _avg_runtime_cache: float | None

    def get_movie_info(self, movie_id: int) -> dict[str, object] | None:
        """Delegate movie-info lookup to CoreMixin.get_movie_info()."""
        return cast(dict[str, object] | None, CoreMixin.get_movie_info(self, movie_id))

    def movies_with_runtime_avg(self) -> float | None:
        """Get average runtime across all movies with ND enrichment data.

        Cached on first call for performance.
        """
        if self.enrichment is None:
            return None
        if hasattr(self, "_avg_runtime_cache"):
            return cast(float | None, self._avg_runtime_cache)
        runtimes: list[float] = []
        for meta in self.enrichment._metadata_map.values():
            if meta.get("runtime") and meta["runtime"] > 0:
                runtimes.append(float(meta["runtime"]))
        if runtimes:
            self._avg_runtime_cache = sum(runtimes) / len(runtimes)
            return cast(float | None, self._avg_runtime_cache)
        self._avg_runtime_cache = None
        return None

    def get_movie_stats(self, movie_id: int) -> dict:
        """Get interesting stats and trivia for a movie."""
        info = self.get_movie_info(movie_id)
        if info is None:
            return {}

        stats: dict[str, object] = {
            "title": info["title"],
            "year": info.get("year"),
            "genres": info.get("genres", []),
            "predicted_rating": info.get("predicted_rating"),
        }

        # Budget / Revenue stats
        budget = info.get("budget")
        revenue = info.get("revenue")
        if budget and revenue:
            budget_f = float(budget)
            revenue_f = float(revenue)
            if budget_f > 0 and revenue_f > 0:
                stats["roi"] = revenue_f / budget_f
                stats["profit"] = revenue_f - budget_f
            if budget_f > 0:
                stats["budget"] = budget_f
            if revenue_f > 0:
                stats["revenue"] = revenue_f

        # Genre count (rarity)
        genre_count = len(info.get("genres", []))
        stats["genre_count"] = genre_count
        # genre_list is only available on the CoreMixin movies DataFrame
        movies = cast(Any, self.movies)
        if movies.get("genre_list") is not None:
            avg_genre_count = float(movies["genre_list"].apply(len).mean())
            stats["genre_count_vs_avg"] = round(float(genre_count - avg_genre_count), 1)

        # Runtime stats
        runtime = info.get("runtime")
        if runtime:
            runtime_f = float(runtime)
            if runtime_f > 0:
                stats["runtime"] = runtime_f
                # Compare to average
                avg_runtime = self.movies_with_runtime_avg()
                if avg_runtime is not None:
                    stats["runtime_diff"] = int(runtime_f - avg_runtime)

        # Popularity percentile (from enrichment data — compare against known values)
        popularity = info.get("popularity")
        if popularity:
            enrichment = self.enrichment
            if enrichment is not None:
                # Compute percentile against all TMDB-enriched popularities
                all_popularities: list[float] = [
                    float(m["popularity"])
                    for m in enrichment._metadata_map.values()
                    if m.get("popularity") and float(m["popularity"]) > 0
                ]
                if all_popularities:
                    pct = (
                        sum(1 for p in all_popularities if p < float(popularity))
                        / len(all_popularities)
                    ) * 100
                    stats["popularity_percentile"] = round(pct, 1)

        # Vote average from TMDB
        vote_avg = info.get("vote_average")
        if vote_avg:
            stats["vote_average"] = vote_avg

        return stats

    # ── ND enrichment methods──────────────────────────────────────────────
    # (~ app/recommender_pkg/core.py)
