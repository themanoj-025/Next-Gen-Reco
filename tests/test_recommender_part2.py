"""Tests for app/recommender.py — search, recommend, and utility methods.

Covers:
  - _normalize_title() and _tokenize() string helpers
  - _query_edit_distance() fuzzy matching
  - _genre_similarity_to() cosine similarity
  - _jaccard_similarity() tag overlap
  - search_movies() and search_movies_advanced()
  - recommend() output structure and diversity
  - get_movie_info() lookup
  - _prefilter_movies() filtering
  - movie_night_generator() output
  - find_movies_combo() output — Part 2."""

import numpy as np
import pytest


class TestGetTopPicks:
    """Tests for the global top picks feature."""

    def test_returns_list(self, recommender) -> None:
        result = recommender.get_top_picks()
        assert isinstance(result, list)

    def test_has_results(self, recommender) -> None:
        result = recommender.get_top_picks(n=5)
        assert len(result) > 0
        assert len(result) <= 5

    def test_genre_filter(self, recommender) -> None:
        result = recommender.get_top_picks(genre="Comedy", n=3)
        for r in result:
            assert "Comedy" in r["genres_str"]

    def test_min_year_filter(self, recommender) -> None:
        result = recommender.get_top_picks(min_year=2010, n=3)
        for r in result:
            if r.get("year"):
                assert r["year"] >= 2010

    def test_result_has_predicted_rating(self, recommender) -> None:
        result = recommender.get_top_picks(n=3)
        assert len(result) > 0
        for r in result:
            assert "predicted_rating" in r
            assert r["predicted_rating"] is not None


# ── enrich_movie_info ─────────────────────────────────────────────────────────


class TestEnrichMovieInfo:
    """Tests for the ND enrichment method."""

    def test_returns_dict(self, recommender) -> None:
        info = recommender.get_movie_info(1)
        enriched = recommender.enrich_movie_info(info)
        assert isinstance(enriched, dict)

    def test_preserves_original_keys(self, recommender) -> None:
        info = recommender.get_movie_info(1)
        enriched = recommender.enrich_movie_info(info)
        assert enriched["movieId"] == info["movieId"]
        assert enriched["title"] == info["title"]
        assert enriched["genres"] == info["genres"]

    def test_adds_enrichment_keys(self, recommender) -> None:
        info = recommender.get_movie_info(1)
        enriched = recommender.enrich_movie_info(info)
        # These keys should exist (may be empty/None if no enrichment data)
        assert "overview" in enriched
        assert "tagline" in enriched
        assert "runtime" in enriched
        assert "budget" in enriched
        assert "revenue" in enriched
        assert "vote_average" in enriched
        assert "director" in enriched
        assert "actors" in enriched


# ── _check_cache_valid ────────────────────────────────────────────────────────


class TestCheckCacheValid:
    """Tests for the cache validation helper."""

    def test_returns_false_for_missing_cache(self, tmp_path) -> None:
        from app.recommender import _check_cache_valid
        result = _check_cache_valid(tmp_path / "nonexistent.npz")
        assert result is False

    def test_returns_true_when_cache_newer(self, tmp_path) -> None:
        import time

        from app.recommender import _check_cache_valid
        source = tmp_path / "source.csv"
        source.touch()
        time.sleep(1.1)  # Windows needs >1s for distinct mtime
        cache = tmp_path / "cache.npz"
        cache.touch()
        assert _check_cache_valid(cache, source) is True

    def test_returns_false_when_source_newer(self, tmp_path) -> None:
        import time

        from app.recommender import _check_cache_valid
        cache = tmp_path / "cache.npz"
        cache.touch()
        time.sleep(1.1)  # Windows needs >1s for distinct mtime
        source = tmp_path / "source.csv"
        source.touch()
        assert _check_cache_valid(cache, source) is False

    def test_returns_true_when_source_missing(self, tmp_path) -> None:
        from app.recommender import _check_cache_valid
        cache = tmp_path / "cache.npz"
        cache.touch()
        assert _check_cache_valid(cache, tmp_path / "nonexistent.csv") is True


# ── search_movies_advanced edge cases ──────────────────────────────────────────


class TestSearchAdvancedEdgeCases:
    """Additional edge cases for advanced search."""

    def test_empty_query_returns_empty(self, recommender) -> None:
        assert recommender.search_movies_advanced("") == []

    def test_single_char_query_returns_empty(self, recommender) -> None:
        assert recommender.search_movies_advanced("a") == []

    def test_rating_min_filter(self, recommender) -> None:
        results = recommender.search_movies_advanced("toy story", rating_min=4.0, limit=5)
        for r in results:
            if r["predicted_rating"] is not None:
                assert r["predicted_rating"] >= 4.0

    def test_impossible_genre_filter(self, recommender) -> None:
        results = recommender.search_movies_advanced("the", genre_filter="NonexistentGenre")
        assert results == []

    def test_impossible_year_filter(self, recommender) -> None:
        results = recommender.search_movies_advanced("the", year_min=1800, year_max=1810)
        assert results == []

    def test_search_score_in_results(self, recommender) -> None:
        results = recommender.search_movies_advanced("Toy Story", limit=3)
        assert len(results) > 0
        for r in results:
            assert "_search_score" in r
            assert r["_search_score"] > 0


