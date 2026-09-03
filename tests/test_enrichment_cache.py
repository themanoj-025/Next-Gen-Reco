"""Tests for the ND enrichment cache (JSON serialization + legacy migration).

Covers the JSON round-trip (including int movieId key restoration), corrupt
cache handling, source-change invalidation, and one-time migration of the
legacy pickle cache into JSON.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import pickle
from pathlib import Path

import pytest

from app.enrichment import NDEnrichment


@pytest.fixture
def cache_paths(tmp_path: Path, monkeypatch) -> tuple[Path, Path, Path]:
    """Point the module cache constants at a temp dir; return (json, pkl, dir)."""
    cache_dir = tmp_path / "cache"
    json_path = cache_dir / "nd_enrichment.json"
    pkl_path = cache_dir / "nd_enrichment.pkl"
    monkeypatch.setattr("app.enrichment._CACHE_DIR", cache_dir)
    monkeypatch.setattr("app.enrichment._ENRICHMENT_CACHE", json_path)
    monkeypatch.setattr("app.enrichment._LEGACY_ENRICHMENT_CACHE", pkl_path)
    return json_path, pkl_path, cache_dir


def _make_enrichment() -> NDEnrichment:
    enrich = NDEnrichment.__new__(NDEnrichment)
    enrich._metadata_map = {1: {"overview": "A movie", "budget": 100, "vote_average": 7.5}}
    enrich._cast_map = {1: {"director": "Jane", "actors": ["Al", "Bo"], "actors_raw": ["Al", "Bo", "unknown"]}}
    enrich._reviews_map = {1: ["great", "fun"]}
    enrich._director_to_movies = {"Jane": [1, 2]}
    enrich._actor_to_movies = {"Al": [1]}
    enrich._loaded = True
    return enrich


def _write_legacy_pickle(pkl_path: Path, data: dict) -> None:
    """Replicate the pre-JSON cache format: HMAC envelope around pickle."""
    key = b"ngreco-default-dev-key"
    raw = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
    sig = hmac.new(key, raw, hashlib.sha256).hexdigest()
    pkl_path.parent.mkdir(parents=True, exist_ok=True)
    with open(pkl_path, "wb") as f:
        pickle.dump({"data": raw, "hmac": sig}, f)


class TestJsonCache:
    def test_save_and_load_roundtrip(self, cache_paths) -> None:
        json_path, _, _ = cache_paths
        enrich = _make_enrichment()
        enrich._save_cache()
        assert json_path.exists()

        fresh = NDEnrichment.__new__(NDEnrichment)
        fresh._metadata_map = {}
        fresh._cast_map = {}
        fresh._reviews_map = {}
        fresh._director_to_movies = {}
        fresh._actor_to_movies = {}
        assert fresh._try_load_cache(None) is True

        assert fresh._metadata_map == {1: {"overview": "A movie", "budget": 100, "vote_average": 7.5}}
        assert fresh._cast_map == {1: {"director": "Jane", "actors": ["Al", "Bo"], "actors_raw": ["Al", "Bo", "unknown"]}}
        assert fresh._reviews_map == {1: ["great", "fun"]}
        assert fresh._director_to_movies == {"Jane": [1, 2]}
        assert fresh._actor_to_movies == {"Al": [1]}
        assert fresh.is_loaded

    def test_int_keys_restored(self, cache_paths) -> None:
        """movieId dict keys must come back as ints, not JSON strings."""
        json_path, _, _ = cache_paths
        _make_enrichment()._save_cache()
        with open(json_path, encoding="utf-8") as f:
            raw = json.load(f)
        assert list(raw["_metadata_map"]) == ["1"]  # JSON stores string keys

        fresh = NDEnrichment.__new__(NDEnrichment)
        for attr in ("_metadata_map", "_cast_map", "_reviews_map", "_director_to_movies", "_actor_to_movies"):
            setattr(fresh, attr, {})
        assert fresh._try_load_cache(None) is True
        assert 1 in fresh._metadata_map  # int key works for lookup

    def test_no_cache_returns_false(self, cache_paths) -> None:
        fresh = NDEnrichment.__new__(NDEnrichment)
        assert fresh._try_load_cache(None) is False

    def test_corrupt_json_returns_false(self, cache_paths) -> None:
        json_path, _, cache_dir = cache_paths
        cache_dir.mkdir(parents=True, exist_ok=True)
        json_path.write_text("{not valid json!!", encoding="utf-8")
        fresh = NDEnrichment.__new__(NDEnrichment)
        assert fresh._try_load_cache(None) is False

    def test_source_change_invalidates_cache(self, cache_paths, tmp_path: Path, monkeypatch) -> None:
        json_path, _, cache_dir = cache_paths
        _make_enrichment()._save_cache()

        # Simulate a source file newer than the cache
        newer = tmp_path / "movies.csv"
        newer.write_text("title\nX\n", encoding="utf-8")
        # Make the source mtime clearly newer than the cache
        import os
        import time

        old = json_path.stat().st_mtime
        os.utime(newer, (old + 100, old + 100))
        monkeypatch.setattr("app.enrichment.TMDB_CSV", newer)
        monkeypatch.setattr("app.enrichment.MAIN_DATA_CSV", tmp_path / "main_data.csv")
        monkeypatch.setattr("app.enrichment.REVIEWS_TXT", tmp_path / "reviews.txt")

        fresh = NDEnrichment.__new__(NDEnrichment)
        assert fresh._try_load_cache(None) is False


class TestLegacyMigration:
    def test_legacy_pickle_migrated_to_json(self, cache_paths) -> None:
        json_path, pkl_path, _ = cache_paths
        data = {
            "_metadata_map": {1: {"overview": "old", "budget": 50}},
            "_cast_map": {1: {"director": "Jane", "actors": ["Al"], "actors_raw": ["Al", "", ""]}},
            "_reviews_map": {2: ["ok"]},
            "_director_to_movies": {"Jane": [1]},
            "_actor_to_movies": {"Al": [1]},
        }
        _write_legacy_pickle(pkl_path, data)

        fresh = NDEnrichment.__new__(NDEnrichment)
        for attr in ("_metadata_map", "_cast_map", "_reviews_map", "_director_to_movies", "_actor_to_movies"):
            setattr(fresh, attr, {})
        assert fresh._try_load_cache(None) is True

        # Data preserved with int keys restored
        assert fresh._metadata_map[1]["overview"] == "old"
        assert fresh._cast_map[1]["director"] == "Jane"
        assert fresh._reviews_map == {2: ["ok"]}

        # Pickle removed, JSON written in its place
        assert not pkl_path.exists()
        assert json_path.exists()
        with open(json_path, encoding="utf-8") as f:
            assert json.load(f)["_metadata_map"]["1"]["overview"] == "old"

    def test_legacy_pickle_tampered_returns_false(self, cache_paths) -> None:
        _, pkl_path, _ = cache_paths
        pkl_path.parent.mkdir(parents=True, exist_ok=True)
        # Wrong HMAC key → integrity check fails
        data = {"_metadata_map": {}}
        raw = pickle.dumps(data)
        sig = hmac.new(b"wrong-key", raw, hashlib.sha256).hexdigest()
        with open(pkl_path, "wb") as f:
            pickle.dump({"data": raw, "hmac": sig}, f)

        fresh = NDEnrichment.__new__(NDEnrichment)
        assert fresh._try_load_cache(None) is False
