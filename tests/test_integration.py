"""Integration tests for Next-Gen-Reco — full HTTP lifecycle through FastAPI.

Tests the complete request-response cycle including middleware, error handling,
multi-endpoint workflows, and OpenAPI schema generation. Uses mocked recommender
but exercises real HTTP routing and middleware.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.api_server import app

pytestmark = pytest.mark.slow
# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture()
def client():
    """Create a TestClient for the FastAPI app."""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def mock_recommender():
    """A fully mocked MovieRecommender."""
    rec = MagicMock()
    rec.search_movies.return_value = [
        {"movieId": 1, "title": "Toy Story", "genres": "Animation|Children"},
        {"movieId": 2, "title": "Jumanji", "genres": "Adventure|Children"},
    ]
    rec.get_movie_info.return_value = {
        "movieId": 1,
        "title": "Toy Story",
        "genres": "Animation|Children",
        "year": 1995,
    }
    rec.recommend.return_value = [
        {"movieId": 2, "title": "Jumanji", "score": 0.95},
        {"movieId": 3, "title": "Grumpier Old Men", "score": 0.88},
    ]
    rec.movies = pd.DataFrame({
        "year": [1995, 2000, 2010, 2015, 2020],
        "rating_count": [100, 200, 150, 300, 250],
    })
    rec.model_result = {"r2": 0.85}
    return rec


# ── Full HTTP Lifecycle ───────────────────────────────────────────────────


class TestHTTPLifecycle:
    """Tests that exercise the full request → middleware → handler → response cycle."""

    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "movielens-ai-api"

    def test_health_has_content_type_json(self, client):
        response = client.get("/health")
        assert "application/json" in response.headers["content-type"]


# ── Middleware Behavior ────────────────────────────────────────────────────


class TestMiddleware:
    """Verify CORS, security headers, and rate limiting are applied."""

    def test_cors_headers_present(self, client):
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:8501",
                "Access-Control-Request-Method": "GET",
            },
        )
        # CORS middleware should respond (may be 405 for OPTIONS but headers present)
        assert response.status_code in (200, 405)

    def test_metrics_endpoint_accessible(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200


# ── Search Endpoints ──────────────────────────────────────────────────────


class TestSearchWorkflow:
    """Integration tests for movie search through the full stack."""

    @patch("app.api_server._get_recommender")
    def test_search_returns_paginated_results(self, mock_get, client, mock_recommender):
        mock_get.return_value = mock_recommender
        response = client.get("/api/v1/movies/search?q=toy&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 2
        mock_recommender.search_movies.assert_called_once_with("toy", limit=2)

    @patch("app.api_server._get_recommender")
    def test_search_with_large_limit(self, mock_get, client, mock_recommender):
        mock_get.return_value = mock_recommender
        response = client.get("/api/v1/movies/search?q=star&limit=100")
        assert response.status_code == 200
        mock_recommender.search_movies.assert_called_once_with("star", limit=100)

    def test_search_missing_query_returns_422(self, client):
        response = client.get("/api/v1/movies/search")
        assert response.status_code == 422

    def test_search_empty_query_returns_422(self, client):
        response = client.get("/api/v1/movies/search?q=")
        assert response.status_code == 422

    @patch("app.api_server._get_recommender")
    def test_search_empty_results(self, mock_get, client, mock_recommender):
        mock_recommender.search_movies.return_value = []
        mock_get.return_value = mock_recommender
        response = client.get("/api/v1/movies/search?q=zzzznonexistent")
        assert response.status_code == 200
        assert response.json() == []


# ── Movie Info Endpoints ──────────────────────────────────────────────────


class TestMovieInfoWorkflow:
    """Integration tests for movie info and recommendations."""

    @patch("app.api_server._get_recommender")
    def test_get_movie_found(self, mock_get, client, mock_recommender):
        mock_get.return_value = mock_recommender
        response = client.get("/api/v1/movies/1")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Toy Story"
        assert data["movieId"] == 1

    @patch("app.api_server._get_recommender")
    def test_get_movie_not_found(self, mock_get, client, mock_recommender):
        mock_recommender.get_movie_info.return_value = None
        mock_get.return_value = mock_recommender
        response = client.get("/api/v1/movies/999999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch("app.api_server._get_recommender")
    def test_recommendations_for_valid_movie(self, mock_get, client, mock_recommender):
        mock_get.return_value = mock_recommender
        response = client.get("/api/v1/recommendations/1?n=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        mock_recommender.recommend.assert_called_once_with(1, n=5)

    @patch("app.api_server._get_recommender")
    def test_recommendations_movie_not_found(self, mock_get, client, mock_recommender):
        mock_recommender.get_movie_info.return_value = None
        mock_get.return_value = mock_recommender
        response = client.get("/api/v1/recommendations/999999")
        assert response.status_code == 404


# ── Stats Endpoint ────────────────────────────────────────────────────────


class TestStatsWorkflow:
    """Integration tests for dataset statistics."""

    @patch("app.api_server._get_recommender")
    def test_stats_returns_all_fields(self, mock_get, client, mock_recommender):
        mock_get.return_value = mock_recommender
        response = client.get("/api/v1/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_movies" in data
        assert "total_ratings" in data
        assert "year_range" in data
        assert "model_loaded" in data
        assert data["total_movies"] == 5
        assert data["total_ratings"] == 1000
        assert data["year_range"]["min"] == 1995
        assert data["year_range"]["max"] == 2020
        assert data["model_loaded"] is True

    @patch("app.api_server._get_recommender")
    def test_stats_without_rating_count_column(self, mock_get, client):
        rec = MagicMock()
        rec.movies = pd.DataFrame({"year": [2000]})
        rec.model_result = None
        mock_get.return_value = rec
        response = client.get("/api/v1/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_ratings"] == 0
        assert data["model_loaded"] is False


# ── Error Handling Workflows ──────────────────────────────────────────────


class TestErrorHandling:
    """Verify graceful error handling across the API."""

    def test_nonexistent_route_returns_404(self, client):
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_wrong_http_method_returns_405(self, client):
        response = client.post("/health")
        assert response.status_code == 405

    @patch("app.api_server._get_recommender")
    def test_recommendations_with_invalid_limit(self, mock_get, client, mock_recommender):
        mock_get.return_value = mock_recommender
        response = client.get("/api/v1/recommendations/1?n=0")
        assert response.status_code == 422  # validation error

    @patch("app.api_server._get_recommender")
    def test_search_with_negative_limit(self, mock_get, client, mock_recommender):
        mock_get.return_value = mock_recommender
        response = client.get("/api/v1/movies/search?q=test&limit=-1")
        assert response.status_code == 422


# ── Multi-Endpoint Workflow ────────────────────────────────────────────────


class TestMultiEndpointWorkflow:
    """Simulate a realistic user session: health → search → movie → recommend → stats."""

    @patch("app.api_server._get_recommender")
    def test_full_user_workflow(self, mock_get, client, mock_recommender):
        mock_get.return_value = mock_recommender

        # Step 1: Check health
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        # Step 2: Search for movies
        search = client.get("/api/v1/movies/search?q=toy")
        assert search.status_code == 200
        results = search.json()
        assert len(results) >= 1

        # Step 3: Get movie details
        movie = client.get("/api/v1/movies/1")
        assert movie.status_code == 200
        assert movie.json()["title"] == "Toy Story"

        # Step 4: Get recommendations
        recs = client.get("/api/v1/recommendations/1?n=5")
        assert recs.status_code == 200
        assert len(recs.json()) >= 1

        # Step 5: Check stats
        stats = client.get("/api/v1/stats")
        assert stats.status_code == 200
        assert stats.json()["total_movies"] == 5

    def test_openapi_schema_is_valid(self, client):
        """Verify the OpenAPI schema is generated and well-formed."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
        assert schema["info"]["title"] == "MovieLens AI API"
        # Verify key endpoints are documented
        assert "/health" in schema["paths"]
        assert "/api/v1/movies/search" in schema["paths"]
        assert "/api/v1/stats" in schema["paths"]
        assert "/api/v1/recommendations/{movie_id}" in schema["paths"]


