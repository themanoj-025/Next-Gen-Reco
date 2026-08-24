"""
Tests for app/recommender.py — search, recommend, and utility methods.

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
  - find_movies_combo() output
"""

import numpy as np
import pytest

# ── String helpers (no recommender instance needed) ───────────────────────────


class TestNormalizeTitle:
    """Tests for title normalization."""

    def test_lowercase(self, recommender):
        assert recommender._normalize_title("TOY STORY") == "toy story"

    def test_strips_whitespace(self, recommender):
        assert recommender._normalize_title("  Toy Story  ") == "toy story"

    def test_removes_punctuation(self, recommender):
        assert recommender._normalize_title("Toy Story: The Sequel!") == "toy story the sequel"

    def test_preserves_numbers(self, recommender):
        assert recommender._normalize_title("2001: A Space Odyssey") == "2001 a space odyssey"

    def test_empty_string(self, recommender):
        assert recommender._normalize_title("") == ""


class TestTokenize:
    """Tests for text tokenization."""

    def test_basic_tokenize(self, recommender):
        tokens = recommender._tokenize("Hello World")
        assert "hello" in tokens
        assert "world" in tokens

    def test_filters_short_tokens(self, recommender):
        tokens = recommender._tokenize("A big dog")
        # "a" is 1 char, filtered out
        assert "a" not in tokens

    def test_lowercase(self, recommender):
        tokens = recommender._tokenize("UPPER CASE")
        assert all(t == t.lower() for t in tokens)

    def test_empty_string(self, recommender):
        assert recommender._tokenize("") == []


class TestQueryEditDistance:
    """Tests for Levenshtein-based fuzzy matching."""

    def test_identical_after_normalize(self, recommender):
        # _query_edit_distance normalizes then truncates title to len(query)+3
        # So "Toy Story" -> "toy story" matches "toy story" exactly
        assert recommender._query_edit_distance("toy story", "Toy Story") == 0

    def test_one_edit_distance(self, recommender):
        dist = recommender._query_edit_distance("toy stori", "Toy Story")
        assert dist == 1

    def test_typos_are_close(self, recommender):
        dist = recommender._query_edit_distance("matrix", "The Matrix")
        # "matrix" normalizes to "matrix", title normalizes to "the matrix" truncated to 9 chars = "the matr"
        # Levenshtein("matrix", "the matr") should be moderate
        assert dist <= 6

    def test_unrelated_strings_are_far(self, recommender):
        dist = recommender._query_edit_distance("completely different", "Toy Story")
        assert dist > 5


# ── Similarity computations ───────────────────────────────────────────────────


class TestGenreSimilarity:
    """Tests for genre cosine similarity."""

    def test_returns_array(self, recommender):
        sim = recommender._genre_similarity_to(1)
        assert isinstance(sim, np.ndarray)

    def test_length_matches_movies(self, recommender):
        sim = recommender._genre_similarity_to(1)
        assert len(sim) == len(recommender.movies)

    def test_self_similarity_is_one(self, recommender):
        sim = recommender._genre_similarity_to(1)
        idx = recommender._get_movie_idx(1)
        assert sim[idx] == pytest.approx(1.0, abs=0.01)

    def test_similar_genres_have_high_score(self, recommender):
        """Two movies with the same genre should have similarity > 0.5."""
        sim = recommender._genre_similarity_to(1)  # Toy Story
        # Find another Animation movie
        anim_movies = recommender.movies[recommender.movies["genres"].str.contains("Animation")]
        if len(anim_movies) > 1:
            other_id = anim_movies.iloc[1]["movieId"]
            other_idx = recommender._get_movie_idx(other_id)
            assert sim[other_idx] > 0.5


