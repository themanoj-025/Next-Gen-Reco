"""Recommender — ND enrichment mixin."""

from __future__ import annotations

from typing import Any


class EnrichmentMixin:
    """ND folder enrichment methods (TMDB metadata, cast, reviews)."""

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
