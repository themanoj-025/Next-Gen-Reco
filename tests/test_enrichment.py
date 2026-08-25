"""
Tests for app/enrichment.py — ND folder data enrichment module.

Covers:
  - _normalize() title normalization
  - _safe_int() / _safe_float() type coercion
  - format_budget() / format_revenue() / format_runtime() display formatting
  - NDEnrichment initialization and lookup methods
  - get_status_summary() output
"""

import pandas as pd

# ── Title normalization ───────────────────────────────────────────────────────


class TestNormalize:
    """Tests for the _normalize title helper."""

    def test_lowercase(self):
        from app.enrichment import _normalize

        assert _normalize("Toy Story") == "toy story"

    def test_removes_year(self):
        from app.enrichment import _normalize

        assert _normalize("Toy Story (1995)") == "toy story"

    def test_removes_special_chars(self):
        from app.enrichment import _normalize

        result = _normalize("Toy Story: The Sequel!")
        assert ":" not in result
        assert "!" not in result

    def test_collapses_whitespace(self):
        from app.enrichment import _normalize

        result = _normalize("Toy    Story")
        assert "  " not in result

    def test_strips_whitespace(self):
        from app.enrichment import _normalize

        assert _normalize("  Toy Story  ") == "toy story"

    def test_empty_string(self):
        from app.enrichment import _normalize

        assert _normalize("") == ""


# ── Type coercion helpers ─────────────────────────────────────────────────────


class TestSafeInt:
    """Tests for _safe_int static method."""

    def test_valid_int(self):
        from app.enrichment import NDEnrichment

        assert NDEnrichment._safe_int(42) == 42

    def test_valid_float(self):
        from app.enrichment import NDEnrichment

        assert NDEnrichment._safe_int(42.7) == 42

    def test_valid_string(self):
        from app.enrichment import NDEnrichment

        assert NDEnrichment._safe_int("100") == 100

    def test_invalid_string(self):
        from app.enrichment import NDEnrichment

        assert NDEnrichment._safe_int("abc") is None

    def test_zero_returns_none(self):
        from app.enrichment import NDEnrichment

        assert NDEnrichment._safe_int(0) is None

    def test_negative_returns_none(self):
        from app.enrichment import NDEnrichment

        assert NDEnrichment._safe_int(-5) is None

    def test_none_returns_none(self):
        from app.enrichment import NDEnrichment

        assert NDEnrichment._safe_int(None) is None


class TestSafeFloat:
    """Tests for _safe_float static method."""

    def test_valid_float(self):
        from app.enrichment import NDEnrichment

        assert NDEnrichment._safe_float(3.14) == 3.14

    def test_valid_string(self):
        from app.enrichment import NDEnrichment

        assert NDEnrichment._safe_float("2.5") == 2.5

    def test_invalid_string(self):
        from app.enrichment import NDEnrichment

        assert NDEnrichment._safe_float("abc") is None

    def test_zero_returns_none(self):
        from app.enrichment import NDEnrichment

        assert NDEnrichment._safe_float(0) is None

    def test_none_returns_none(self):
        from app.enrichment import NDEnrichment

        assert NDEnrichment._safe_float(None) is None


# ── Formatting helpers ────────────────────────────────────────────────────────


class TestFormatBudget:
    """Tests for budget formatting."""

    def test_billions(self):
        from app.enrichment import NDEnrichment

        enrich = NDEnrichment.__new__(NDEnrichment)
        enrich._metadata_map = {1: {"budget": 2_000_000_000}}
        assert enrich.format_budget(1) == "$2.0B"

    def test_millions(self):
        from app.enrichment import NDEnrichment

        enrich = NDEnrichment.__new__(NDEnrichment)
        enrich._metadata_map = {1: {"budget": 150_000_000}}
        assert enrich.format_budget(1) == "$150M"

    def test_thousands(self):
        from app.enrichment import NDEnrichment

        enrich = NDEnrichment.__new__(NDEnrichment)
        enrich._metadata_map = {1: {"budget": 500_000}}
        assert enrich.format_budget(1) == "$500K"

    def test_no_data(self):
        from app.enrichment import NDEnrichment

        enrich = NDEnrichment.__new__(NDEnrichment)
        enrich._metadata_map = {}
        assert enrich.format_budget(1) == ""


class TestFormatRevenue:
    """Tests for revenue formatting."""

    def test_billions(self):
        from app.enrichment import NDEnrichment

        enrich = NDEnrichment.__new__(NDEnrichment)
        enrich._metadata_map = {1: {"revenue": 3_000_000_000}}
        assert enrich.format_revenue(1) == "$3.0B"

    def test_millions(self):
        from app.enrichment import NDEnrichment

        enrich = NDEnrichment.__new__(NDEnrichment)
        enrich._metadata_map = {1: {"revenue": 200_000_000}}
        assert enrich.format_revenue(1) == "$200M"