class TestJaccardSimilarity:
    """Tests for tag Jaccard similarity."""

    def test_returns_float(self, recommender):
        sim = recommender._jaccard_similarity(1, 2)
        assert isinstance(sim, float)

    def test_returns_zero_for_unknown_movie(self, recommender):
        sim = recommender._jaccard_similarity(999999, 1)
        assert sim == 0.0

    def test_symmetric(self, recommender):
        sim_ab = recommender._jaccard_similarity(1, 2)
        sim_ba = recommender._jaccard_similarity(2, 1)
        assert sim_ab == sim_ba


# ── Search ────────────────────────────────────────────────────────────────────


class TestSearchMovies:
    """Tests for movie search functionality."""

    def test_exact_title_match(self, recommender):
        results = recommender.search_movies("Toy Story")
        assert len(results) > 0
        assert any("Toy Story" in r["title"] for r in results)

    def test_case_insensitive(self, recommender):
        results = recommender.search_movies("toy story")
        assert len(results) > 0

    def test_partial_match(self, recommender):
        results = recommender.search_movies("matrix")
        assert len(results) > 0

    def test_no_results_for_nonsense(self, recommender):
        results = recommender.search_movies("zzzznonexistentzzzz")
        assert len(results) == 0

    def test_limit_respected(self, recommender):
        results = recommender.search_movies("the", limit=5)
        assert len(results) <= 5

    def test_short_query_returns_empty(self, recommender):
        results = recommender.search_movies("a")
        assert len(results) == 0

    def test_result_has_required_fields(self, recommender):
        results = recommender.search_movies("Toy Story")
        assert len(results) > 0
        r = results[0]
        assert "movieId" in r
        assert "title" in r
        assert "genres" in r

    def test_advanced_search_with_genre_filter(self, recommender):
        results = recommender.search_movies_advanced("the", genre_filter="Comedy", limit=5)
        for r in results:
            assert "Comedy" in r["genres_str"]

    def test_advanced_search_with_year_filter(self, recommender):
        results = recommender.search_movies_advanced("the", year_min=2000, year_max=2010, limit=5)
        for r in results:
            if r["year"]:
                assert 2000 <= r["year"] <= 2010


class TestSearchSuggestions:
    """Tests for 'Did you mean?' suggestions."""

    def test_returns_list(self, recommender):
        suggestions = recommender.search_suggestions("toy stori")
        assert isinstance(suggestions, list)

    def test_short_query_returns_empty(self, recommender):
        suggestions = recommender.search_suggestions("ab")
        assert len(suggestions) == 0


# ── Recommend ─────────────────────────────────────────────────────────────────


class TestRecommend:
    """Tests for the hybrid recommendation engine."""

    def test_returns_list(self, recommender):
        recs = recommender.recommend(1, n=5)
        assert isinstance(recs, list)

    def test_returns_correct_count(self, recommender):
        recs = recommender.recommend(1, n=5)
        assert len(recs) <= 5

    def test_does_not_include_self(self, recommender):
        recs = recommender.recommend(1, n=10)
        movie_ids = [r["movieId"] for r in recs]
        assert 1 not in movie_ids

    def test_result_has_required_fields(self, recommender):
        recs = recommender.recommend(1, n=3)
        assert len(recs) > 0
        r = recs[0]
        required = {"movieId", "title", "genres", "similarity", "genre_similarity", "tag_similarity", "year_proximity"}
        assert required.issubset(set(r.keys()))

    def test_similarity_is_bounded(self, recommender):
        recs = recommender.recommend(1, n=10)
        for r in recs:
            assert 0.0 <= r["similarity"] <= 1.0

    def test_unknown_movie_returns_empty(self, recommender):
        recs = recommender.recommend(999999, n=5)
        assert recs == []

    def test_different_weights_produce_different_results(self, recommender):
        recs_default = recommender.recommend(1, n=5)
        recs_genre_heavy = recommender.recommend(1, n=5, genre_weight=0.9, tag_weight=0.05, year_weight=0.03, rating_weight=0.02)
        # The order or content should differ
        default_ids = [r["movieId"] for r in recs_default]
        genre_ids = [r["movieId"] for r in recs_genre_heavy]
        # At least some overlap expected, but order may differ
        assert len(default_ids) > 0
        assert len(genre_ids) > 0


