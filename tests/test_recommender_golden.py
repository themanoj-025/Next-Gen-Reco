"""Golden-input tests for the recommender ensemble.

A fixed movie goes in, a pinned top-N list comes out.  The expected outputs
live in ``tests/golden/recommend_movie_*.json`` (movieId + title + the
rounded hybrid similarity), so any change to the hybrid scoring formula,
the genre/tag/year/rating weighting, the diversity penalty, or the data
files shows up as a diff against the committed golden values.

Regenerate the goldens after an *intentional* scoring change with::

    python -m tests.regen_golden

Also covers ensemble behavior invariants: self-exclusion, determinism,
weight sensitivity, result schema, and unknown-movie handling.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

GOLDEN_DIR = Path(__file__).parent / "golden"

# Similarity is asserted with a small tolerance: the golden stores 4-decimal
# roundings of float32 numpy math, which is stable across platforms but not
# worth exact-equality coupling.
SIM_TOL = 1e-4


def _load_golden(movie_id: int) -> list[dict]:
    with open(GOLDEN_DIR / f"recommend_movie_{movie_id}.json", encoding="utf-8") as f:
        data: list[dict] = json.load(f)
    return data


class TestGoldenTopN:
    """Fixed input -> pinned top-N output."""

    @pytest.mark.parametrize("movie_id", [1, 273])
    def test_top_n_matches_golden(self, recommender, movie_id: int) -> None:
        expected = _load_golden(movie_id)
        actual = recommender.recommend(movie_id, n=len(expected))

        assert len(actual) == len(expected), "top-N list length changed"
        for got, want in zip(actual, expected, strict=True):
            assert got["movieId"] == want["movieId"], (
                f"rank order changed: expected {want['title']} ({want['movieId']}), "
                f"got {got['title']} ({got['movieId']})"
            )
            assert got["title"] == want["title"]
            assert got["similarity"] == pytest.approx(want["similarity"], abs=SIM_TOL)

    def test_golden_top1_for_toy_story(self, recommender) -> None:
        """The marquee case: Toy Story's best match is Monsters, Inc."""
        top = recommender.recommend(1, n=1)[0]
        assert top["movieId"] == 4886
        assert top["title"] == "Monsters, Inc. (2001)"

    def test_deterministic_across_calls(self, recommender) -> None:
        first = recommender.recommend(1, n=10)
        second = recommender.recommend(1, n=10)
        assert [r["movieId"] for r in first] == [r["movieId"] for r in second]
        assert [r["similarity"] for r in first] == [r["similarity"] for r in second]

    def test_golden_files_exist_for_parametrize(self) -> None:
        """Guard the fixtures themselves — a rename would break collection."""
        for movie_id in (1, 273):
            assert (GOLDEN_DIR / f"recommend_movie_{movie_id}.json").exists()


class TestEnsembleBehavior:
    """Hybrid scoring invariants that must hold regardless of goldens."""

    def test_excludes_the_query_movie(self, recommender) -> None:
        ids = [r["movieId"] for r in recommender.recommend(1, n=20)]
        assert 1 not in ids

    def test_respects_n(self, recommender) -> None:
        for n in (1, 5, 12, 25):
            assert len(recommender.recommend(1, n=n)) == n

    def test_result_schema(self, recommender) -> None:
        r = recommender.recommend(1, n=1)[0]
        assert {
            "movieId",
            "title",
            "year",
            "genres",
            "genres_str",
            "similarity",
            "predicted_rating",
            "genre_similarity",
            "tag_similarity",
            "year_proximity",
        } <= set(r)
        assert 0.0 < r["similarity"] <= 1.0

    def test_results_sorted_by_similarity_desc(self, recommender) -> None:
        sims = [r["similarity"] for r in recommender.recommend(1, n=20)]
        assert sims == sorted(sims, reverse=True)

    def test_unknown_movie_returns_empty(self, recommender) -> None:
        assert recommender.recommend(999_999_999, n=5) == []

    def test_zero_weights_still_returns_results(self, recommender) -> None:
        """Tag/rating weights of 0 fall back to genre+year only."""
        recs = recommender.recommend(1, n=10, tag_weight=0.0, rating_weight=0.0, year_weight=0.0)
        assert len(recs) == 10

    def test_genre_only_rankings_are_childfriendly(self, recommender) -> None:
        """With tag+rating+year weights off, genre similarity drives ranking —
        Toy Story's nearest neighbours by one-hot genre overlap are other
        five-genre family films."""
        recs = recommender.recommend(
            1, n=5, tag_weight=0.0, rating_weight=0.0, year_weight=0.0, diversify=False
        )
        # Toy Story = Adventure|Animation|Children|Comedy|Fantasy; expect the
        # other five-genre animated titles to dominate the pure-genre ranking.
        top_genres = [set(r["genres"]) for r in recs[:3]]
        for g in top_genres:
            assert "Animation" in g or "Children" in g

    def test_diversify_flag_changes_output_consistently(self, recommender) -> None:
        plain = recommender.recommend(1, n=10, diversify=False)
        diversified = recommender.recommend(1, n=10, diversify=True)
        # Same candidate pool (both non-empty, same length); scores may differ.
        assert len(plain) == len(diversified) == 10

    def test_large_n_graceful(self, recommender) -> None:
        """Large n works without error and returns exactly n results.

        Rating/tag weights are zeroed: with them on, each of the n*10
        candidates costs a scaler+model predict (minutes of runtime), and
        this test is about list sizing, not scoring.
        """
        out = recommender.recommend(1, n=1500, tag_weight=0.0, rating_weight=0.0)
        assert len(out) == 1500
        assert out[0]["movieId"] != 1
