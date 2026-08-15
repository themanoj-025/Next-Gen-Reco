"""Poster, TMDB, and rating display utilities."""

import os

import requests
import streamlit as st
from dotenv import load_dotenv

# ── TMDB API (optional) ───────────────────────────────────────────────────────

load_dotenv()

TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "")
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
TMDB_SEARCH_BASE = "https://api.themoviedb.org/3/search/movie"


# ── Poster color palette ─────────────────────────────────────────────────────

POSTER_COLORS = [
    "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
    "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
    "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
    "linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)",
    "linear-gradient(135deg, #fccb90 0%, #d57eeb 100%)",
    "linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%)",
    "linear-gradient(135deg, #f5576c 0%, #ff6a88 100%)",
    "linear-gradient(135deg, #30cfd0 0%, #330867 100%)",
    "linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)",
    "linear-gradient(135deg, #5ee7df 0%, #b490ca 100%)",
    "linear-gradient(135deg, #d299c2 0%, #fef9d7 100%)",
    "linear-gradient(135deg, #f6d365 0%, #fda085 100%)",
    "linear-gradient(135deg, #96fbc4 0%, #f9f586 100%)",
    "linear-gradient(135deg, #fbab7e 0%, #f7ce68 100%)",
    "linear-gradient(135deg, #85ffbd 0%, #fffb7d 100%)",
    "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
    "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
]


def _poster_gradient(movie_id: int) -> str:
    """Get a consistent gradient color for a movie based on its ID."""
    return POSTER_COLORS[movie_id % len(POSTER_COLORS)]


def _poster_initials(title: str) -> str:
    """Get initials from a movie title for the poster."""
    clean = title.replace("'", "").replace('"', "")
    words = clean.split()[:3]
    initials = "".join(w[0].upper() for w in words if w and w[0].isalpha())
    return initials[:3] if initials else "🎬"


def _poster_html(movie_id: int, title: str, year: int | None = None, size: str = "100%") -> str:
    """Generate a styled poster placeholder HTML (gradient fallback)."""
    gradient = _poster_gradient(movie_id)
    initials = _poster_initials(title)
    year_str = f" ({year})" if year else ""
    return f"""
    <div class="movie-poster" style="background: {gradient}; width: {size};">
        {initials}
        <div class="poster-title">{title[:40]}{year_str}</div>
    </div>
    """


# ── TMDB Poster Integration (optional) ───────────────────────────────────────


# ── TMDB Poster Integration (optional) ───────────────────────────────────────


@st.cache_data(ttl=3600, max_entries=500)
def _tmdb_poster_cached(title: str, year: int | None = None) -> str | None:
    """Cached TMDB poster lookup. Reduces network calls on reruns."""
    api_key = TMDB_API_KEY
    if not api_key:
        return None
    try:
        params = {"query": title, "api_key": api_key, "language": "en-US"}
        if year:
            params["year"] = year
        resp = requests.get(TMDB_SEARCH_BASE, params=params, timeout=3)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if results:
            poster_path = results[0].get("poster_path")
            if poster_path:
                return f"{TMDB_IMAGE_BASE}{poster_path}"
        return None
    except Exception:
        return None


def _search_tmdb_poster(movie_id: int, title: str, year: int | None = None) -> str | None:
    """Search TMDB for a movie poster URL. Uses @st.cache_data for persistence."""
    cache = st.session_state.tmdb_poster_cache
    if movie_id in cache:
        return cache[movie_id]

    url = _tmdb_poster_cached(title, year)
    cache[movie_id] = url
    return url


def _movie_poster_html(
    movie_id: int, title: str, year: int | None = None, size: str = "100%"
) -> str:
    """Render movie poster — TMDB image if available and enabled, otherwise gradient placeholder."""
    if st.session_state.get("use_tmdb_posters", False):
        poster_url = _search_tmdb_poster(movie_id, title, year)
        if poster_url:
            return f"""
            <div class="tmdb-poster" style="width:{size};">
                <img src="{poster_url}" alt="{title}" loading="lazy">
            </div>
            """
    return _poster_html(movie_id, title, year, size)


# ── Rating & display helpers ─────────────────────────────────────────────────


def _rating_color(rating: float | None) -> str:
    if rating is None:
        return "#888"
    if rating >= 4.0:
        return "#22c55e"
    elif rating >= 3.0:
        return "#fbbf24"
    elif rating >= 2.0:
        return "#f97316"
    else:
        return "#ef4444"


def _rating_stars(rating: float | None) -> str:
    if rating is None:
        return "—"
    full = int(rating)
    half = 1 if rating - full >= 0.25 else 0
    empty = 5 - full - half
    return "★" * full + ("½" if half else "") + "☆" * empty


def _genre_chip_class(genre: str) -> str:
    genre_lower = genre.lower().replace("'", "").replace(" ", "")
    known = {
        "action": "action",
        "adventure": "adventure",
        "animation": "default",
        "children": "default",
        "comedy": "comedy",
        "crime": "thriller",
        "documentary": "documentary",
        "drama": "drama",
        "fantasy": "adventure",
        "filmnoir": "thriller",
        "horror": "horror",
        "musical": "default",
        "mystery": "thriller",
        "romance": "romance",
        "scifi": "scifi",
        "thriller": "thriller",
        "war": "action",
        "western": "default",
    }
    return known.get(genre_lower, "default")


# ── Session state ─────────────────────────────────────────────────────────────
