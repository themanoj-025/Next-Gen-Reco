"""
MovieLens AI - Streamlit Entry Point
=====================================
This is the main entry point for Streamlit Cloud hosting.
It directly imports all components and runs the app.
"""

import os
import sys

# Ensure project root is on sys.path for all imports
_project_root = os.path.dirname(os.path.abspath(__file__))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import logging
import warnings

warnings.filterwarnings("ignore")

# Surface the enrichment module's logs in the Streamlit terminal without
# altering Streamlit's own logging configuration.
_enrichment_logger = logging.getLogger("app.enrichment")
_enrichment_logger.setLevel(logging.INFO)
if not _enrichment_logger.handlers:
    _enrichment_handler = logging.StreamHandler()
    _enrichment_handler.setFormatter(
        logging.Formatter("%(levelname)s %(name)s: %(message)s")
    )
    _enrichment_logger.addHandler(_enrichment_handler)
_enrichment_logger.propagate = False

from datetime import datetime

import streamlit as st

from app.ui.combo_finder import render_combo_finder
from app.ui.compare import render_comparison
from app.ui.components import (
    render_export,
    render_feature_explanation,
    render_metrics_card,
    render_movie_detail,
    render_similar_movies,
    render_similarity_breakdown,
    render_visualization_charts,
)
from app.ui.dashboard import render_dashboard
from app.ui.decade_explorer import render_decade_explorer
from app.ui.explore import render_mood_explorer, render_surprise_me
from app.ui.for_you import render_for_you
from app.ui.home import render_home
from app.ui.movie_night import render_movie_night
from app.ui.poster_utils import _rating_color
from app.ui.search import render_search
from app.ui.session_utils import init_session
from app.ui.stats import render_movie_stats_section
from app.ui.styles import inject_css

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="MovieLens AI",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def render_header():
    """Render IMDb-style top nav bar and Streamlit-native navigation buttons."""
    theme = st.session_state.get("theme", "dark")
    inject_css(theme)

    st.markdown(
        """
    <div class="imdb-nav">
        <div class="imdb-nav-logo">🎬 MovieLens AI <span>| Predictor</span></div>
        <div class="imdb-nav-links">
            <span class="imdb-nav-link active">🏠 Home</span>
            <span class="imdb-nav-link">🔍 Search</span>
            <span class="imdb-nav-link">👤 Dashboard</span>
            <span class="imdb-nav-link">🎲 Surprise</span>
            <span class="imdb-nav-link">🎨 Genre</span>
            <span class="imdb-nav-link">⚖️ Compare</span>
            <span class="imdb-nav-link">❤️ For You</span>
            <span class="imdb-nav-link">📅 Decades</span>
            <span class="imdb-nav-link">🎯 Combo</span>
            <span class="imdb-nav-link">🎬 Movie Night</span>
        </div>
        <div class="imdb-nav-right">
            <span class="imdb-nav-user">👤 Guest</span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    current = st.session_state.get("active_tab", "Home")
    nav_items = [
        ("Home", "🏠"),
        ("Search", "🔍"),
        ("Dashboard", "👤"),
        ("Surprise", "🎲"),
        ("Genre", "🎨"),
        ("Compare", "⚖️"),
        ("For You", "❤️"),
        ("Decades", "📅"),
        ("Combo", "🎯"),
        ("Movie Night", "🎬"),
    ]
    cols = st.columns(len(nav_items))
    for i, (tab_key, icon) in enumerate(nav_items):
        with cols[i]:
            is_active = current == tab_key
            if is_active:
                st.markdown(
                    f'<div style="text-align:center;padding:0.3rem 0.2rem;background:rgba(245,197,24,0.1);border-radius:6px;color:#f5c518;font-size:0.75rem;font-weight:600;">{icon} {tab_key}</div>',
                    unsafe_allow_html=True,
                )
            else:
                if st.button(f"{icon} {tab_key}", key=f"nav_{tab_key}", use_container_width=True):
                    if tab_key == "Search":
                        st.session_state.active_tab = "Search"
                    else:
                        st.session_state.active_tab = tab_key
                    st.session_state.selected_movie_id = None
                    st.rerun()


def main():
    init_session()
    render_header()

    # Determine active page
    if st.session_state.selected_movie_id is not None:
        active_page = "detail"
    elif st.session_state.active_tab == "Search":
        active_page = "search"
    else:
        active_page = st.session_state.get("active_tab", "Home")

    # Sidebar
    with st.sidebar:
        st.session_state.get("theme", "dark")
        st.markdown('<div style="padding:0.5rem 0;">', unsafe_allow_html=True)
        st.markdown(
            '<div style="font-size:1.1rem;font-weight:700;color:#f5c518;margin-bottom:0.5rem;">🎬 Menu</div>',
            unsafe_allow_html=True,
        )

        nav_map = {
            "Home": "🏠 Home",
            "Search": "🔍 Search",
            "Dashboard": "👤 Dashboard",
            "Surprise": "🎲 Surprise",
            "Genre": "🎨 Genre",
            "Compare": "⚖️ Compare",
            "For You": "❤️ For You",
            "Decades": "📅 Decades",
            "Combo": "🎯 Combo",
            "Movie Night": "🎬 Movie Night",
        }
        for tab_key, tab_label in nav_map.items():
            is_active = active_page == tab_key or (active_page == "search" and tab_key == "Search")
            bt = "primary" if is_active else "secondary"
            if st.button(tab_label, key=f"side_{tab_key}", use_container_width=True, type=bt):
                if tab_key == "Search":
                    st.session_state.active_tab = "Search"
                else:
                    st.session_state.active_tab = tab_key
                st.session_state.selected_movie_id = None
                st.rerun()

        st.markdown(
            '<hr style="border-color:var(--sidebar-hr);margin:0.5rem 0;">',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div style="color:var(--text-muted);font-size:0.75rem;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.3rem;">Quick Stats</div>',
            unsafe_allow_html=True,
        )
        ur = len(st.session_state.user_ratings)
        wl = len(st.session_state.watchlist)
        avg_r = sum(st.session_state.user_ratings.values()) / ur if ur > 0 else 0
        is_dark = st.session_state.get("theme", "dark") == "dark"
        stat_color = "rgba(255,255,255,0.6)" if is_dark else "#475569"
        strong_color = "white" if is_dark else "#0f172a"
        st.markdown(
            f'<div class="sidebar-stat" style="font-size:0.85rem;color:{stat_color};margin:0.2rem 0;">⭐ Rated: <strong style="color:{strong_color};">{ur}</strong></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="sidebar-stat" style="font-size:0.85rem;color:{stat_color};margin:0.2rem 0;">📋 Watchlist: <strong style="color:{strong_color};">{wl}</strong></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="sidebar-stat" style="font-size:0.85rem;color:{stat_color};margin:0.2rem 0;">📊 Avg: <strong style="color:{_rating_color(avg_r) if ur > 0 else ("#888" if is_dark else "#64748b")};">{avg_r:.1f}</strong></div>',
            unsafe_allow_html=True,
        )

        # Theme toggle
        st.markdown(
            '<hr style="border-color:var(--border-color);margin:0.5rem 0;">',
            unsafe_allow_html=True,
        )
        theme = st.session_state.get("theme", "dark")
        theme_label = "🌙 Dark Mode" if theme == "dark" else "☀️ Light Mode"
        if st.button(theme_label, key="theme_toggle_btn", use_container_width=True):
            st.session_state.theme = "light" if theme == "dark" else "dark"
            st.rerun()

        st.markdown(
            '<hr style="border-color:var(--border-color);margin:0.5rem 0;">',
            unsafe_allow_html=True,
        )
        with st.expander("⚙️ Settings", expanded=False):
            tmdb_enabled = st.toggle(
                "TMDB Posters",
                value=st.session_state.get("use_tmdb_posters", False),
                key="sidebar_tmdb_toggle",
            )
            if tmdb_enabled != st.session_state.use_tmdb_posters:
                st.session_state.use_tmdb_posters = tmdb_enabled
                st.rerun()
            api_key = st.text_input(
                "TMDB API Key",
                value=st.session_state.get("tmdb_api_key", ""),
                type="password",
                key="sidebar_tmdb_key",
                placeholder="Env var or custom",
            )
            if api_key:
                st.session_state.tmdb_api_key = api_key

        st.markdown("</div>", unsafe_allow_html=True)

    # Main content area — with theme class wrapper
    theme_class = f"theme-{st.session_state.get('theme', 'dark')}"
    st.markdown(f'<div class="{theme_class}">', unsafe_allow_html=True)
    st.markdown('<div class="main-content">', unsafe_allow_html=True)

    if active_page == "detail":
        movie_id = st.session_state.selected_movie_id
        info = render_movie_detail(movie_id)
        if info:
            render_metrics_card(info)
            render_movie_stats_section(movie_id, info)
            rec = st.session_state.recommender
            with st.spinner("Finding similar movies..."):
                recs = rec.recommend(movie_id, n=12)
            render_similar_movies(movie_id, info, recs)
            render_visualization_charts(movie_id, info, recs)
            render_similarity_breakdown(movie_id, recs)
            render_feature_explanation(movie_id)
            render_export(movie_id, info, recs)

        if st.button("← Back to Home", key="back_home", use_container_width=False):
            st.session_state.selected_movie_id = None
            st.session_state.active_tab = "Home"
            st.rerun()

    elif active_page in ("search", "Search"):
        render_search()
    elif active_page in ("Dashboard",):
        render_dashboard()
    elif active_page in ("Surprise",):
        render_surprise_me()
    elif active_page in ("Genre",):
        render_mood_explorer()
    elif active_page in ("Compare",):
        render_comparison()
    elif active_page in ("For You",):
        render_for_you()
    elif active_page in ("Decades",):
        render_decade_explorer()
    elif active_page in ("Combo",):
        render_combo_finder()
    elif active_page in ("Movie Night",):
        render_movie_night()
    else:
        render_home()

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Footer
    st.markdown(
        f"""
    <div class="app-footer">
        <div class="app-footer-brand">🎬 MovieLens AI</div>
        <div class="app-footer-links">
            <a href="#">About</a>
            <a href="#">Movies</a>
            <a href="#">Genres</a>
            <a href="#">Top Picks</a>
            <a href="#">API</a>
            <a href="#">Help</a>
        </div>
        <div class="app-footer-copy">
            Using MovieLens 32M Dataset &bull; Random Forest &bull; XGBoost &bull; Content-Based Filtering<br>
            &copy; {datetime.now().year} MovieLens AI &mdash; Not affiliated with IMDb or MovieLens
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


# No __name__ guard needed — Streamlit always executes the main script directly
main()
