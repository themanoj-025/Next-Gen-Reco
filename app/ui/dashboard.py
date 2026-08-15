"""
MovieLens AI Dashboard — Redesigned
====================================
Clean, modern dashboard with smooth transitions, semantic HTML5,
and a focused layout centered on user ratings and watchlist.
"""

import csv
import io

import streamlit as st

from app.data.loader import _save_user_data
from app.ui.components import WATCHLIST_CATEGORIES
from app.ui.poster_utils import _genre_chip_class, _rating_color


def _stars_display(rating: float | None) -> str:
    if rating is None:
        return ""
    full = int(rating)
    half = 1 if rating - full >= 0.25 and rating - full < 0.75 else 0
    empty = 5 - full - half
    return "★" * full + ("½" if half else "") + "☆" * empty


def _render_empty_state(icon: str, text: str, hint: str = ""):
    st.markdown(
        f"""<article class="dash-empty" role="status">
            <div class="dash-empty-icon">{icon}</div>
            <p class="dash-empty-text">{text}</p>
            {f'<p class="dash-empty-hint">{hint}</p>' if hint else ""}
        </article>""",
        unsafe_allow_html=True,
    )


def render_dashboard():
    rec = st.session_state.recommender
    ratings = st.session_state.user_ratings
    watchlist = st.session_state.watchlist

    avg_rating = sum(ratings.values()) / len(ratings) if ratings else 0
    avg_color = _rating_color(avg_rating) if ratings else "#888"

    # ════════════════════════════════════════════════════════════════
    # HEADER
    # ════════════════════════════════════════════════════════════════

    st.markdown(
        """
    <header class="dash-header">
        <h1 class="dash-title">👤 My Dashboard</h1>
        <p class="dash-subtitle">Your ratings, watchlist & personal stats</p>
    </header>
    """,
        unsafe_allow_html=True,
    )

    # ════════════════════════════════════════════════════════════════
    # STAT CARDS — simple, clean glass-morphism
    # ════════════════════════════════════════════════════════════════

    high_faves = sum(1 for v in ratings.values() if v >= 4) if ratings else 0

    st.markdown(
        f"""
    <section class="dash-stats" aria-label="Quick stats">
        <article class="dash-stat dash-stat--gold">
            <span class="dash-stat-icon">⭐</span>
            <span class="dash-stat-value">{len(ratings)}</span>
            <span class="dash-stat-label">Rated</span>
        </article>
        <article class="dash-stat dash-stat--green">
            <span class="dash-stat-icon">🎯</span>
            <span class="dash-stat-value" style="color:{avg_color}">{avg_rating:.1f}<small>/5</small></span>
            <span class="dash-stat-label">Avg Rating</span>
        </article>
        <article class="dash-stat dash-stat--blue">
            <span class="dash-stat-icon">📋</span>
            <span class="dash-stat-value">{len(watchlist)}</span>
            <span class="dash-stat-label">Watchlist</span>
        </article>
        <article class="dash-stat dash-stat--purple">
            <span class="dash-stat-icon">🏆</span>
            <span class="dash-stat-value">{high_faves}</span>
            <span class="dash-stat-label">Faves (4★+)</span>
        </article>
    </section>
    """,
        unsafe_allow_html=True,
    )

    # ════════════════════════════════════════════════════════════════
    # TABS
    # ════════════════════════════════════════════════════════════════

    tab_ratings, tab_watchlist, tab_settings = st.tabs(
        ["⭐ My Ratings", "📋 Watchlist", "⚙️ Settings"]
    )

    # ──────────────────────────────────────────────────────────────────
    # TAB 1: MY RATINGS
    # ──────────────────────────────────────────────────────────────────

    with tab_ratings:
        if not ratings:
            _render_empty_state(
                "⭐",
                "You haven't rated any movies yet.",
                "Search for a movie and click a star to rate it!",
            )
        else:
            sorted_ratings = sorted(ratings.items(), key=lambda x: (-x[1], x[0]))

            # Summary line
            st.markdown(
                f'<p class="dash-summary">{len(ratings)} movie{"s" if len(ratings) != 1 else ""} rated · Avg: '
                f'<strong style="color:{avg_color}">{avg_rating:.1f}</strong>/5.0</p>',
                unsafe_allow_html=True,
            )

            # Rating distribution — animated mini bars
            dist_counts = {r: sum(1 for v in ratings.values() if v == r) for r in range(5, 0, -1)}
            bars_html = ""
            for rval in range(5, 0, -1):
                count = dist_counts.get(rval, 0)
                pct = count / len(ratings) * 100 if ratings else 0
                bar_color = (
                    "#22c55e"
                    if rval >= 4
                    else "#fbbf24" if rval >= 3 else "#f97316" if rval >= 2 else "#ef4444"
                )
                bars_html += f"""
                <figure class="dash-dist-bar">
                    <figcaption class="dash-dist-count">{count}</figcaption>
                    <div class="dash-dist-track">
                        <div class="dash-dist-fill" style="height:{max(pct, 3)}%;background:{bar_color}"></div>
                    </div>
                    <figcaption class="dash-dist-label">{rval}★</figcaption>
                </figure>"""

            st.markdown(
                f'<nav class="dash-dist" aria-label="Rating distribution">{bars_html}</nav>',
                unsafe_allow_html=True,
            )

            # Movie cards grid
            cards_html = ""
            buttons_data = []
            for i, (mid, rval) in enumerate(sorted_ratings):
                info = rec.get_movie_info(mid)
                if not info:
                    continue
                r_color = _rating_color(rval)
                r_year = f"({info['year']})" if info.get("year") else ""
                r_title = info["title"][:30] + "…" if len(info["title"]) > 30 else info["title"]
                pred = info["predicted_rating"]
                stars = "★" * rval + "☆" * (5 - rval)
                gcs = "".join(
                    f'<span class="genre-chip {_genre_chip_class(g)} dash-chip-mini">{g[:5]}</span>'
                    for g in info["genres"][:2]
                )

                cards_html += f"""
                <article class="dash-movie-card" style="animation-delay:{0.04 * i}s">
                    <header class="dash-movie-card-header">
                        <h3 class="dash-movie-card-title">{r_title}</h3>
                        <span class="dash-movie-card-year">{r_year}</span>
                    </header>
                    <div class="dash-movie-card-genres">{gcs}</div>
                    <div class="dash-movie-card-stars" style="color:{r_color}">{stars}</div>
                    <div class="dash-movie-card-rating" style="color:{r_color}">{rval}<small>/5</small></div>
                    <footer class="dash-movie-card-pred">Predicted: {f"{pred:.2f}" if pred else "N/A"}</footer>
                </article>"""
                buttons_data.append((mid, info["title"], i))

            st.markdown(
                f'<section class="dash-movie-grid" aria-label="Rated movies">{cards_html}</section>',
                unsafe_allow_html=True,
            )

            for mid, title, i in buttons_data:
                if st.button("View", key=f"dash_rate_{mid}_{i}", use_container_width=True):
                    st.session_state.selected_movie_id = mid
                    st.session_state.search_query = title
                    st.rerun()

    # ──────────────────────────────────────────────────────────────────
    # TAB 2: WATCHLIST
    # ──────────────────────────────────────────────────────────────────

    with tab_watchlist:
        if not watchlist:
            _render_empty_state(
                "📋",
                "Your watchlist is empty.",
                "Add movies by clicking the 📋 button on any movie!",
            )
        else:
            wl_categories: dict[str, list] = {cat: [] for cat in WATCHLIST_CATEGORIES}
            for mid, cat in watchlist.items():
                if cat in wl_categories:
                    wl_categories[cat].append(mid)

            category_icons = {"Want to Watch": "👀", "Watching": "📺", "Watched": "✅"}

            total_wl = len(watchlist)
            st.markdown(
                f'<p class="dash-summary">{total_wl} movie{"s" if total_wl != 1 else ""} in watchlist</p>',
                unsafe_allow_html=True,
            )

            for cat in WATCHLIST_CATEGORIES:
                mids = wl_categories.get(cat, [])
                if not mids:
                    continue
                icon = category_icons.get(cat, "📋")

                cards_html = ""
                wl_buttons = []
                for mid in sorted(mids):
                    info = rec.get_movie_info(mid)
                    if not info:
                        continue
                    r_pred = info["predicted_rating"]
                    r_color = _rating_color(r_pred)
                    r_year = f"({info['year']})" if info.get("year") else ""
                    r_title = info["title"][:30] + "…" if len(info["title"]) > 30 else info["title"]
                    stars = _stars_display(r_pred) if r_pred else ""
                    gcs = "".join(
                        f'<span class="genre-chip {_genre_chip_class(g)} dash-chip-mini">{g[:5]}</span>'
                        for g in info["genres"][:2]
                    )

                    cards_html += f"""
                    <article class="dash-movie-card" style="animation-delay:{0.04 * mids.index(mid)}s">
                        <header class="dash-movie-card-header">
                            <h3 class="dash-movie-card-title">{r_title}</h3>
                            <span class="dash-movie-card-year">{r_year}</span>
                        </header>
                        <div class="dash-movie-card-genres">{gcs}</div>
                        <div class="dash-movie-card-stars" style="color:{r_color}">{stars}</div>
                        <div class="dash-movie-card-rating" style="color:{r_color}">{f"{r_pred:.2f}" if r_pred else "N/A"}<small> /5</small></div>
                    </article>"""
                    wl_buttons.append((mid, info["title"], cat))

                st.markdown(
                    f"""
                <nav class="dash-wl-section" aria-label="{cat}">
                    <header class="dash-wl-header">
                        <span class="dash-wl-icon">{icon}</span>
                        <h3 class="dash-wl-title">{cat}</h3>
                        <span class="dash-wl-count">{len(mids)}</span>
                    </header>
                    <section class="dash-movie-grid">{cards_html}</section>
                </nav>
                """,
                    unsafe_allow_html=True,
                )

                for mid, title, wl_cat in wl_buttons:
                    act_cols = st.columns(2)
                    with act_cols[0]:
                        if st.button("View", key=f"wl_view_{mid}_{wl_cat}"):
                            st.session_state.selected_movie_id = mid
                            st.session_state.search_query = title
                            st.rerun()
                    with act_cols[1]:
                        if st.button("✕", key=f"wl_rem_{mid}_{wl_cat}"):
                            del st.session_state.watchlist[mid]
                            _save_user_data()
                            st.rerun()

    # ──────────────────────────────────────────────────────────────────
    # TAB 3: SETTINGS
    # ──────────────────────────────────────────────────────────────────

    with tab_settings:
        st.markdown(
            """
        <header class="dash-settings-header">
            <h2 class="dash-settings-title">⚙️ Settings & Data</h2>
            <p class="dash-settings-desc">Manage your personal data. These actions cannot be undone.</p>
        </header>
        """,
            unsafe_allow_html=True,
        )

        reset_cols = st.columns(4)
        with reset_cols[0]:
            if st.button("🗑️ Ratings", use_container_width=True, type="secondary"):
                st.session_state.user_ratings = {}
                _save_user_data()
                st.rerun()
        with reset_cols[1]:
            if st.button("🗑️ Watchlist", use_container_width=True, type="secondary"):
                st.session_state.watchlist = {}
                _save_user_data()
                st.rerun()
        with reset_cols[2]:
            if st.button("🗑️ History", use_container_width=True, type="secondary"):
                st.session_state.search_history = []
                st.session_state.tmdb_poster_cache = {}
                _save_user_data()
                st.rerun()
        with reset_cols[3]:
            if st.button("🔄 All", use_container_width=True, type="secondary"):
                st.session_state.user_ratings = {}
                st.session_state.watchlist = {}
                st.session_state.search_history = []
                st.session_state.tmdb_poster_cache = {}
                _save_user_data()
                st.rerun()

        st.markdown('<hr class="dash-divider">', unsafe_allow_html=True)

        st.markdown(
            """
        <header class="dash-export-header">
            <h3 class="dash-export-title">📥 Export</h3>
        </header>
        """,
            unsafe_allow_html=True,
        )

        if st.session_state.watchlist:
            wl_output = io.StringIO()
            wl_writer = csv.writer(wl_output)
            wl_writer.writerow(
                ["Movie ID", "Title", "Category", "Year", "Genres", "Predicted Rating"]
            )
            for mid, cat in sorted(st.session_state.watchlist.items()):
                info = rec.get_movie_info(mid)
                if info:
                    wl_writer.writerow(
                        [
                            mid,
                            info["title"],
                            cat,
                            info.get("year", ""),
                            "; ".join(info["genres"]),
                            (
                                f"{info['predicted_rating']:.2f}"
                                if info["predicted_rating"]
                                else "N/A"
                            ),
                        ]
                    )
            st.download_button(
                label="📥 Download Watchlist (CSV)",
                data=wl_output.getvalue(),
                file_name="my_watchlist.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.markdown(
                '<p class="dash-empty-hint">Nothing to export yet — add movies to your watchlist first.</p>',
                unsafe_allow_html=True,
            )

        if st.session_state.user_ratings:
            r_output = io.StringIO()
            r_writer = csv.writer(r_output)
            r_writer.writerow(
                [
                    "Movie ID",
                    "Title",
                    "Your Rating",
                    "Predicted Rating",
                    "Year",
                    "Genres",
                ]
            )
            for mid, rval in sorted(st.session_state.user_ratings.items()):
                info = rec.get_movie_info(mid)
                if info:
                    r_writer.writerow(
                        [
                            mid,
                            info["title"],
                            rval,
                            (
                                f"{info['predicted_rating']:.2f}"
                                if info["predicted_rating"]
                                else "N/A"
                            ),
                            info.get("year", ""),
                            "; ".join(info["genres"]),
                        ]
                    )
            st.download_button(
                label="⭐ Download Ratings (CSV)",
                data=r_output.getvalue(),
                file_name="my_ratings.csv",
                mime="text/csv",
                use_container_width=True,
            )