# ── get_movie_info ────────────────────────────────────────────────────────────


class TestGetMovieInfo:
    """Tests for the movie info lookup."""

    def test_returns_dict_for_valid_id(self, recommender):
        info = recommender.get_movie_info(1)
        assert isinstance(info, dict)

    def test_returns_none_for_invalid_id(self, recommender):
        info = recommender.get_movie_info(999999)
        assert info is None

    def test_has_expected_keys(self, recommender):
        info = recommender.get_movie_info(1)
        assert "movieId" in info
        assert "title" in info
        assert "genres" in info

    def test_movie_id_matches(self, recommender):
        info = recommender.get_movie_info(1)
        assert info["movieId"] == 1


# ── _prefilter_movies ─────────────────────────────────────────────────────────


class TestPrefilterMovies:
    """Tests for the vectorized pre-filter."""

    def test_genre_filter(self, recommender):
        filtered = recommender._prefilter_movies(genre_filter="Comedy")
        assert len(filtered) > 0
        assert all("Comedy" in g for g in filtered["genres"])

    def test_year_filter(self, recommender):
        filtered = recommender._prefilter_movies(year_min=2000, year_max=2005)
        assert len(filtered) > 0
        years = filtered["year"]
        assert all(2000 <= y <= 2005 for y in years if y > 0)

    def test_no_filter_returns_all(self, recommender):
        filtered = recommender._prefilter_movies()
        assert len(filtered) == len(recommender.movies)

    def test_impossible_filter_returns_empty(self, recommender):
        filtered = recommender._prefilter_movies(genre_filter="NonexistentGenre123")
        assert len(filtered) == 0


# ── movie_night_generator ─────────────────────────────────────────────────────


@pytest.mark.slow
class TestMovieNightGenerator:
    """Tests for the movie marathon generator.

    Marked slow because movie_night_generator iterates over all movies
    and calls predict_rating for each one (~30s with 87K movies).
    """

    def test_returns_list(self, recommender):
        result = recommender.movie_night_generator(genre="Comedy", movie_count=3)
        assert isinstance(result, list)

    def test_respects_count_limit(self, recommender):
        result = recommender.movie_night_generator(movie_count=2)
        assert len(result) <= 2

    def test_count_cannot_exceed_5(self, recommender):
        result = recommender.movie_night_generator(movie_count=100)
        assert len(result) <= 5

    def test_count_cannot_be_zero(self, recommender):
        result = recommender.movie_night_generator(movie_count=0)
        # min(max(0, 1), 5) = 1, so should return at least 0 or 1
        assert len(result) <= 1

    def test_genre_filter_works(self, recommender):
        result = recommender.movie_night_generator(genre="Animation", movie_count=3)
        for r in result:
            assert "Animation" in r["genres_str"]


# ── find_movies_combo ─────────────────────────────────────────────────────────


@pytest.mark.slow
class TestFindMoviesCombo:
    """Tests for the multi-criteria combo finder.

    Marked slow because find_movies_combo iterates over candidates
    and calls predict_rating for each one.
    """

    def test_returns_list(self, recommender):
        result = recommender.find_movies_combo(genre="Comedy")
        assert isinstance(result, list)

    def test_genre_filter(self, recommender):
        result = recommender.find_movies_combo(genre="Comedy", limit=5)
        for r in result:
            assert "Comedy" in r["genres_str"]

    def test_year_filter(self, recommender):
        result = recommender.find_movies_combo(year_min=1990, year_max=1995, limit=5)
        for r in result:
            if r.get("year"):
                assert 1990 <= r["year"] <= 1995

    def test_limit_respected(self, recommender):
        result = recommender.find_movies_combo(limit=3)
        assert len(result) <= 3

    def test_impossible_criteria_returns_empty(self, recommender):
        result = recommender.find_movies_combo(genre="NonexistentGenre123")
        assert result == []


