"""Info widgets -- feature explanation, metrics, similar movies, export."""

from __future__ import annotations

import csv
import io

import pandas as pd
import streamlit as st

from app.ui.poster_utils import _rating_color


def render_similar_movies(movie_id: int, info: dict, recs: list) -> None:
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



def render_feature_explanation(movie_id: int) -> None:
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



def render_metrics_card(info: dict) -> None:
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



def render_export(movie_id: int, info: dict, recs: list) -> None:
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
