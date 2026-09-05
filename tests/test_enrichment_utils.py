"""Tests for Next-Gen-Reco enrichment utility functions.

Tests title normalization, caching, and data merging logic.
"""

import pandas as pd


class TestTitleNormalization:
    """Test movie title normalization for matching."""

    def test_normalize_title_lowercase(self) -> None:
        from app.enrichment import _normalize

        assert _normalize("Toy Story") == "toy story"

    def test_normalize_title_strip_whitespace(self) -> None:
        from app.enrichment import _normalize

        assert _normalize("  Toy Story  ") == "toy story"

    def test_normalize_title_remove_year(self) -> None:
        from app.enrichment import _normalize

        result = _normalize("Toy Story (1995)")
        assert "1995" not in result

    def test_normalize_title_special_chars(self) -> None:
        from app.enrichment import _normalize

        result = _normalize("Toy Story: The Movie!")
        # Should remove punctuation
        assert "!" not in result


class TestTmdbTitle:
    """Test TMDB title normalization."""

    def test_tmdb_title_lowercase(self) -> None:
        from app.enrichment import _tmdb_title

        assert _tmdb_title("Avatar") == "avatar"

    def test_tmdb_title_strips_special(self) -> None:
        from app.enrichment import _tmdb_title

        result = _tmdb_title("The Movie: Part 2")
        assert ":" not in result
        assert "the movie part 2" == result


class TestEnrichmentClass:
    """Test NDEnrichment class initialization and methods."""

    def test_init_without_movies_df(self) -> None:
        from app.enrichment import NDEnrichment

        enrich = NDEnrichment()
        assert enrich.is_loaded is False

    def test_metadata_returns_none_for_unknown(self) -> None:
        from app.enrichment import NDEnrichment

        enrich = NDEnrichment()
        assert enrich.get_metadata(999999) is None

    def test_cast_returns_none_for_unknown(self) -> None:
        from app.enrichment import NDEnrichment

        enrich = NDEnrichment()
        assert enrich.get_cast(999999) is None

    def test_reviews_returns_none_for_unknown(self) -> None:
        from app.enrichment import NDEnrichment

        enrich = NDEnrichment()
        assert enrich.get_reviews(999999) is None

    def test_get_movies_by_director_empty(self) -> None:
        from app.enrichment import NDEnrichment

        enrich = NDEnrichment()
        assert enrich.get_movies_by_director("Nonexistent") == []

    def test_get_movies_by_actor_empty(self) -> None:
        from app.enrichment import NDEnrichment

        enrich = NDEnrichment()
        assert enrich.get_movies_by_actor("Nonexistent") == []

    def test_has_data_false_for_unknown(self) -> None:
        from app.enrichment import NDEnrichment

        enrich = NDEnrichment()
        assert enrich.has_data(999999) is False

    def test_format_budget_empty(self) -> None:
        from app.enrichment import NDEnrichment

        enrich = NDEnrichment()
        assert enrich.format_budget(999999) == ""

    def test_format_revenue_empty(self) -> None:
        from app.enrichment import NDEnrichment

        enrich = NDEnrichment()
        assert enrich.format_revenue(999999) == ""

    def test_format_runtime_empty(self) -> None:
        from app.enrichment import NDEnrichment

        enrich = NDEnrichment()
        assert enrich.format_runtime(999999) == ""

    def test_get_status_summary_empty(self) -> None:
        from app.enrichment import NDEnrichment

        enrich = NDEnrichment()
        summary = enrich.get_status_summary(999999)
        assert isinstance(summary, dict)
        assert len(summary) == 0

    def test_get_cache_size_estimate(self) -> None:
        from app.enrichment import NDEnrichment

        enrich = NDEnrichment()
        assert isinstance(enrich.get_cache_size_estimate(), int)