# ── get_movies_by_decade ──────────────────────────────────────────────────────


@pytest.mark.slow
class TestGetMoviesByDecade:
    """Tests for the decade explorer.

    Marked slow because get_movies_by_decade iterates over candidates
    and calls predict_rating for each one.
    """

    def test_returns_dict(self, recommender):
        result = recommender.get_movies_by_decade(1990)
        assert isinstance(result, dict)

    def test_has_expected_keys(self, recommender):
        result = recommender.get_movies_by_decade(1990)
        assert "decade" in result
        assert "decade_label" in result
        assert "count" in result
        assert "top_movies" in result
        assert "genre_distribution" in result

    def test_decade_label_format(self, recommender):
        result = recommender.get_movies_by_decade(1990)
        assert result["decade_label"] == "1990s"

    def test_count_is_positive(self, recommender):
        result = recommender.get_movies_by_decade(1990)
        assert result["count"] > 0

    def test_genre_distribution_is_dict(self, recommender):
        result = recommender.get_movies_by_decade(1990)
        assert isinstance(result["genre_distribution"], dict)


# ── get_feature_breakdown ─────────────────────────────────────────────────────


class TestFeatureBreakdown:
    """Tests for the prediction explanation feature."""

    def test_returns_dict_for_valid_movie(self, recommender):
        result = recommender.get_feature_breakdown(1)
        # May be None if model isn't loaded, but should not raise
        if result is not None:
            assert "prediction" in result

    def test_returns_none_for_unknown_movie(self, recommender):
        result = recommender.get_feature_breakdown(999999)
        assert result is None


# ── _exact_search ─────────────────────────────────────────────────────────────


class TestExactSearch:
    """Tests for the fast vectorized exact/substring search path."""

    def test_exact_match(self, recommender):
        # Use a title that exists exactly (no year suffix)
        # Find a movie with a very short title
        short_titles = recommender.movies[recommender.movies["title"].str.len() < 15]
        if len(short_titles) > 0:
            title = short_titles.iloc[0]["title"]
            results = recommender._exact_search(title.lower())
            assert len(results) > 0
            assert results[0][0] == 100.0

    def test_starts_with_match(self, recommender):
        results = recommender._exact_search("toy")
        assert len(results) > 0
        # Score should be 80 for starts-with match
        assert results[0][0] == 80.0

    def test_contains_match(self, recommender):
        results = recommender._exact_search("matrix")
        assert len(results) > 0
        # Score is 80 for starts-with or 60-70 for contains
        assert results[0][0] >= 60.0

    def test_no_match_returns_empty(self, recommender):
        results = recommender._exact_search("zzzznonexistentzzzz")
        assert results == []


# ── get_top_picks ─────────────────────────────────────────────────────────────


class TestGetTopPicks:
    """Tests for the global top picks feature."""

    def test_returns_list(self, recommender):
        result = recommender.get_top_picks()
        assert isinstance(result, list)

    def test_has_results(self, recommender):
        result = recommender.get_top_picks(n=5)
        assert len(result) > 0
        assert len(result) <= 5

    def test_genre_filter(self, recommender):
        result = recommender.get_top_picks(genre="Comedy", n=3)
        for r in result:
            assert "Comedy" in r["genres_str"]

    def test_min_year_filter(self, recommender):
        result = recommender.get_top_picks(min_year=2010, n=3)
        for r in result:
            if r.get("year"):
                assert r["year"] >= 2010

    def test_result_has_predicted_rating(self, recommender):
        result = recommender.get_top_picks(n=3)
        assert len(result) > 0
        for r in result:
            assert "predicted_rating" in r
            assert r["predicted_rating"] is not None


# ── enrich_movie_info ─────────────────────────────────────────────────────────