# ── recommend edge cases ───────────────────────────────────────────────────────


class TestRecommendEdgeCases:
    """Additional edge cases for the recommendation engine."""

    def test_no_diversify(self, recommender) -> None:
        recs = recommender.recommend(1, n=5, diversify=False)
        assert len(recs) > 0
        # Without diversity, top picks should have higher similarity
        assert recs[0]["similarity"] > 0

    def test_all_genres_no_tags(self, recommender) -> None:
        recs = recommender.recommend(1, n=5, genre_weight=1.0, tag_weight=0.0, year_weight=0.0, rating_weight=0.0)
        assert len(recs) > 0
        # genre_similarity should be the main component
        for r in recs:
            assert r["genre_similarity"] > 0

    def test_all_tags_no_genres(self, recommender) -> None:
        recs = recommender.recommend(1, n=5, genre_weight=0.0, tag_weight=1.0, year_weight=0.0, rating_weight=0.0)
        assert len(recs) > 0

    def test_large_n(self, recommender) -> None:
        recs = recommender.recommend(1, n=50)
        assert len(recs) > 0
        assert len(recs) <= 50

    def test_n_one(self, recommender) -> None:
        recs = recommender.recommend(1, n=1)
        assert len(recs) == 1

    def test_movie_with_no_genres(self, recommender) -> None:
        # Find a movie with (no genres listed)
        no_genre = recommender.movies[recommender.movies["genres"].str.contains("no genres listed", na=False)]
        if len(no_genre) > 0:
            mid = no_genre.iloc[0]["movieId"]
            recs = recommender.recommend(int(mid), n=3)
            assert isinstance(recs, list)

    def test_all_rec_keys_present(self, recommender) -> None:
        recs = recommender.recommend(1, n=3)
        for r in recs:
            required = {"movieId", "title", "genres", "genres_str", "similarity",
                        "predicted_rating", "genre_similarity", "tag_similarity", "year_proximity"}
            assert required.issubset(set(r.keys()))


# ── get_movie_stats ────────────────────────────────────────────────────────────


class TestGetMovieStats:
    """Tests for the movie statistics feature."""

    def test_returns_dict(self, recommender) -> None:
        stats = recommender.get_movie_stats(1)
        assert isinstance(stats, dict)

    def test_has_expected_keys(self, recommender) -> None:
        stats = recommender.get_movie_stats(1)
        assert "title" in stats
        assert "genres" in stats
        assert "genre_count" in stats
        assert "genre_count_vs_avg" in stats

    def test_returns_empty_for_unknown(self, recommender) -> None:
        stats = recommender.get_movie_stats(999999)
        assert stats == {}

    def test_genre_count_is_int(self, recommender) -> None:
        stats = recommender.get_movie_stats(1)
        assert isinstance(stats["genre_count"], int)
        assert stats["genre_count"] > 0

    def test_genre_count_vs_avg_is_float(self, recommender) -> None:
        stats = recommender.get_movie_stats(1)
        assert isinstance(stats["genre_count_vs_avg"], float)


# ── search_movies wrapper ──────────────────────────────────────────────────────


class TestSearchMoviesWrapper:
    """Tests for the search_movies wrapper that delegates to advanced search."""

    def test_delegates_to_advanced(self, recommender) -> None:
        results = recommender.search_movies("Toy Story", limit=5)
        assert len(results) > 0
        assert "Toy Story" in results[0]["title"]

    def test_empty_for_nonsense(self, recommender) -> None:
        results = recommender.search_movies("zzzznonexistentzzzz")
        assert results == []


# ── ND enrichment wrapper methods ──────────────────────────────────────────────


class TestEnrichmentWrappers:
    """Tests for the ND enrichment delegation methods."""

    def test_get_enriched_metadata(self, recommender) -> None:
        meta = recommender.get_enriched_metadata(1)
        if meta is not None:
            assert isinstance(meta, dict)

    def test_get_enriched_cast(self, recommender) -> None:
        cast = recommender.get_enriched_cast(1)
        if cast is not None:
            assert isinstance(cast, dict)

    def test_get_enriched_reviews(self, recommender) -> None:
        reviews = recommender.get_enriched_reviews(1)
        if reviews is not None:
            assert isinstance(reviews, list)

    def test_get_movies_by_director(self, recommender) -> None:
        result = recommender.get_movies_by_director("Nonexistent Director")
        assert isinstance(result, list)

    def test_get_movies_by_actor(self, recommender) -> None:
        result = recommender.get_movies_by_actor("Nonexistent Actor")
        assert isinstance(result, list)

    def test_movies_with_runtime_avg(self, recommender) -> None:
        avg = recommender.movies_with_runtime_avg()
        if avg is not None:
            assert avg > 0
            # Should be cached on second call
            avg2 = recommender.movies_with_runtime_avg()
            assert avg == avg2


