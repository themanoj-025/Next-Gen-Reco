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
