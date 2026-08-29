"""Tests for Next-Gen-Reco enrichment utility functions.

Tests title normalization, caching, and data merging logic.
"""


import pandas as pd


class TestTitleNormalization:
    """Test movie title normalization for matching."""

    def test_normalize_title_lowercase(self) -> None:
        from app.enrichment import _normalize_title

        assert _normalize_title("Toy Story") == "toy story"

    def test_normalize_title_strip_whitespace(self) -> None:
        from app.enrichment import _normalize_title

        assert _normalize_title("  Toy Story  ") == "toy story"

    def test_normalize_title_remove_year(self) -> None:
        from app.enrichment import _normalize_title

        result = _normalize_title("Toy Story (1995)")
        assert "1995" not in result

    def test_normalize_title_special_chars(self) -> None:
        from app.enrichment import _normalize_title

        result = _normalize_title("Toy Story: The Movie!")
        # Should remove punctuation
        assert "!" not in result


class TestCacheHelpers:
    """Test caching logic."""

    def test_cache_path_construction(self) -> None:
        from app.enrichment import _cache_path

        path = _cache_path("test_cache.pkl")
        assert path.name == "test_cache.pkl"
        assert path.suffix == ".pkl"


class TestEnrichmentMerge:
    """Test data merging with ND folder data."""

    def test_merge_empty_dataframes(self) -> None:
        df_main = pd.DataFrame({"movieId": [1, 2], "title": ["Movie A", "Movie B"]})
        df_nd = pd.DataFrame(columns=["title", "overview"])

        from app.enrichment import _merge_nd_data

        result = _merge_nd_data(df_main, df_nd)
        assert len(result) == 2
        assert "overview" in result.columns

    def test_merge_with_matching_titles(self) -> None:
        df_main = pd.DataFrame({"movieId": [1], "title": ["Toy Story"]})
        df_nd = pd.DataFrame({"title": ["Toy Story"], "overview": ["A toy adventure"]})

        from app.enrichment import _merge_nd_data

        result = _merge_nd_data(df_main, df_nd)
        assert len(result) == 1
        assert result.iloc[0]["overview"] == "A toy adventure"

    def test_merge_preserves_all_main_rows(self) -> None:
        df_main = pd.DataFrame({"movieId": [1, 2, 3], "title": ["A", "B", "C"]})
        df_nd = pd.DataFrame({"title": ["A"], "overview": ["About A"]})

        from app.enrichment import _merge_nd_data

        result = _merge_nd_data(df_main, df_nd)
        assert len(result) == 3
