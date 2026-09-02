"""
Unit tests for Next-Gen-Reco — FastAPI REST API (api_server.py).

Covers: health, search, movie info, recommendations, stats endpoints.
Tests both open access and API key auth modes.
"""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


pytestmark = pytest.mark.slow
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.api_server import app, verify_api_key

# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def client() -> None:
    """Create a TestClient for the FastAPI app."""
    return TestClient(app)


# ── Health Endpoint ───────────────────────────────────────────────────────

class TestHealthEndpoint:
    def test_health_returns_ok(self, client) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "movielens-ai-api"

    def test_health_is_get(self, client) -> None:
        response = client.get("/health")
        assert response.status_code == 200


# ── Search Endpoint ───────────────────────────────────────────────────────

class TestSearchMovies:
    @patch("app.api_server._get_recommender")
    def test_search_returns_results(self, mock_get, client) -> None:
        mock_rec = MagicMock()
        mock_rec.search_movies.return_value = [
            {"movieId": 1, "title": "Toy Story", "genres": "Animation|Children"}
        ]
        mock_get.return_value = mock_rec

        response = client.get("/api/v1/movies/search?q=toy")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        mock_rec.search_movies.assert_called_once_with("toy", limit=20)

    @patch("app.api_server._get_recommender")
    def test_search_with_limit(self, mock_get, client) -> None:
        mock_rec = MagicMock()
        mock_rec.search_movies.return_value = []
        mock_get.return_value = mock_rec

        response = client.get("/api/v1/movies/search?q=star&limit=5")
        assert response.status_code == 200
        mock_rec.search_movies.assert_called_once_with("star", limit=5)

    def test_search_missing_query(self, client) -> None:
        response = client.get("/api/v1/movies/search")
        assert response.status_code == 422

    def test_search_empty_query(self, client) -> None:
        response = client.get("/api/v1/movies/search?q=")
        assert response.status_code == 422


# ── Movie Info Endpoint ───────────────────────────────────────────────────

class TestGetMovie:
    @patch("app.api_server._get_recommender")
    def test_get_movie_found(self, mock_get, client) -> None:
        mock_rec = MagicMock()
        mock_rec.get_movie_info.return_value = {
            "movieId": 1, "title": "Toy Story", "genres": "Animation"
        }
        mock_get.return_value = mock_rec

        response = client.get("/api/v1/movies/1")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Toy Story"

    @patch("app.api_server._get_recommender")
    def test_get_movie_not_found(self, mock_get, client) -> None:
        mock_rec = MagicMock()
        mock_rec.get_movie_info.return_value = None
        mock_get.return_value = mock_rec

        response = client.get("/api/v1/movies/999999")
        assert response.status_code == 404


# ── Recommendations Endpoint ──────────────────────────────────────────────

class TestGetRecommendations:
    @patch("app.api_server._get_recommender")
    def test_get_recommendations(self, mock_get, client) -> None:
        mock_rec = MagicMock()
        mock_rec.get_movie_info.return_value = {"movieId": 1}
        mock_rec.recommend.return_value = [
            {"movieId": 2, "title": "Toy Story 2", "score": 0.95}
        ]
        mock_get.return_value = mock_rec

        response = client.get("/api/v1/recommendations/1?n=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        mock_rec.recommend.assert_called_once_with(1, n=5)

    @patch("app.api_server._get_recommender")
    def test_get_recommendations_movie_not_found(self, mock_get, client) -> None:
        mock_rec = MagicMock()
        mock_rec.get_movie_info.return_value = None
        mock_get.return_value = mock_rec

        response = client.get("/api/v1/recommendations/999999")
        assert response.status_code == 404


# ── Stats Endpoint ────────────────────────────────────────────────────────

class TestDatasetStats:
    @patch("app.api_server._get_recommender")
    def test_stats_returns_metrics(self, mock_get, client) -> None:
        import pandas as pd
        mock_rec = MagicMock()
        mock_rec.movies = pd.DataFrame({
            "year": [1995, 2000, 2010],
            "rating_count": [100, 200, 300]
        })
        mock_rec.model_result = {"r2": 0.85}
        mock_get.return_value = mock_rec

        response = client.get("/api/v1/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_movies"] == 3
        assert data["total_ratings"] == 600
        assert data["model_loaded"] is True
        assert data["year_range"]["min"] == 1995
        assert data["year_range"]["max"] == 2010


# ── API Key Auth ──────────────────────────────────────────────────────────

class TestAPIKeyAuth:
    def test_no_key_allows_open_access(self) -> None:
        """When NEXT_GEN_RECO_API_KEY is empty, all endpoints are open."""
        client = TestClient(app)
        response = client.get("/api/v1/stats")
        assert response.status_code != 401
        assert response.status_code != 403

    def test_verify_api_key_returns_none_when_no_env_key(self) -> None:
        with patch.dict(os.environ, {"NEXT_GEN_RECO_API_KEY": ""}):
            result = asyncio.run(verify_api_key(credentials=None))
            assert result is None

    def test_verify_api_key_rejects_wrong_key(self) -> None:
        with patch.dict(os.environ, {"NEXT_GEN_RECO_API_KEY": "correct-key"}):
            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="wrong-key")
            with pytest.raises(HTTPException) as exc_info:
                asyncio.run(verify_api_key(credentials=creds))
            assert exc_info.value.status_code == 403

    def test_verify_api_key_rejects_missing_credentials(self) -> None:
        with patch.dict(os.environ, {"NEXT_GEN_RECO_API_KEY": "some-key"}):
            with pytest.raises(HTTPException) as exc_info:
                asyncio.run(verify_api_key(credentials=None))
            assert exc_info.value.status_code == 401

    def test_verify_api_key_accepts_correct_key(self) -> None:
        with patch.dict(os.environ, {"NEXT_GEN_RECO_API_KEY": "my-secret"}):
            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="my-secret")
            result = asyncio.run(verify_api_key(credentials=creds))
            assert result.credentials == "my-secret"


# ── HTTP Method Validation ────────────────────────────────────────────────

class TestHTTPMethods:
    def test_health_only_accepts_get(self, client) -> None:
        response = client.post("/health")
        assert response.status_code == 405

    @patch("app.api_server._get_recommender")
    def test_search_only_accepts_get(self, mock_get, client) -> None:
        mock_rec = MagicMock()
        mock_rec.search_movies.return_value = []
        mock_get.return_value = mock_rec
        response = client.post("/api/v1/movies/search?q=test")
        assert response.status_code == 405


# ── Response Format Validation ────────────────────────────────────────────

class TestResponseFormat:
    def test_health_response_structure(self, client) -> None:
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert isinstance(data["status"], str)

    @patch("app.api_server._get_recommender")
    def test_search_response_is_list(self, mock_get, client) -> None:
        mock_rec = MagicMock()
        mock_rec.search_movies.return_value = []
        mock_get.return_value = mock_rec
        response = client.get("/api/v1/movies/search?q=test")
        assert isinstance(response.json(), list)

    @patch("app.api_server._get_recommender")
    def test_stats_response_structure(self, mock_get, client) -> None:
        import pandas as pd


        mock_rec = MagicMock()
        mock_rec.movies = pd.DataFrame({"year": [2000], "rating_count": [50]})
        mock_rec.model_result = None
        mock_get.return_value = mock_rec
        response = client.get("/api/v1/stats")
        data = response.json()
        assert "total_movies" in data
        assert "total_ratings" in data
        assert "year_range" in data
        assert "model_loaded" in data