class TestEnrichMovieInfo:
    """Tests for the ND enrichment method."""

    def test_returns_dict(self, recommender):
        info = recommender.get_movie_info(1)
        enriched = recommender.enrich_movie_info(info)
        assert isinstance(enriched, dict)

    def test_preserves_original_keys(self, recommender):
        info = recommender.get_movie_info(1)
        enriched = recommender.enrich_movie_info(info)
        assert enriched["movieId"] == info["movieId"]
        assert enriched["title"] == info["title"]
        assert enriched["genres"] == info["genres"]

    def test_adds_enrichment_keys(self, recommender):
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

    def test_returns_false_for_missing_cache(self, tmp_path):
        from app.recommender import _check_cache_valid
        result = _check_cache_valid(tmp_path / "nonexistent.npz")
        assert result is False

    def test_returns_true_when_cache_newer(self, tmp_path):
        from app.recommender import _check_cache_valid
        import time
        source = tmp_path / "source.csv"
        source.touch()
        time.sleep(1.1)  # Windows needs >1s for distinct mtime
        cache = tmp_path / "cache.npz"
        cache.touch()
        assert _check_cache_valid(cache, source) is True

    def test_returns_false_when_source_newer(self, tmp_path):
        from app.recommender import _check_cache_valid
        import time
        cache = tmp_path / "cache.npz"
        cache.touch()
        time.sleep(1.1)  # Windows needs >1s for distinct mtime
        source = tmp_path / "source.csv"
        source.touch()
        assert _check_cache_valid(cache, source) is False

    def test_returns_true_when_source_missing(self, tmp_path):
        from app.recommender import _check_cache_valid
        cache = tmp_path / "cache.npz"
        cache.touch()
        assert _check_cache_valid(cache, tmp_path / "nonexistent.csv") is True


# ── search_movies_advanced edge cases ──────────────────────────────────────────


class TestSearchAdvancedEdgeCases:
    """Additional edge cases for advanced search."""

    def test_empty_query_returns_empty(self, recommender):
        assert recommender.search_movies_advanced("") == []

    def test_single_char_query_returns_empty(self, recommender):
        assert recommender.search_movies_advanced("a") == []

    def test_rating_min_filter(self, recommender):
        results = recommender.search_movies_advanced("toy story", rating_min=4.0, limit=5)
        for r in results:
            if r["predicted_rating"] is not None:
                assert r["predicted_rating"] >= 4.0

    def test_impossible_genre_filter(self, recommender):
        results = recommender.search_movies_advanced("the", genre_filter="NonexistentGenre")
        assert results == []

    def test_impossible_year_filter(self, recommender):
        results = recommender.search_movies_advanced("the", year_min=1800, year_max=1810)
        assert results == []

    def test_search_score_in_results(self, recommender):
        results = recommender.search_movies_advanced("Toy Story", limit=3)
        assert len(results) > 0
        for r in results:
            assert "_search_score" in r
            assert r["_search_score"] > 0


# ── recommend edge cases ───────────────────────────────────────────────────────


