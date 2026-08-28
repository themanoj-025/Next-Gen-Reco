"""Movie detail page layout."""

from __future__ import annotations

import streamlit as st

from app.ui.detail_widgets.rating_widgets import (
    render_rating_widget,
    render_watchlist_button,
)
from app.ui.poster_utils import (
    _genre_chip_class,
    _movie_poster_html,
    _rating_color,
    _rating_stars,
)


def render_movie_detail(movie_id: int) -> None:
    rec = st.session_state.recommender
    info = rec.get_movie_info(movie_id)
    if info is None:
        st.error("Movie not found.")
        return

    # Enrich with ND data
    info = rec.enrich_movie_info(info)

    title = info["title"]
    year = info["year"]
    genres = info["genres"]
    pred = info["predicted_rating"]

    year_str = f"({year})" if year else ""
    rating_color = _rating_color(pred)
    stars = _rating_stars(pred) if pred else "—"
    pred_str = f"{pred:.2f}" if pred is not None else "N/A"

    genre_chips = "".join(
        f'<span class="genre-chip {_genre_chip_class(g)}">{g}</span>' for g in genres
    )

    # Layout: poster on left, detail on right
    col_left, col_right = st.columns([1, 2.5])

    # ── Left column: Poster + actions ────────────────────────────────────
    with col_left:
        st.markdown(
            _movie_poster_html(movie_id, title, year, size="100%"),
            unsafe_allow_html=True,
        )

        # Watchlist widget
        st.markdown('<div class="detail-side-widget">', unsafe_allow_html=True)
        render_watchlist_button(movie_id)
        st.markdown("</div>", unsafe_allow_html=True)

        # Rating widget
        render_rating_widget(movie_id)

    # ── Right column: Movie info ────────────────────────────────────────
    with col_right:
        # Hero card
        st.markdown(
            f"""
        <div class="detail-hero">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:1.5rem;">
                <div style="flex:1;min-width:200px;">
                    <h2 class="movie-title-main">{title}<span class="year-badge">{year_str}</span></h2>
                    <div style="margin:0.6rem 0;">{genre_chips}</div>
                </div>
                <div style="display:flex;flex-direction:column;align-items:center;gap:0.3rem;min-width:120px;">
                    <div class="rating-badge" style="border-color:{rating_color}30;">
                        <div class="rb-value" style="color:{rating_color};">{pred_str}</div>
                        <div class="rb-label">Predicted /5</div>
                        <div class="rb-stars" style="color:{rating_color};">{stars}</div>
                    </div>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # ── Enriched metadata ────────────────────────────────────────────
        tagline = info.get("tagline", "")
        overview = info.get("overview", "")
        director = info.get("director", "")
        actors = info.get("actors", [])
        runtime = info.get("runtime")
        budget = info.get("budget")
        revenue = info.get("revenue")
        vote_avg = info.get("vote_average")

        # Tagline
        if tagline:
            st.markdown(
                f'<div class="detail-tagline">“{tagline}”</div>',
                unsafe_allow_html=True,
            )

        # Overview
        if overview:
            st.markdown(
                f'<div class="detail-overview">{overview[:2000]}{"…" if len(overview) > 2000 else ""}</div>',
                unsafe_allow_html=True,
            )

        # Stats row (runtime / budget / revenue / TMDB)
        stat_parts = []
        if runtime:
            h = runtime // 60
            m = runtime % 60
            runtime_str = f"{h}h {m}m" if h > 0 else f"{m}m"
            stat_parts.append(
                f'<span class="detail-stat-chip"><span class="chip-icon">⏱</span> {runtime_str}</span>'
            )
        if budget and budget > 0:
            budget_str = (
                f"${budget / 1_000_000:.0f}M" if budget >= 1_000_000 else f"${budget / 1_000:.0f}K"
            )
            stat_parts.append(
                f'<span class="detail-stat-chip"><span class="chip-icon">💰</span> {budget_str}</span>'
            )
        if revenue and revenue > 0:
            rev_str = (
                f"${revenue / 1_000_000:.0f}M"
                if revenue >= 1_000_000
                else f"${revenue / 1_000:.0f}K"
            )
            stat_parts.append(
                f'<span class="detail-stat-chip"><span class="chip-icon">💵</span> {rev_str}</span>'
            )
        if vote_avg:
            tmdb_color = "#01b4e4" if vote_avg >= 7 else "#fbbf24" if vote_avg >= 5 else "#ef4444"
            stat_parts.append(
                f'<span class="detail-stat-chip" style="color:{tmdb_color};"><span class="chip-icon">🎬</span> TMDB: {vote_avg:.1f}</span>'
            )
        if stat_parts:
            st.markdown(
                '<div class="detail-stats">' + "".join(stat_parts) + "</div>",
                unsafe_allow_html=True,
            )

        # Metadata rows
        st.markdown('<div style="margin:0.75rem 0;">', unsafe_allow_html=True)

        if director and director.lower() not in ("unknown", "nan", ""):
            st.markdown(
                f"""
            <div class="detail-meta-row">
                <span class="meta-label">🎬 Director</span>
                <span class="meta-value">{director}</span>
            </div>
            """,
                unsafe_allow_html=True,
            )

        if actors:
            cast_str = ", ".join(actors[:4])
            if len(actors) > 4:
                cast_str += f" <span style='color:var(--text-muted-2);font-size:0.8rem;'>+{len(actors) - 4} more</span>"
            st.markdown(
                f"""
            <div class="detail-meta-row">
                <span class="meta-label">🎭 Cast</span>
                <span class="meta-value">{cast_str}</span>
            </div>
            """,
                unsafe_allow_html=True,
            )

        prod = info.get("production_companies", "")
        if prod and prod.lower() != "nan":
            st.markdown(
                f"""
            <div class="detail-meta-row">
                <span class="meta-label">🎮 Studio</span>
                <span class="meta-value">{prod[:100]}{"…" if len(prod) > 100 else ""}</span>
            </div>
            """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

        # Keywords
        keywords = info.get("keywords", "")
        if keywords and keywords.lower() != "nan":
            kw_list = [k.strip() for k in keywords.split(",") if k.strip()][:12]
            if kw_list:
                kw_chips = "".join(f'<span class="detail-kw-chip">{k}</span>' for k in kw_list)
                st.markdown(
                    f'<div class="detail-kw-grid">{kw_chips}</div>',
                    unsafe_allow_html=True,
                )

        # User rating
        if movie_id in st.session_state.user_ratings:
            ur = st.session_state.user_ratings[movie_id]
            ur_color = _rating_color(ur)
            st.markdown(
                f'<div style="margin-top:0.5rem;font-size:0.85rem;color:var(--text-muted);">'
                f'Your Rating: <span style="color:{ur_color};">{"★" * ur}{"☆" * (5 - ur)} ({ur}/5)</span></div>',
                unsafe_allow_html=True,
            )

    # ── Director: More by this director ──────────────────────────────────
    if director and director.lower() not in ("unknown", "nan", ""):
        dir_movies = rec.get_movies_by_director(director)
        dir_movies = [m for m in dir_movies if m != movie_id][:8]
        if dir_movies:
            st.markdown(
                f"""
            <div class="dash-section-header" style="margin-top:2rem;">
                <span class="h-icon">🎬</span>
                <span class="h-title">More by {director}</span>
            </div>
            """,
                unsafe_allow_html=True,
            )

            st.markdown('<div class="detail-mini-grid">', unsafe_allow_html=True)
            for i, dir_mid in enumerate(dir_movies):
                dir_info = rec.get_movie_info(dir_mid)
                if dir_info:
                    d_pred = dir_info["predicted_rating"]
                    d_col = _rating_color(d_pred)
                    d_year = f"({dir_info['year']})" if dir_info.get("year") else "—"
                    d_title = (
                        dir_info["title"][:32] + "…"
                        if len(dir_info["title"]) > 32
                        else dir_info["title"]
                    )
                    gcs = "".join(
                        f'<span class="genre-chip {_genre_chip_class(g)}" style="font-size:0.5rem;padding:0.1rem 0.35rem;margin:0.05rem 0.1rem;">{g[:5]}</span>'
                        for g in dir_info["genres"][:2]
                    )
                    st.markdown(
                        f"""
                    <div class="detail-mini-card" data-mid="{dir_mid}">
                        <div class="dmc-title">{d_title}</div>
                        <div class="dmc-year">{d_year}</div>
                        <div>{gcs}</div>
                        <div class="dmc-rating" style="color:{d_col};">{d_pred:.2f if d_pred else "N/A"}<span class="dmc-max"> /5.0</span></div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
                    if st.button("View", key=f"dir_btn_{dir_mid}_{i}"):
                        st.session_state.selected_movie_id = dir_mid
                        st.session_state.search_query = dir_info["title"]
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # ── Actors: Featuring this actor ─────────────────────────────────────
    shown_actors = set()
    for actor in actors[:3]:
        if actor and actor.lower() not in ("unknown", "nan", "") and actor not in shown_actors:
            shown_actors.add(actor)
            act_movies = rec.get_movies_by_actor(actor)
            act_movies = [m for m in act_movies if m != movie_id][:6]
            if act_movies:
                st.markdown(
                    f"""
                <div class="dash-section-header" style="margin-top:2rem;">
                    <span class="h-icon">🎭</span>
                    <span class="h-title">Also starring {actor}</span>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                st.markdown('<div class="detail-mini-grid">', unsafe_allow_html=True)
                for j, act_mid in enumerate(act_movies):
                    act_info = rec.get_movie_info(act_mid)
                    if act_info:
                        a_pred = act_info["predicted_rating"]
                        a_col = _rating_color(a_pred)
                        a_year = f"({act_info['year']})" if act_info.get("year") else "—"
                        a_title = (
                            act_info["title"][:28] + "…"
                            if len(act_info["title"]) > 28
                            else act_info["title"]
                        )
                        st.markdown(
                            f"""
                        <div class="detail-mini-card" data-mid="{act_mid}">
                            <div class="dmc-title" style="font-size:0.8rem;">{a_title}</div>
                            <div class="dmc-year">{a_year}</div>
                            <div class="dmc-rating" style="color:{a_col};font-size:1rem;">{a_pred:.2f if a_pred else "N/A"}<span class="dmc-max"> /5.0</span></div>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )
                        if st.button("View", key=f"act_btn_{act_mid}_{actor}_{j}"):
                            st.session_state.selected_movie_id = act_mid
                            st.session_state.search_query = act_info["title"]
                            st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

    return info


# ── Similar Movies ────────────────────────────────────────────────────────────


