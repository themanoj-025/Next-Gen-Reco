"""Shared UI components — modern glass-morphism design."""

import csv
import io

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.data.loader import _save_user_data
from app.ui.poster_utils import (
    _genre_chip_class,
    _movie_poster_html,
    _rating_color,
    _rating_stars,
)

# ── Helpers ───────────────────────────────────────────────────────────────────


def _stars_display(rating: float | None) -> str:
    if rating is None:
        return ""
    full = int(rating)
    half = 1 if rating - full >= 0.25 and rating - full < 0.75 else 0
    empty = 5 - full - half
    return "★" * full + ("½" if half else "") + "☆" * empty


# ── Rating Widget ─────────────────────────────────────────────────────────────


def render_rating_widget(movie_id: int):
    """Show interactive star rating for a movie with modern styling."""
    current = st.session_state.user_ratings.get(movie_id)

    st.markdown(
        """
    <div class="detail-side-widget">
        <div class="w-label">⭐ Your Rating</div>
    """,
        unsafe_allow_html=True,
    )

    cols = st.columns(5)
    rating_changed = False
    for i in range(5):
        val = i + 1
        is_filled = current is not None and val <= current
        star = "★" if is_filled else "☆"
        with cols[i]:
            if st.button(
                star,
                key=f"rate_{movie_id}_{val}",
                use_container_width=True,
                help=f"Rate {val}/5",
            ):
                if current == val:
                    del st.session_state.user_ratings[movie_id]
                else:
                    st.session_state.user_ratings[movie_id] = val
                rating_changed = True
                _save_user_data()

    if current:
        r_color = _rating_color(current)
        st.markdown(
            f'<div style="color:var(--text-muted);font-size:0.8rem;">'
            f'<span style="color:{r_color};">{"★" * current}{"☆" * (5 - current)}</span> ({current}/5)</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="color:var(--text-muted-2);font-size:0.75rem;">Click a star to rate</div>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    if rating_changed:
        st.rerun()


# ── Watchlist button ──────────────────────────────────────────────────────────

WATCHLIST_CATEGORIES = ["Want to Watch", "Watching", "Watched"]


def render_watchlist_button(movie_id: int):
    in_wl = movie_id in st.session_state.watchlist

    if not in_wl:
        if st.button("📋 Add to Watchlist", key=f"wl_add_{movie_id}", use_container_width=True):
            st.session_state.watchlist[movie_id] = "Want to Watch"
            _save_user_data()
            st.rerun()
    else:
        current_cat = st.session_state.watchlist[movie_id]
        st.markdown(
            f'<div style="margin-bottom:0.3rem;color:var(--text-muted);font-size:0.8rem;">'
            f'📋 In Watchlist: <strong style="color:#fbbf24;">{current_cat}</strong></div>',
            unsafe_allow_html=True,
        )

        new_cat = st.selectbox(
            "Status",
            WATCHLIST_CATEGORIES,
            index=(
                WATCHLIST_CATEGORIES.index(current_cat)
                if current_cat in WATCHLIST_CATEGORIES
                else 0
            ),
            key=f"wl_cat_{movie_id}",
            label_visibility="collapsed",
        )
        if new_cat != current_cat:
            st.session_state.watchlist[movie_id] = new_cat
            _save_user_data()
            st.rerun()

        if st.button(
            "🗑️ Remove",
            key=f"wl_rem_{movie_id}",
            use_container_width=True,
            type="secondary",
        ):
            del st.session_state.watchlist[movie_id]
            _save_user_data()
            st.rerun()


# ── Movie Detail ──────────────────────────────────────────────────────────────


def render_movie_detail(movie_id: int):
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


def render_similar_movies(movie_id: int, info: dict, recs: list):
    if not recs:
        st.info("No similar movies found.")
        return

    st.markdown(
        f"""
    <div class="dash-section-header">
        <span class="h-icon">🎯</span>
        <span class="h-title">Similar Movies</span>
        <span class="h-subtitle">Because you searched for "{info["title"]}"</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sim-card-grid">', unsafe_allow_html=True)
    for i, r in enumerate(recs[:12]):
        r_pred = r["predicted_rating"]
        r_color = _rating_color(r_pred)
        r_year = f"({r['year']})" if r["year"] else "—"
        r_title = r["title"][:40] + "…" if len(r["title"]) > 40 else r["title"]

        sim_pct = f"{r['similarity'] * 100:.0f}%"
        stars = _stars_display(r_pred) if r_pred else ""

        gcs = "".join(
            f'<span class="genre-chip {_genre_chip_class(g)}" style="font-size:0.55rem;padding:0.1rem 0.4rem;margin:0.1rem 0.1rem;">{g[:6]}</span>'
            for g in r["genres"][:3]
        )

        wl_badge = (
            ' <span class="sc-badge">📋</span>'
            if r["movieId"] in st.session_state.watchlist
            else ""
        )
        ur_badge = ""
        if r["movieId"] in st.session_state.user_ratings:
            ur_badge = (
                f' <span class="sc-badge">⭐{st.session_state.user_ratings[r["movieId"]]}</span>'
            )

        st.markdown(
            f"""
        <div class="sim-card-new" style="animation-delay:{0.05 * i}s;" data-mid="{r["movieId"]}">
            <div class="sc-title">{r_title}{wl_badge}{ur_badge}</div>
            <div class="sc-year">{r_year}</div>
            <div class="sc-genres">{gcs}</div>
            {f'<div style="font-size:0.85rem;letter-spacing:1px;color:{r_color};">{stars}</div>' if stars else ""}
            <div class="sc-rating" style="color:{r_color};">{r_pred:.2f if r_pred else "N/A"}<span class="sc-max"> /5.0</span></div>
            <div class="sc-sim">Match: {sim_pct}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        act_cols = st.columns(2)
        with act_cols[0]:
            if st.button("Select", key=f"rec_btn_{r['movieId']}_{i}"):
                st.session_state.selected_movie_id = r["movieId"]
                st.session_state.search_query = r["title"]
                st.rerun()
        with act_cols[1]:
            wl_label = "➖" if r["movieId"] in st.session_state.watchlist else "➕"
            if st.button(wl_label, key=f"rec_wl_{r['movieId']}_{i}", help="Toggle watchlist"):
                if r["movieId"] in st.session_state.watchlist:
                    del st.session_state.watchlist[r["movieId"]]
                else:
                    st.session_state.watchlist[r["movieId"]] = "Want to Watch"
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# ── Feature Explanation ───────────────────────────────────────────────────────


def render_feature_explanation(movie_id: int):
    rec = st.session_state.recommender
    fb = rec.get_feature_breakdown(movie_id)
    if fb is None or fb.get("explanation") is None:
        st.markdown(
            '<div style="color:var(--text-muted-2);padding:1rem;">Feature breakdown not available for this movie.</div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        """
    <div class="dash-section-header">
        <span class="h-icon">🔬</span>
        <span class="h-title">Prediction Breakdown</span>
        <span class="h-subtitle">How each feature contributes to the predicted rating</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

    explanation = fb["explanation"]
    st.code(explanation, language="text")


# ── Metrics ───────────────────────────────────────────────────────────────────


def render_metrics_card(info: dict):
    pred = info["predicted_rating"]
    pred_color = "#22c55e" if pred and pred >= 3.5 else "#fbbf24" if pred else "#888"

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""
        <div class="dash-stat-glass" style="padding:1rem;text-align:center;">
            <div class="stat-glow"></div>
            <span class="stat-icon" style="font-size:1.2rem;">⭐</span>
            <div class="stat-value" style="font-size:1.8rem;color:{pred_color};">{pred:.2f if pred else "N/A"}</div>
            <div class="stat-label">Predicted Rating</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
        <div class="dash-stat-glass" style="padding:1rem;text-align:center;">
            <div class="stat-glow"></div>
            <span class="stat-icon" style="font-size:1.2rem;">🎨</span>
            <div class="stat-value" style="font-size:1.8rem;">{len(info["genres"])}</div>
            <div class="stat-label">Genres</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
        <div class="dash-stat-glass" style="padding:1rem;text-align:center;">
            <div class="stat-glow"></div>
            <span class="stat-icon" style="font-size:1.2rem;">📅</span>
            <div class="stat-value" style="font-size:1.8rem;">{info["year"] if info["year"] else "—"}</div>
            <div class="stat-label">Release Year</div>
        </div>
        """,
            unsafe_allow_html=True,
        )


# ── Visualization Charts ──────────────────────────────────────────────────────


def render_visualization_charts(movie_id: int, info: dict, recs: list):
    if info is None:
        return

    st.markdown(
        """
    <div class="dash-section-header">
        <span class="h-icon">📊</span>
        <span class="h-title">Analysis</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

    tab1, tab2 = st.tabs(["Genre Distribution", "Rating Comparison"])

    with tab1:
        genres = info["genres"]
        genre_counts = {}
        for r in recs:
            for g in r["genres"]:
                genre_counts[g] = genre_counts.get(g, 0) + 1

        all_genre_set = list(set(genres + list(genre_counts.keys())))
        df_genres = pd.DataFrame(
            {
                "Genre": all_genre_set,
                "In This Movie": [1 if g in genres else 0 for g in all_genre_set],
                "In Similar Movies": [genre_counts.get(g, 0) for g in all_genre_set],
            }
        ).sort_values("In Similar Movies", ascending=True)

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                y=df_genres["Genre"],
                x=df_genres["In This Movie"],
                name="This Movie",
                orientation="h",
                marker=dict(color="#f7971e", line=dict(color="#ffd200", width=1)),
                text=df_genres["In This Movie"],
                textposition="outside",
            )
        )
        fig.add_trace(
            go.Bar(
                y=df_genres["Genre"],
                x=df_genres["In Similar Movies"],
                name="In Similar Movies",
                orientation="h",
                marker=dict(
                    color="rgba(96,165,250,0.6)",
                    line=dict(color="rgba(96,165,250,0.8)", width=1),
                ),
                text=df_genres["In Similar Movies"],
                textposition="outside",
            )
        )
        fig.update_layout(
            barmode="group",
            height=350,
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="rgba(255,255,255,0.7)", size=11),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(color="rgba(255,255,255,0.6)", size=10),
            ),
            xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", title="Count"),
            yaxis=dict(title="", gridcolor="rgba(255,255,255,0.05)"),
            hoverlabel=dict(bgcolor="rgba(30,30,60,0.95)", font=dict(color="white", size=12)),
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        if not recs:
            st.info("No recommendations to compare.")
        else:
            rec_df = pd.DataFrame(recs)
            rec_df["display"] = rec_df["title"].apply(lambda x: x[:30] + "…" if len(x) > 30 else x)

            this_pred = info["predicted_rating"]
            all_data = pd.DataFrame(
                [
                    {
                        "Movie": f"📌 {info['title'][:30]}",
                        "Rating": this_pred,
                        "Type": "This Movie",
                    }
                ]
                + [
                    {
                        "Movie": r["display"],
                        "Rating": r["predicted_rating"],
                        "Type": "Similar",
                    }
                    for r in recs[:8]
                    if r["predicted_rating"] is not None
                ]
            )

            fig2 = go.Figure()
            colors_list = [
                "#f7971e" if t == "This Movie" else "rgba(96,165,250,0.5)" for t in all_data["Type"]
            ]
            fig2.add_trace(
                go.Bar(
                    x=all_data["Movie"],
                    y=all_data["Rating"],
                    marker=dict(
                        color=colors_list,
                        line=dict(color="rgba(255,255,255,0.1)", width=1),
                    ),
                    text=all_data["Rating"].apply(lambda x: f"{x:.2f}"),
                    textposition="outside",
                    hovertemplate="%{x}<br>Rating: %{y:.2f}<extra></extra>",
                )
            )
            fig2.update_layout(
                height=350,
                margin=dict(l=0, r=0, t=10, b=60),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="rgba(255,255,255,0.7)", size=10),
                xaxis=dict(showgrid=False, tickangle=45, title=""),
                yaxis=dict(
                    showgrid=True,
                    gridcolor="rgba(255,255,255,0.05)",
                    title="Predicted Rating",
                    range=[0, 5.5],
                ),
                hoverlabel=dict(bgcolor="rgba(30,30,60,0.95)", font=dict(color="white", size=12)),
            )
            st.plotly_chart(fig2, use_container_width=True)