class TestFormatRuntime:
    """Tests for runtime formatting."""

    def test_hours_and_minutes(self):
        from app.enrichment import NDEnrichment

        enrich = NDEnrichment.__new__(NDEnrichment)
        enrich._metadata_map = {1: {"runtime": 150}}
        assert enrich.format_runtime(1) == "2h 30m"

    def test_hours_only(self):
        from app.enrichment import NDEnrichment

        enrich = NDEnrichment.__new__(NDEnrichment)
        enrich._metadata_map = {1: {"runtime": 120}}
        assert enrich.format_runtime(1) == "2h"

    def test_minutes_only(self):
        from app.enrichment import NDEnrichment

        enrich = NDEnrichment.__new__(NDEnrichment)
        enrich._metadata_map = {1: {"runtime": 45}}
        assert enrich.format_runtime(1) == "45m"

    def test_no_data(self):
        from app.enrichment import NDEnrichment

        enrich = NDEnrichment.__new__(NDEnrichment)
        enrich._metadata_map = {}
        assert enrich.format_runtime(1) == ""


# ── NDEnrichment class ────────────────────────────────────────────────────────


class TestNDEnrichment:
    """Tests for the NDEnrichment class initialization and lookups."""

    def test_init_without_movies(self):
        from app.enrichment import NDEnrichment

        enrich = NDEnrichment()
        assert not enrich.is_loaded

    def test_init_with_movies(self):
        from app.enrichment import NDEnrichment

        test_movies = pd.DataFrame(
            {
                "movieId": [1, 2],
                "title": ["Toy Story (1995)", "Avatar (2009)"],
                "genres": ["Animation|Children|Comedy", "Action|Adventure|Fantasy"],
            }
        )
        enrich = NDEnrichment(test_movies)
        # May or may not find matches depending on ND data availability
        assert isinstance(enrich._metadata_map, dict)

    def test_get_metadata_returns_none_for_unknown(self):
        from app.enrichment import NDEnrichment

        enrich = NDEnrichment()
        assert enrich.get_metadata(999999) is None

    def test_get_cast_returns_none_for_unknown(self):
        from app.enrichment import NDEnrichment

        enrich = NDEnrichment()
        assert enrich.get_cast(999999) is None

    def test_get_reviews_returns_none_for_unknown(self):
        from app.enrichment import NDEnrichment

        enrich = NDEnrichment()
        assert enrich.get_reviews(999999) is None

    def test_get_movies_by_director_returns_empty(self):
        from app.enrichment import NDEnrichment

        enrich = NDEnrichment()
        assert enrich.get_movies_by_director("Unknown Director") == []

    def test_get_movies_by_actor_returns_empty(self):
        from app.enrichment import NDEnrichment

        enrich = NDEnrichment()
        assert enrich.get_movies_by_actor("Unknown Actor") == []

    def test_has_data_false_for_empty(self):
        from app.enrichment import NDEnrichment

        enrich = NDEnrichment()
        assert not enrich.has_data(1)

    def test_get_cache_size_estimate(self):
        from app.enrichment import NDEnrichment

        enrich = NDEnrichment()
        assert enrich.get_cache_size_estimate() == 0

    def test_get_status_summary_returns_dict(self):
        from app.enrichment import NDEnrichment

        enrich = NDEnrichment()
        summary = enrich.get_status_summary(1)
        assert isinstance(summary, dict)


class TestNormalize:
    def test_basic_lowercasing(self):
        from app.enrichment import _normalize
        assert _normalize("Toy Story") == "toy story"

    def test_removes_year_in_parens(self):
        from app.enrichment import _normalize
        assert _normalize("Toy Story (1995)") == "toy story"

    def test_removes_special_chars(self):
        from app.enrichment import _normalize
        assert _normalize("Star Wars: A New Hope") == "star wars a new hope"

    def test_collapses_whitespace(self):
        from app.enrichment import _normalize
        assert _normalize("  Toy   Story  ") == "toy story"

    def test_strips_whitespace(self):
        from app.enrichment import _normalize
        assert _normalize("  Toy Story  ") == "toy story"

    def test_empty_string(self):
        from app.enrichment import _normalize
        assert _normalize("") == ""

    def test_only_year(self):
        from app.enrichment import _normalize
        assert _normalize("(1995)") == ""

    def test_apostrophes_removed(self):
        from app.enrichment import _normalize
        assert _normalize("Bill & Ted's Excellent Adventure") == "bill ted s excellent adventure"


class TestTmdbTitle:
    def test_basic_lowercasing(self):
        from app.enrichment import _tmdb_title
        assert _tmdb_title("Toy Story") == "toy story"

    def test_removes_special_chars(self):
        from app.enrichment import _tmdb_title
        assert _tmdb_title("Star Wars: Episode IV") == "star wars episode iv"

    def test_collapses_whitespace(self):
        from app.enrichment import _tmdb_title
        assert _tmdb_title("  Toy   Story  ") == "toy story"

    def test_empty_string(self):
        from app.enrichment import _tmdb_title
        assert _tmdb_title("") == ""

    def test_numbers_preserved(self):
        from app.enrichment import _tmdb_title
        assert _tmdb_title("10 Things I Hate About You") == "10 things i hate about you"