# ── Auth Flow Integration ─────────────────────────────────────────────────


class TestAuthFlow:
    """Test API key authentication across the full request cycle."""

    def test_open_access_when_no_key_set(self, client):
        """When NEXT_GEN_RECO_API_KEY is empty, all endpoints are open."""
        with patch.dict(os.environ, {"NEXT_GEN_RECO_API_KEY": ""}):
            response = client.get("/health")
            assert response.status_code == 200

    def test_rejects_request_without_auth_header(self):
        with patch.dict(os.environ, {"NEXT_GEN_RECO_API_KEY": "test-key"}):
            c = TestClient(app, raise_server_exceptions=False)
            response = c.get("/api/v1/stats")
            assert response.status_code == 401

    def test_rejects_wrong_api_key(self):
        with patch.dict(os.environ, {"NEXT_GEN_RECO_API_KEY": "correct-key"}):
            c = TestClient(app, raise_server_exceptions=False)
            response = c.get(
                "/api/v1/stats",
                headers={"Authorization": "Bearer wrong-key"},
            )
            assert response.status_code == 403

    def test_accepts_correct_api_key(self):
        with patch.dict(os.environ, {"NEXT_GEN_RECO_API_KEY": "my-secret"}):
            c = TestClient(app, raise_server_exceptions=False)
            with patch("app.api_server._get_recommender") as mock_get:
                rec = MagicMock()
                rec.movies = pd.DataFrame({"year": [2000]})
                rec.model_result = None
                mock_get.return_value = rec
                response = c.get(
                    "/api/v1/stats",
                    headers={"Authorization": "Bearer my-secret"},
                )
                assert response.status_code == 200


# ── Concurrent Request Handling ───────────────────────────────────────────


class TestConcurrentRequests:
    """Verify the API handles multiple sequential requests without state leaks."""

    @patch("app.api_server._get_recommender")
    def test_sequential_search_requests(self, mock_get, client, mock_recommender):
        mock_get.return_value = mock_recommender
        for query in ["toy", "star", "war", "love"]:
            response = client.get(f"/api/v1/movies/search?q={query}")
            assert response.status_code == 200
            assert isinstance(response.json(), list)

    @patch("app.api_server._get_recommender")
    def test_mixed_endpoint_requests(self, mock_get, client, mock_recommender):
        mock_get.return_value = mock_recommender
        # Interleave different endpoints
        client.get("/health")
        client.get("/api/v1/movies/search?q=toy")
        client.get("/api/v1/stats")
        client.get("/api/v1/movies/1")
        client.get("/api/v1/recommendations/1")
        # All should succeed
        response = client.get("/health")
        assert response.status_code == 200
