"""Tests for the disk-persistent TMDB poster TTL cache.

Covers cache-key derivation (normalization, year scoping), TTL expiry
(injectable clock), negative-result caching, persistence across instances,
and corrupt-file resilience.
"""

from __future__ import annotations

import json

import pytest

from app.ui.poster_cache import (
    PosterTTLCache,
    cached_poster,
    get_cache,
    poster_cache_key,
    remember_poster,
)

pytestmark = pytest.mark.unit


@pytest.fixture
def fake_clock():
    """Mutable clock injected into the cache."""
    now = [1_000_000.0]
    return now


@pytest.fixture
def cache(tmp_path, fake_clock) -> PosterTTLCache:
    return PosterTTLCache(path=tmp_path / "posters.json", ttl=100, now=lambda: fake_clock[0])


class TestCacheKey:
    """Cache-key derivation: normalization + year scoping."""

    def test_key_includes_version_prefix(self) -> None:
        assert poster_cache_key("Toy Story", 1995).startswith("v1:")

    def test_key_lowercases_and_collapses_whitespace(self) -> None:
        assert poster_cache_key("The Matrix", 1999) == poster_cache_key("the   MATRIX", 1999)

    def test_key_strips_punctuation(self) -> None:
        assert poster_cache_key("Spy vs. Spy!", 2000) == poster_cache_key("Spy vs Spy", 2000)

    def test_key_scopes_by_year(self) -> None:
        assert poster_cache_key("Batman", 1989) != poster_cache_key("Batman", 2022)

    def test_key_none_year_differs_from_set_year(self) -> None:
        assert poster_cache_key("Inception") != poster_cache_key("Inception", 2010)

    def test_key_empty_title_is_stable(self) -> None:
        assert poster_cache_key("") == poster_cache_key(None) == "v1::"

    def test_different_titles_do_not_collide(self) -> None:
        assert poster_cache_key("Alien", 1979) != poster_cache_key("Aliens", 1986)


class TestGetSet:
    """Round-trip + miss semantics."""

    def test_miss_returns_none(self, cache) -> None:
        assert cache.get("v1:nope:") is None
        assert "v1:nope:" not in cache

    def test_set_then_get(self, cache) -> None:
        key = poster_cache_key("Toy Story", 1995)
        cache.set(key, "https://img.tmdb.org/p.jpg")
        assert cache.get(key) == "https://img.tmdb.org/p.jpg"
        assert key in cache

    def test_negative_result_is_cached(self, cache) -> None:
        """A lookup that found nothing must be recallable without refetch."""
        key = poster_cache_key("Obscure Film", 1970)
        cache.set(key, None)
        assert key in cache  # found (present)…
        assert cache.get(key) is None  # …but with a None URL

    def test_overwrite_updates_url(self, cache) -> None:
        key = poster_cache_key("Up", 2009)
        cache.set(key, "https://a")
        cache.set(key, "https://b")
        assert cache.get(key) == "https://b"


class TestTTL:
    """Expiry via the injectable clock."""

    def test_fresh_entry_hits(self, cache, fake_clock) -> None:
        key = poster_cache_key("Cars", 2006)
        cache.set(key, "https://img")
        fake_clock[0] += 99  # still inside ttl=100
        assert cache.get(key) == "https://img"

    def test_expired_entry_misses(self, cache, fake_clock) -> None:
        key = poster_cache_key("Cars", 2006)
        cache.set(key, "https://img")
        fake_clock[0] += 101
        assert cache.get(key) is None
        assert key not in cache

    def test_expired_negative_is_forgotten(self, cache, fake_clock) -> None:
        key = poster_cache_key("No Poster", None)
        cache.set(key, None)
        assert key in cache
        fake_clock[0] += 101
        assert key not in cache  # caller may retry the network

    def test_prune_removes_only_expired(self, cache, fake_clock) -> None:
        old_key = poster_cache_key("Old", 1990)
        cache.set(old_key, "https://old")
        fake_clock[0] += 60
        new_key = poster_cache_key("New", 2020)
        cache.set(new_key, "https://new")
        fake_clock[0] += 50  # old is now 110s old, new is 50s
        removed = cache.prune()
        assert removed == 1
        assert old_key not in cache
        assert cache.get(new_key) == "https://new"


class TestPersistence:
    """Disk round-trips — the whole point of this cache."""

    def test_survives_new_instance(self, tmp_path, fake_clock) -> None:
        path = tmp_path / "posters.json"
        key = poster_cache_key("Arrival", 2016)
        PosterTTLCache(path=path, ttl=100, now=lambda: fake_clock[0]).set(key, "https://img")

        reborn = PosterTTLCache(path=path, ttl=100, now=lambda: fake_clock[0])
        assert reborn.get(key) == "https://img"

    def test_expired_across_restart(self, tmp_path, fake_clock) -> None:
        path = tmp_path / "posters.json"
        key = poster_cache_key("Dune", 2021)
        PosterTTLCache(path=path, ttl=100, now=lambda: fake_clock[0]).set(key, "https://img")

        fake_clock[0] += 101
        reborn = PosterTTLCache(path=path, ttl=100, now=lambda: fake_clock[0])
        assert reborn.get(key) is None

    def test_missing_file_is_empty_cache(self, tmp_path) -> None:
        cache = PosterTTLCache(path=tmp_path / "absent.json")
        assert cache.get("v1:x:") is None

    def test_corrupt_file_is_treated_as_empty(self, tmp_path) -> None:
        path = tmp_path / "broken.json"
        path.write_text("{not json", encoding="utf-8")
        cache = PosterTTLCache(path=path)
        assert cache.get("v1:x:") is None
        cache.set("v1:x:", "https://img")  # and it can recover
        assert PosterTTLCache(path=path).get("v1:x:") == "https://img"

    def test_malformed_entries_filtered(self, tmp_path) -> None:
        path = tmp_path / "posters.json"
        path.write_text(
            json.dumps(
                {
                    "v1:good:1999": {"url": "https://img", "ts": 1_000_000.0},
                    "v1:badshape:": "just-a-string",
                    "v1:no-ts:": {"url": "https://x"},
                }
            ),
            encoding="utf-8",
        )
        cache = PosterTTLCache(path=path, ttl=10**9, now=lambda: 1_000_000.0)
        assert cache.get("v1:good:1999") == "https://img"
        assert "v1:badshape:" not in cache
        assert "v1:no-ts:" not in cache


class TestModuleAPI:
    """``cached_poster`` / ``remember_poster`` integration with a swapped cache."""

    @pytest.fixture(autouse=True)
    def _swap_cache(self, tmp_path, monkeypatch):
        from app.ui import poster_cache as mod

        shared = PosterTTLCache(path=tmp_path / "shared.json", ttl=100)
        monkeypatch.setattr(mod, "_cache", shared)
        yield shared
        monkeypatch.setattr(mod, "_cache", None)

    def test_miss_then_remember_then_hit(self) -> None:
        found, url = cached_poster("Se7en", 1995)
        assert found is False and url is None

        remember_poster("Se7en", 1995, "https://img")
        found, url = cached_poster("Se7en", 1995)
        assert found is True and url == "https://img"

    def test_negative_roundtrip_through_module_api(self) -> None:
        remember_poster("Nope", None, None)
        found, url = cached_poster("Nope", None)
        assert found is True and url is None

    def test_key_normalization_flows_through_api(self) -> None:
        remember_poster("The Matrix!", 1999, "https://img")
        found, url = cached_poster("the matrix", 1999)
        assert found is True and url == "https://img"

    def test_get_cache_returns_shared_instance(self) -> None:
        assert get_cache() is get_cache()
