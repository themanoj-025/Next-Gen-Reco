"""Personalized recommendations page."""

import streamlit as st

from app.ui.poster_utils import _genre_chip_class, _rating_color


def render_for_you() -> None:
    st.markdown(
        '<div class="section-title"><span class="icon">❤️</span> For You</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-subtitle">Personalized recommendations based on your ratings</div>',
        unsafe_allow_html=True,
    )

    rec = st.session_state.recommender
    ratings = st.session_state.user_ratings

    if len(ratings) < 2:
        st.markdown(
            '<div class="empty-state"><div class="icon">❤️</div>'
            '<div class="text">Rate at least 2 movies to get personalized recommendations! '
            "Movies you rate highly will be used to find similar content you might like.</div></div>",
            unsafe_allow_html=True,
        )
        return

    # Get highly rated movies (4+)
    high_rated = {mid: r for mid, r in ratings.items() if r >= 4}

    if not high_rated:
        st.markdown(
            '<div class="empty-state"><div class="icon">❤️</div>'
            '<div class="text">Rate some movies at 4★ or 5★ to get personalized recommendations!</div></div>',
            unsafe_allow_html=True,
        )
        return

    with st.spinner("Computing personalized recommendations..."):
        # Collect recommendations from highly rated movies
        all_recs = []
        seen_ids = set()

        for mid in high_rated:
            # Skip movies the user already rated
            if mid in seen_ids:
                continue
            seen_ids.add(mid)

            recs = rec.recommend(mid, n=5)
            for r in recs:
                rid = r["movieId"]
                if rid not in ratings and rid not in seen_ids:
                    weight = high_rated.get(mid, 3) / 5.0
                    r["_score"] = r["similarity"] * weight
                    all_recs.append(r)
                    seen_ids.add(rid)

        # Sort by score
        all_recs.sort(key=lambda x: x.get("_score", 0), reverse=True)

        if not all_recs:
            st.info("No personalized recommendations found yet. Rate more movies!")
            return

        st.markdown(
            f'<div style="color:var(--text-muted-2);font-size:0.8rem;margin-bottom:1rem;">'
            f"Based on your {len(high_rated)} highest-rated movies. Showing top picks:</div>",
            unsafe_allow_html=True,
        )

        cols = st.columns(4)
        for i, r in enumerate(all_recs[:12]):
            with cols[i % 4]:
                r_pred = r["predicted_rating"]
                r_pred_str = f"{r_pred:.2f}" if r_pred is not None else "N/A"
                r_color = _rating_color(r_pred)
                r_year = f"({r['year']})" if r["year"] else ""

                r_title = r["title"]
                if len(r_title) > 35:
                    r_title = r_title[:32] + "..."

                gcs = "".join(
                    f'<span class="genre-chip {_genre_chip_class(g)}" style="font-size:0.6rem;padding:0.1rem 0.4rem;margin:0.1rem 0.1rem;">{g[:5]}</span>'
                    for g in r["genres"][:2]
                )

                wl_badge = " 📋" if r["movieId"] in st.session_state.watchlist else ""

                st.markdown(
                    f"""
                <div class="sim-card" style="cursor:pointer;">
                    <div class="sim-card-title">{r_title}{wl_badge}</div>
                    <div class="sim-card-year">{r_year}</div>
                    <div class="sim-card-genres">{gcs}</div>
                    <div class="sim-card-rating" style="color:{r_color};">{r_pred_str}
                        <span style="font-size:0.7rem;font-weight:400;color:var(--text-muted-2);"> /5.0</span>
                    </div>
                    <div class="sim-card-sim">Match: {r["_score"] * 100:.0f}%</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                if st.button("View", key=f"foryou_btn_{r['movieId']}_{i}"):
                    st.session_state.selected_movie_id = r["movieId"]
                    st.session_state.search_query = r["title"]
                    st.rerun()


# ── Export Recommendations ────────────────────────────────────────────────────