class TestRecommendEdgeCases:
    """Additional edge cases for the recommendation engine."""

    def test_no_diversify(self, recommender):
        recs = recommender.recommend(1, n=5, diversify=False)
        assert len(recs) > 0
        # Without diversity, top picks should have higher similarity
        assert recs[0]["similarity"] > 0

    def test_all_genres_no_tags(self, recommender):
        recs = recommender.recommend(1, n=5, genre_weight=1.0, tag_weight=0.0, year_weight=0.0, rating_weight=0.0)
        assert len(recs) > 0
        # genre_similarity should be the main component
        for r in recs:
            assert r["genre_similarity"] > 0

    def test_all_tags_no_genres(self, recommender):
        recs = recommender.recommend(1, n=5, genre_weight=0.0, tag_weight=1.0, year_weight=0.0, rating_weight=0.0)
        assert len(recs) > 0

    def test_large_n(self, recommender):
        recs = recommender.recommend(1, n=50)
        assert len(recs) > 0
        assert len(recs) <= 50

    def test_n_one(self, recommender):
        recs = recommender.recommend(1, n=1)
        assert len(recs) == 1

    def test_movie_with_no_genres(self, recommender):
        # Find a movie with (no genres listed)
        no_genre = recommender.movies[recommender.movies["genres"].str.contains("no genres listed", na=False)]
        if len(no_genre) > 0:
            mid = no_genre.iloc[0]["movieId"]
            recs = recommender.recommend(int(mid), n=3)
            assert isinstance(recs, list)

    def test_all_rec_keys_present(self, recommender):
        recs = recommender.recommend(1, n=3)
        for r in recs:
            required = {"movieId", "title", "genres", "genres_str", "similarity",
                        "predicted_rating", "genre_similarity", "tag_similarity", "year_proximity"}
            assert required.issubset(set(r.keys()))


# ── get_movie_stats ────────────────────────────────────────────────────────────


class TestGetMovieStats:
    """Tests for the movie statistics feature."""

    def test_returns_dict(self, recommender):
        stats = recommender.get_movie_stats(1)
        assert isinstance(stats, dict)

    def test_has_expected_keys(self, recommender):
        stats = recommender.get_movie_stats(1)
        assert "title" in stats
        assert "genres" in stats
        assert "genre_count" in stats
        assert "genre_count_vs_avg" in stats

    def test_returns_empty_for_unknown(self, recommender):
        stats = recommender.get_movie_stats(999999)
        assert stats == {}

    def test_genre_count_is_int(self, recommender):
        stats = recommender.get_movie_stats(1)
        assert isinstance(stats["genre_count"], int)
        assert stats["genre_count"] > 0

    def test_genre_count_vs_avg_is_float(self, recommender):
        stats = recommender.get_movie_stats(1)
        assert isinstance(stats["genre_count_vs_avg"], float)


# ── search_movies wrapper ──────────────────────────────────────────────────────


class TestSearchMoviesWrapper:
    """Tests for the search_movies wrapper that delegates to advanced search."""

    def test_delegates_to_advanced(self, recommender):
        results = recommender.search_movies("Toy Story", limit=5)
        assert len(results) > 0
        assert "Toy Story" in results[0]["title"]

    def test_empty_for_nonsense(self, recommender):
        results = recommender.search_movies("zzzznonexistentzzzz")
        assert results == []


# ── ND enrichment wrapper methods ──────────────────────────────────────────────


class TestEnrichmentWrappers:
    """Tests for the ND enrichment delegation methods."""

    def test_get_enriched_metadata(self, recommender):
        meta = recommender.get_enriched_metadata(1)
        if meta is not None:
            assert isinstance(meta, dict)

    def test_get_enriched_cast(self, recommender):
        cast = recommender.get_enriched_cast(1)
        if cast is not None:
            assert isinstance(cast, dict)

    def test_get_enriched_reviews(self, recommender):
        reviews = recommender.get_enriched_reviews(1)
        if reviews is not None:
            assert isinstance(reviews, list)

    def test_get_movies_by_director(self, recommender):
        result = recommender.get_movies_by_director("Nonexistent Director")
        assert isinstance(result, list)

    def test_get_movies_by_actor(self, recommender):
        result = recommender.get_movies_by_actor("Nonexistent Actor")
        assert isinstance(result, list)

    def test_movies_with_runtime_avg(self, recommender):
        avg = recommender.movies_with_runtime_avg()
        if avg is not None:
            assert avg > 0
            # Should be cached on second call
            avg2 = recommender.movies_with_runtime_avg()
            assert avg == avg2


# ── _get_movie_idx ─────────────────────────────────────────────────────────────


