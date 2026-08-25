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

from fastapi import Depends, FastAPI, HTTPException, Query, Response, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.recommender import MovieRecommender

try:
    from prometheus_client import Counter, Histogram, generate_latest

    _PROM_AVAILABLE = True
except ImportError:
    _PROM_AVAILABLE = False

# ── App Setup ─────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if _PROM_AVAILABLE:
    NGRECO_REQUEST_COUNT = Counter(
        "ngreco_requests_total",
        "Total HTTP requests",
        ["method", "endpoint", "status"],
    )
    NGRECO_REQUEST_LATENCY = Histogram(
        "ngreco_request_duration_seconds",
        "HTTP request latency in seconds",
        ["method", "endpoint"],
        buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    )
    NGRECO_SEARCH_COUNT = Counter("ngreco_search_total", "Movie search requests")
    NGRECO_RECOMMEND_COUNT = Counter("ngreco_recommend_total", "Recommendation requests")

app = FastAPI(
    title="MovieLens AI API",
    description="MovieLens AI Recommendation Engine API. Provides movie search,\n"
    "personalized recommendations, and dataset statistics.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "health",
            "description": "Service health check endpoints",
        },
        {
            "name": "movies",
            "description": "Movie search and details",
        },
        {
            "name": "recommendations",
            "description": "Personalized movie recommendations",
        },
        {
            "name": "analytics",
            "description": "Dataset statistics and metadata",
        },
    ],
)

@app.middleware("http")
async def track_metrics(request, call_next):
    import time as _time
    request.state.start_time = _time.time()
    response = await call_next(request)
    if _PROM_AVAILABLE:
        path = request.url.path
        NGRECO_REQUEST_COUNT.labels(
            method=request.method, endpoint=path, status=response.status_code
        ).inc()
        if hasattr(request.state, "start_time"):
            NGRECO_REQUEST_LATENCY.labels(method=request.method, endpoint=path).observe(
                _time.time() - request.state.start_time
            )
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

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
    if _PROM_AVAILABLE:
        NGRECO_SEARCH_COUNT.inc()
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
    if _PROM_AVAILABLE:
        NGRECO_RECOMMEND_COUNT.inc()
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


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    if not _PROM_AVAILABLE:
        return {"status": "prometheus_client not installed"}
    return Response(content=generate_latest(), media_type="text/plain")


# ── Main ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
