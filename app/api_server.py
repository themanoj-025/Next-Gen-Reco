"""
api_server.py — FastAPI REST API for MovieLens AI Recommendation Engine
========================================================================
Exposes search, recommendation, and movie info endpoints with optional
API key auth.

Usage:
    uvicorn app.api_server:app --host 0.0.0.0 --port 8000

Auth:
    Set NEXT_GEN_RECO_API_KEY env var to enable Bearer token auth.
    When unset, all endpoints are open (backward compatible).
"""

import logging
import os
import secrets
import sys
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.recommender import MovieRecommender

# ── App Setup ─────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MovieLens AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

security = HTTPBearer(auto_error=False)

# ── Auth ──────────────────────────────────────────────────────────────────


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials | None = Security(security),
) -> HTTPAuthorizationCredentials:
    """Verify API key from Authorization header. Enabled when NEXT_GEN_RECO_API_KEY is set."""
    api_key = os.environ.get("NEXT_GEN_RECO_API_KEY", "")
    if not api_key:
        return credentials  # No key configured — open access
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    if not secrets.compare_digest(credentials.credentials, api_key):
        raise HTTPException(status_code=403, detail="Invalid API key")
    return credentials


# ── Lazy-loaded recommender ───────────────────────────────────────────────

_recommender: MovieRecommender | None = None


def _get_recommender() -> MovieRecommender:
    """Lazy-load the MovieRecommender (expensive init)."""
    global _recommender
    if _recommender is None:
        logger.info("Loading MovieRecommender (first request)...")
        _recommender = MovieRecommender(model_name="v1_test")
        logger.info("MovieRecommender loaded.")
    return _recommender


# ── Endpoints ─────────────────────────────────────────────────────────────


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "movielens-ai-api"}


@app.get("/api/v1/movies/search", dependencies=[Depends(verify_api_key)])
async def search_movies(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
) -> list[dict[str, Any]]:
    """Search movies by title."""
    rec = _get_recommender()
    results = rec.search_movies(q, limit=limit)
    return results


@app.get("/api/v1/movies/{movie_id}", dependencies=[Depends(verify_api_key)])
async def get_movie(movie_id: int) -> dict[str, Any]:
    """Get detailed info for a movie by ID."""
    rec = _get_recommender()
    info = rec.get_movie_info(movie_id)
    if info is None:
        raise HTTPException(status_code=404, detail=f"Movie {movie_id} not found")
    return info


@app.get("/api/v1/recommendations/{movie_id}", dependencies=[Depends(verify_api_key)])
async def get_recommendations(
    movie_id: int,
    n: int = Query(10, ge=1, le=50, description="Number of recommendations"),
) -> list[dict[str, Any]]:
    """Get similar movie recommendations for a given movie ID."""
    rec = _get_recommender()
    info = rec.get_movie_info(movie_id)
    if info is None:
        raise HTTPException(status_code=404, detail=f"Movie {movie_id} not found")
    results = rec.recommend(movie_id, n=n)
    return results


@app.get("/api/v1/stats", dependencies=[Depends(verify_api_key)])
async def dataset_stats() -> dict[str, Any]:
    """Return summary statistics about the MovieLens dataset."""
    rec = _get_recommender()
    return {
        "total_movies": len(rec.movies),
        "total_ratings": int(rec.movies["rating_count"].sum()) if "rating_count" in rec.movies.columns else 0,
        "year_range": {
            "min": int(rec.movies["year"].min()) if "year" in rec.movies.columns else 0,
            "max": int(rec.movies["year"].max()) if "year" in rec.movies.columns else 0,
        },
        "model_loaded": rec.model_result is not None,
    }


# ── Main ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