# ── Similarity Breakdown ──────────────────────────────────────────────────────


def render_similarity_breakdown(movie_id: int, recs: list):
    if not recs:
        return

    st.markdown(
        """
    <div class="dash-section-header">
        <span class="h-icon">📐</span>
        <span class="h-title">Similarity Breakdown</span>
        <span class="h-subtitle">How each recommendation scored across similarity dimensions</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

    data = []
    for r in recs[:8]:
        display = r["title"][:35] + "…" if len(r["title"]) > 35 else r["title"]
        data.append(
            {
                "Movie": display,
                "Genre Match": r["genre_similarity"],
                "Tag Match": r["tag_similarity"],
                "Year Proximity": r["year_proximity"],
            }
        )

    df_sim = pd.DataFrame(data)
    fig = go.Figure()
    for col, color in [
        ("Genre Match", "#f7971e"),
        ("Tag Match", "#60a5fa"),
        ("Year Proximity", "#34d399"),
    ]:
        fig.add_trace(
            go.Bar(
                name=col,
                x=df_sim["Movie"],
                y=df_sim[col],
                marker=dict(color=color, opacity=0.85),
                text=df_sim[col].apply(lambda x: f"{x:.0%}"),
                textposition="inside",
                textfont=dict(size=9, color="white"),
            )
        )

    fig.update_layout(
        barmode="group",
        height=300,
        margin=dict(l=0, r=0, t=10, b=60),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="rgba(255,255,255,0.7)", size=10),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color="rgba(255,255,255,0.6)", size=10),
        ),
        xaxis=dict(showgrid=False, tickangle=45, title=""),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.05)",
            title="Similarity Score",
            tickformat=".0%",
            range=[0, 1.1],
        ),
        hoverlabel=dict(bgcolor="rgba(30,30,60,0.95)", font=dict(color="white", size=12)),
    )
    st.plotly_chart(fig, use_container_width=True)


# ── Export ────────────────────────────────────────────────────────────────────


def render_export(movie_id: int, info: dict, recs: list):
    st.markdown(
        """
    <div class="dash-section-header">
        <span class="h-icon">📥</span>
        <span class="h-title">Export</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if not recs:
        st.info("No recommendations to export.")
        return

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Rank",
            "Movie ID",
            "Title",
            "Year",
            "Genres",
            "Similarity Score",
            "Predicted Rating",
            "Genre Similarity",
            "Tag Similarity",
            "Year Proximity",
        ]
    )

    for i, r in enumerate(recs):
        writer.writerow(
            [
                i + 1,
                r["movieId"],
                r["title"],
                r["year"] or "",
                "; ".join(r["genres"]),
                f"{r['similarity']:.2%}",
                f"{r['predicted_rating']:.2f}" if r["predicted_rating"] is not None else "N/A",
                f"{r['genre_similarity']:.2%}",
                f"{r['tag_similarity']:.2%}",
                f"{r['year_proximity']:.2%}",
            ]
        )

    csv_data = output.getvalue()

    st.download_button(
        label="📥 Download Recommendations as CSV",
        data=csv_data,
        file_name=f"recommendations_{info['title'][:30].replace(' ', '_').replace('/', '_')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.markdown(
        f'<div style="color:var(--text-muted-2);font-size:0.75rem;margin-top:0.3rem;">'
        f'Exports {len(recs)} recommendations for "{info["title"]}"</div>',
        unsafe_allow_html=True,
    )
