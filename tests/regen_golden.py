#!/usr/bin/env python3
"""Regenerate tests/golden/recommend_movie_*.json after an intentional
scoring change.

Run from the repo root::

    python -m tests.regen_golden

Then eyeball the diff — the goldens are the contract in code review.
"""

from __future__ import annotations

import json
from pathlib import Path

# movieIds pinned in tests/test_recommender_golden.py
GOLDEN_MOVIES = [1, 273]
GOLDEN_N = 10
GOLDEN_DIR = Path(__file__).parent / "golden"


def main() -> None:
    from app.recommender import MovieRecommender

    rec = MovieRecommender(model_name="v1_test")
    GOLDEN_DIR.mkdir(exist_ok=True)
    for movie_id in GOLDEN_MOVIES:
        out = [
            {"movieId": r["movieId"], "title": r["title"], "similarity": r["similarity"]}
            for r in rec.recommend(movie_id, n=GOLDEN_N)
        ]
        path = GOLDEN_DIR / f"recommend_movie_{movie_id}.json"
        path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {path} ({len(out)} entries)")


if __name__ == "__main__":
    main()