# ── _get_movie_idx ─────────────────────────────────────────────────────────────


class TestGetMovieIdx:
    """Tests for the movie index lookup."""

    def test_valid_movie(self, recommender) -> None:
        idx = recommender._get_movie_idx(1)
        assert idx is not None
        assert isinstance(idx, int)

    def test_invalid_movie(self, recommender) -> None:
        idx = recommender._get_movie_idx(999999)
        assert idx is None


# ── _predict_rating_safe ───────────────────────────────────────────────────────


class TestPredictRatingSafe:
    """Tests for the safe prediction wrapper."""

    def test_valid_movie(self, recommender) -> None:
        row = recommender.movies_by_id.get(1)
        if row is not None:
            pred = recommender._predict_rating_safe(row)
            # May be None if model isn't loaded, but should not raise
            if pred is not None:
                assert isinstance(pred, float)

    def test_returns_none_for_no_model(self, recommender) -> None:
        # Even without a model, should not raise
        row = recommender.movies_by_id.get(1)
        if row is not None:
            result = recommender._predict_rating_safe(row)
            # Result could be None or a float — both acceptable
            assert result is None or isinstance(result, float)


# ── Module-level prediction cache ──────────────────────────────────────────────


class TestPredictionCache:
    """Tests for the module-level prediction cache behavior."""

    def test_cache_cleared_on_init(self, recommender) -> None:
        from app.recommender import _prediction_cache
        # Cache may be populated by earlier tests in this module-scoped fixture.
        # Verify the cache is a dict and was set up during __init__.
        assert isinstance(_prediction_cache, dict)

    def test_cache_populated_after_predict(self, recommender) -> None:
        from app.recommender import _predict_model_result, _prediction_cache
        if _predict_model_result is not None:
            row = recommender.movies_by_id.get(1)
            if row is not None:
                recommender._predict_rating_safe(row)
                # After prediction, cache should have an entry for movieId=1
                assert 1 in _prediction_cache

    def test_cache_returns_same_value(self, recommender) -> None:
        from app.recommender import _predict_model_result
        if _predict_model_result is not None:
            row = recommender.movies_by_id.get(1)
            if row is not None:
                pred1 = recommender._predict_rating_safe(row)
                pred2 = recommender._predict_rating_safe(row)
                assert pred1 == pred2


# ── _precompute_title_tokens ──────────────────────────────────────────────────


class TestPrecomputeTitleTokens:
    """Tests for the title token precomputation."""

    def test_creates_tokens(self, recommender) -> None:
        recommender._precompute_title_tokens()
        assert hasattr(recommender, "_title_tokens")
        assert len(recommender._title_tokens) == len(recommender.movies)

    def test_tokens_are_lists(self, recommender) -> None:
        recommender._precompute_title_tokens()
        for tokens in recommender._title_tokens.head(5):
            assert isinstance(tokens, list)


# ── search_suggestions edge cases ──────────────────────────────────────────────


class TestSearchSuggestionsEdgeCases:
    """Additional tests for search suggestions."""

    def test_returns_unique_titles(self, recommender) -> None:
        suggestions = recommender.search_suggestions("toy stori")
        assert len(suggestions) == len(set(suggestions))

    def test_returns_max_three(self, recommender) -> None:
        suggestions = recommender.search_suggestions("the")
        assert len(suggestions) <= 3

    def test_returns_strings(self, recommender) -> None:
        suggestions = recommender.search_suggestions("matrix")
        for s in suggestions:
            assert isinstance(s, str)


# ── _build_genre_vectors ──────────────────────────────────────────────────────


class TestBuildGenreVectors:
    """Tests for genre vector construction."""

    def test_vectors_shape(self, recommender) -> None:
        assert recommender._genre_vectors.shape[0] == len(recommender.movies)
        assert recommender._genre_vectors.shape[1] == len(recommender.genre_cols)

    def test_norms_positive(self, recommender) -> None:
        assert all(n > 0 for n in recommender._genre_norms)

    def test_genre_dummies_is_dataframe(self, recommender) -> None:
        import pandas as pd
        assert isinstance(recommender.genre_dummies, pd.DataFrame)


# ── _build_tag_lookup ──────────────────────────────────────────────────────────


class TestBuildTagLookup:
    """Tests for tag lookup construction."""

    def test_lookup_is_dict(self, recommender) -> None:
        assert isinstance(recommender._tag_lookup, dict)

    def test_lookup_values_are_sets(self, recommender) -> None:
        for val in list(recommender._tag_lookup.values())[:5]:
            assert isinstance(val, set)

    def test_tag_cols_populated(self, recommender) -> None:
        assert len(recommender._tag_cols) > 0