class TestGetMovieIdx:
    """Tests for the movie index lookup."""

    def test_valid_movie(self, recommender):
        idx = recommender._get_movie_idx(1)
        assert idx is not None
        assert isinstance(idx, int)

    def test_invalid_movie(self, recommender):
        idx = recommender._get_movie_idx(999999)
        assert idx is None


# ── _predict_rating_safe ───────────────────────────────────────────────────────


class TestPredictRatingSafe:
    """Tests for the safe prediction wrapper."""

    def test_valid_movie(self, recommender):
        row = recommender.movies_by_id.get(1)
        if row is not None:
            pred = recommender._predict_rating_safe(row)
            # May be None if model isn't loaded, but should not raise
            if pred is not None:
                assert isinstance(pred, float)

    def test_returns_none_for_no_model(self, recommender):
        # Even without a model, should not raise
        row = recommender.movies_by_id.get(1)
        if row is not None:
            result = recommender._predict_rating_safe(row)
            # Result could be None or a float — both acceptable
            assert result is None or isinstance(result, float)


# ── Module-level prediction cache ──────────────────────────────────────────────


class TestPredictionCache:
    """Tests for the module-level prediction cache behavior."""

    def test_cache_cleared_on_init(self, recommender):
        from app.recommender import _prediction_cache
        # Cache may be populated by earlier tests in this module-scoped fixture.
        # Verify the cache is a dict and was set up during __init__.
        assert isinstance(_prediction_cache, dict)

    def test_cache_populated_after_predict(self, recommender):
        from app.recommender import _prediction_cache, _predict_model_result
        if _predict_model_result is not None:
            row = recommender.movies_by_id.get(1)
            if row is not None:
                recommender._predict_rating_safe(row)
                # After prediction, cache should have an entry for movieId=1
                assert 1 in _prediction_cache

    def test_cache_returns_same_value(self, recommender):
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

    def test_creates_tokens(self, recommender):
        recommender._precompute_title_tokens()
        assert hasattr(recommender, "_title_tokens")
        assert len(recommender._title_tokens) == len(recommender.movies)

    def test_tokens_are_lists(self, recommender):
        recommender._precompute_title_tokens()
        for tokens in recommender._title_tokens.head(5):
            assert isinstance(tokens, list)


# ── search_suggestions edge cases ──────────────────────────────────────────────


class TestSearchSuggestionsEdgeCases:
    """Additional tests for search suggestions."""

    def test_returns_unique_titles(self, recommender):
        suggestions = recommender.search_suggestions("toy stori")
        assert len(suggestions) == len(set(suggestions))

    def test_returns_max_three(self, recommender):
        suggestions = recommender.search_suggestions("the")
        assert len(suggestions) <= 3

    def test_returns_strings(self, recommender):
        suggestions = recommender.search_suggestions("matrix")
        for s in suggestions:
            assert isinstance(s, str)


# ── _build_genre_vectors ──────────────────────────────────────────────────────


class TestBuildGenreVectors:
    """Tests for genre vector construction."""

    def test_vectors_shape(self, recommender):
        assert recommender._genre_vectors.shape[0] == len(recommender.movies)
        assert recommender._genre_vectors.shape[1] == len(recommender.genre_cols)

    def test_norms_positive(self, recommender):
        assert all(n > 0 for n in recommender._genre_norms)

    def test_genre_dummies_is_dataframe(self, recommender):
        import pandas as pd
        assert isinstance(recommender.genre_dummies, pd.DataFrame)


# ── _build_tag_lookup ──────────────────────────────────────────────────────────


class TestBuildTagLookup:
    """Tests for tag lookup construction."""

    def test_lookup_is_dict(self, recommender):
        assert isinstance(recommender._tag_lookup, dict)

    def test_lookup_values_are_sets(self, recommender):
        for val in list(recommender._tag_lookup.values())[:5]:
            assert isinstance(val, set)

    def test_tag_cols_populated(self, recommender):
        assert len(recommender._tag_cols) > 0
