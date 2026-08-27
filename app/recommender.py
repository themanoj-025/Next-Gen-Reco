"""
MovieLens Content-Based Recommendation Engine
==============================================
Recommends similar movies using a hybrid approach:
  - Genre cosine similarity (primary, computed on-the-fly)
  - Tag Jaccard similarity (computed on-demand)
  - Year proximity
  - Predicted rating boost (computed only for top candidates)

Usage:
    from recommender import MovieRecommender
    rec = MovieRecommender()
    recommendations = rec.recommend(movie_id=1, n=10)

.. note::

   The implementation has been refactored into ``app.recommender_pkg``
   for maintainability.  This module re-exports ``MovieRecommender`` so
   that existing ``from app.recommender import MovieRecommender`` imports
   continue to work unchanged.
"""

from __future__ import annotations

# Re-export from the package for backward compatibility.
from app.recommender_pkg import MovieRecommender  # noqa: F401

__all__ = ["MovieRecommender"]


# ── Quick test ────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    print("Testing MovieRecommender...")
    rec = MovieRecommender()

    # Test search
    print("\n--- Search 'toy story' ---")
    results = rec.search_movies("toy story", limit=5)
    for r in results:
        print(f"  [{r['movieId']}] {r['title']}  (pred: {r['predicted_rating']})")

    if results:
        mid = results[0]["movieId"]
        print(f"\n--- Recommend for movie {mid} ---")
        recs = rec.recommend(mid, n=8)
        for r in recs:
            genres = ", ".join(r["genres"][:3])
            print(
                f"  [{r['movieId']}] {r['title']}  sim={r['similarity']:.3f}  pred={r['predicted_rating']}  [{genres}]"
            )

        print(f"\n--- Feature breakdown for {mid} ---")
        fb = rec.get_feature_breakdown(mid)
        if fb and fb.get("explanation"):
            print(fb["explanation"])
        else:
            print("  (not available)")
