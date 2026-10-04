"""Disk-persistent TTL cache for TMDB poster lookups.

Poster lookups are network-bound and slow; the app already keeps two
in-memory layers (``st.cache_data(ttl=3600)`` and a per-session dict), both
of which are lost on process restart.  This cache survives restarts by
persisting to ``.cache/poster_cache.json`` and expires entries after
``POSTER_CACHE_TTL`` seconds.

Deliberately Streamlit-free so it can be unit-tested without a runtime.
"""

from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path
from typing import cast

from app._paths import CACHE_DIR

logger = logging.getLogger(__name__)

#: Poster URLs change rarely; a week of reuse is safe and bounds staleness.
POSTER_CACHE_TTL = 7 * 24 * 3600
POSTER_CACHE_FILE = CACHE_DIR / "poster_cache.json"

#: Key format version — bump if the key derivation changes so stale-format
#: entries are discarded instead of misread.
_KEY_VERSION = "v1"


def poster_cache_key(title: str | None, year: int | None = None) -> str:
    """Derive the cache key for a poster lookup.

    Normalizes the title (lowercase, strip punctuation/whitespace) so
    cosmetic differences (``"The Matrix"`` vs ``"the  matrix "``) hit the
    same entry, and scopes by year so reboots with the same title don't
    collide (``"Batman" (2022)`` vs ``"Batman" (1989)``).

    >>> poster_cache_key("The Matrix", 1999)
    'v1:the matrix:1999'
    >>> poster_cache_key("the  matrix!", None)
    'v1:the matrix:'
    """
    norm = re.sub(r"[^a-z0-9]+", " ", (title or "").lower()).strip()
    norm = re.sub(r"\s+", " ", norm)
    return f"{_KEY_VERSION}:{norm}:{year if year is not None else ''}"


class PosterTTLCache:
    """JSON-file-backed cache mapping keys to poster URLs with TTL expiry.

    ``now`` is injectable for tests.  A missing or corrupt file is treated
    as an empty cache (posters are rebuildable from the API, so losing the
    cache is safe).
    """

    def __init__(
        self,
        path: Path | None = None,
        ttl: int = POSTER_CACHE_TTL,
        now=time.time,
    ) -> None:
        self.path = Path(path) if path is not None else POSTER_CACHE_FILE
        self.ttl = ttl
        self._now = now
        self._data: dict[str, dict] | None = None

    def _load(self) -> dict[str, dict]:
        if self._data is not None:
            return self._data
        try:
            with open(self.path, encoding="utf-8") as f:
                raw = json.load(f)
            # Only trust dict[str, {url, ts}] shapes; anything else is corrupt.
            if isinstance(raw, dict):
                self._data = {
                    k: v for k, v in raw.items() if isinstance(v, dict) and "url" in v and "ts" in v
                }
            else:
                self._data = {}
        except FileNotFoundError:
            self._data = {}
        except (OSError, ValueError) as e:
            logger.warning("Poster cache unreadable (%s) — starting empty", e)
            self._data = {}
        return self._data

    def get(self, key: str) -> str | None:
        """Return the cached URL, or ``None`` for miss/expiry.

        Note: ``None`` is also a legitimate cached value (lookup ran and
        found no poster) — callers distinguish via :meth:`__contains`.
        """
        entry = self._load().get(key)
        if entry is None:
            return None
        if self._now() - float(entry["ts"]) > self.ttl:
            return None
        url = entry["url"]
        if not isinstance(url, str):
            return None
        return url

    def __contains__(self, key: str) -> bool:
        entry = self._load().get(key)
        if entry is None:
            return False
        return bool(self._now() - float(entry["ts"]) <= self.ttl)

    def set(self, key: str, url: str | None) -> None:
        """Record ``url`` (may be ``None`` = negative result) under ``key``."""
        data = self._load()
        data[key] = {"url": url, "ts": self._now()}
        self._save()

    def prune(self) -> int:
        """Drop expired entries; returns how many were removed."""
        data = self._load()
        cutoff = self._now() - self.ttl
        expired = [k for k, v in data.items() if float(v["ts"]) < cutoff]
        for k in expired:
            del data[k]
        if expired:
            self._save()
        return len(expired)

    def _save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".json.tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._data or {}, f, ensure_ascii=False)
            tmp.replace(self.path)
        except (OSError, ValueError) as e:
            logger.warning("Could not persist poster cache (%s)", e)


# Process-wide instance; Streamlit reruns share it across sessions.
_cache: PosterTTLCache | None = None


def get_cache() -> PosterTTLCache:
    """Return the shared cache instance (lazy so tests can swap the path)."""
    global _cache
    if _cache is None:
        _cache = PosterTTLCache()
    return _cache


def cached_poster(title: str, year: int | None = None) -> tuple[bool, str | None]:
    """Look up ``title``/``year`` in the disk cache.

    Returns ``(found, url)`` — ``found=False`` means miss/expiry (caller
    should fetch), ``found=True`` with ``url=None`` is a cached negative.
    """
    key = poster_cache_key(title, year)
    cache = get_cache()
    if key in cache:
        return True, cache.get(key)
    return False, None


def remember_poster(title: str, year: int | None = None, url: str | None = None) -> None:
    """Persist a lookup result (including negatives) to the disk cache."""
    get_cache().set(poster_cache_key(title, year), url)
