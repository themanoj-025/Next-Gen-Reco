import streamlit as st

from app.ui.poster_utils import _genre_chip_class, _movie_poster_html, _rating_color


def render_comparison():
    st.markdown(
        '<div class="section-title"><span class="icon">⚖️</span> Movie Comparison</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-subtitle">Compare two movies side by side</div>',
        unsafe_allow_html=True,
    )

    rec = st.session_state.recommender

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Movie 1")
        q1 = st.text_input("Search first movie:", key="comp_q1", placeholder="Type movie name...")
        if q1 and len(q1) >= 2:
            results1 = rec.search_movies(q1.strip(), limit=5)
            for r in results1:
                if st.button(f"🎬 {r['title']}", key=f"comp1_{r['movieId']}"):
                    # Keep only the most recent 2 selections
                    current = st.session_state.comparison_ids
                    if len(current) >= 2:
                        current = current[-1:]  # drop oldest
                    st.session_state.comparison_ids = list(set(current) | {r["movieId"]})
                    st.rerun()

    with col2:
        st.markdown("#### Movie 2")
        q2 = st.text_input("Search second movie:", key="comp_q2", placeholder="Type movie name...")
        if q2 and len(q2) >= 2:
            results2 = rec.search_movies(q2.strip(), limit=5)
            for r in results2:
                if st.button(f"🎬 {r['title']}", key=f"comp2_{r['movieId']}"):
                    # Keep only the most recent 2 selections
                    current = st.session_state.comparison_ids
                    if len(current) >= 2:
                        current = current[-1:]
                    st.session_state.comparison_ids = list(set(current) | {r["movieId"]})
                    st.rerun()

    if st.session_state.comparison_ids:
        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

        # Show selected movie chips
        chips = []
        for mid in st.session_state.comparison_ids:
            info = rec.get_movie_info(mid)
            if info:
                chips.append(f'<span class="info-badge">{info["title"][:30]}</span>')
        if chips:
            st.markdown(
                f'<div style="margin-bottom:0.5rem;">Selected: {" vs ".join(chips)}</div>',
                unsafe_allow_html=True,
            )

        if st.button("🔄 Clear Comparison", use_container_width=False):
            st.session_state.comparison_ids = []
            st.rerun()

        # Show comparison if we have 2 movies
        ids = st.session_state.comparison_ids
        if len(ids) >= 2:
            id1, id2 = ids[0], ids[1]
            info1 = rec.get_movie_info(id1)
            info2 = rec.get_movie_info(id2)

            if info1 and info2:
                col_a, col_b = st.columns(2)

                for col, info in [(col_a, info1), (col_b, info2)]:
                    with col:
                        mid = info["movieId"]
                        r_pred = info["predicted_rating"]
                        r_pred_str = f"{r_pred:.2f}" if r_pred is not None else "N/A"
                        r_color = _rating_color(r_pred)
                        r_year = f"({info['year']})" if info.get("year") else ""

                        gcs = "".join(
                            f'<span class="genre-chip {_genre_chip_class(g)}" style="font-size:0.7rem;padding:0.15rem 0.5rem;margin:0.1rem 0.2rem;">{g}</span>'
                            for g in info["genres"]
                        )

                        st.markdown(
                            _movie_poster_html(mid, info["title"], info.get("year"), size="80%"),
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f"""
                        <div style="margin-top:0.5rem;">
                            <div style="font-size:1.2rem;font-weight:700;color:var(--text-primary);">{info["title"]}</div>
                            <div style="color:var(--text-muted);">{r_year}</div>
                            <div style="margin:0.5rem 0;">{gcs}</div>
                            <div style="font-size:2rem;font-weight:800;color:{r_color};">{r_pred_str}
                                <span style="font-size:0.9rem;font-weight:400;color:var(--text-muted-2);"> /5.0</span>
                            </div>
                            <div style="margin-top:0.5rem;font-size:0.85rem;color:var(--text-secondary);">
                                Genres: {len(info["genres"])} | Year: {info["year"] or "N/A"}
                            </div>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                        if st.button("Select", key=f"comp_sel_{mid}"):
                            st.session_state.selected_movie_id = mid
                            st.session_state.search_query = info["title"]
                            st.rerun()

                # Show prediction difference
                if info1["predicted_rating"] is not None and info2["predicted_rating"] is not None:
                    diff = info1["predicted_rating"] - info2["predicted_rating"]
                    if abs(diff) > 0.01:
                        winner = info1["title"] if diff > 0 else info2["title"]
                        st.markdown(
                            f'<div style="text-align:center;padding:1rem;color:var(--text-secondary);font-size:1rem;">'
                            f'📊 <strong style="color:var(--star-color);">{winner}</strong> predicted '
                            f'<strong style="color:{"#22c55e" if diff > 0 else "#ef4444"};">{abs(diff):.2f}</strong> points higher'
                            f"</div>",
                            unsafe_allow_html=True,
                        )


# ── Dashboard ─────────────────────────────────────────────────────────────────
