"""Combo finder page."""

import streamlit as st

from app.ui.poster_utils import _genre_chip_class, _rating_color


def render_combo_finder():
    st.markdown(
        '<div class="section-title"><span class="icon">🎯</span> Combo Finder</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-subtitle">Combine multiple criteria to find the perfect movie</div>',
        unsafe_allow_html=True,
    )

    rec = st.session_state.recommender
    all_genres = sorted(rec.genre_cols)

    with st.container():
        combo_col1, combo_col2 = st.columns(2)

        with combo_col1:
            selected_genre = st.selectbox(
                "🎭 Genre",
                ["Any Genre"] + all_genres,
                index=0,
                key="combo_genre",
            )

            director_name = st.text_input(
                "🎬 Director",
                placeholder="e.g. Christopher Nolan",
                key="combo_director",
            )

        with combo_col2:
            year_range = st.slider(
                "📅 Year Range",
                1900,
                2026,
                (1990, 2020),
                key="combo_year",
            )

            actor_name = st.text_input(
                "🎭 Actor",
                placeholder="e.g. Morgan Freeman",
                key="combo_actor",
            )

        rating_min = st.slider(
            "⭐ Minimum Predicted Rating",
            1.0,
            5.0,
            1.0,
            0.5,
            key="combo_rating",
        )

        sort_col1, sort_col2, sort_col3 = st.columns([1, 1, 1])
        with sort_col1:
            sort_by = st.selectbox(
                "Sort by",
                ["Predicted Rating", "Year", "Popularity"],
                index=0,
                key="combo_sort",
            )
        with sort_col2:
            combo_limit = st.number_input(
                "Max results",
                min_value=5,
                max_value=50,
                value=16,
                step=1,
                key="combo_limit",
            )
        with sort_col3:
            search_clicked = st.button("🔍 Search Combos", use_container_width=True, type="primary")

    if search_clicked:
        sort_map = {
            "Predicted Rating": "predicted_rating",
            "Year": "year",
            "Popularity": "popularity",
        }

        with st.spinner("🔍 Finding movies that match all your criteria..."):
            results = rec.find_movies_combo(
                genre=selected_genre if selected_genre != "Any Genre" else None,
                year_min=year_range[0],
                year_max=year_range[1],
                director=director_name.strip() if director_name.strip() else None,
                actor=actor_name.strip() if actor_name.strip() else None,
                rating_min=rating_min if rating_min > 1.0 else None,
                sort_by=sort_map.get(sort_by, "predicted_rating"),
                limit=int(combo_limit),
            )

        if not results:
            st.markdown(
                '<div class="empty-state"><div class="icon">🎯</div>'
                '<div class="text">No movies found matching all criteria. Try broadening your filters!</div></div>',
                unsafe_allow_html=True,
            )
            return

        st.markdown(
            f'<div style="color:var(--text-muted-2);font-size:0.85rem;margin-bottom:1rem;">'
            f"Found {len(results)} movies matching your criteria:</div>",
            unsafe_allow_html=True,
        )

        cols = st.columns(4)
        for i, info in enumerate(results):
            with cols[i % 4]:
                mid = info["movieId"]
                r_pred = info.get("predicted_rating")
                r_pred_str = f"{r_pred:.2f}" if r_pred is not None else "N/A"
                r_color = _rating_color(r_pred)
                r_year = f"({info['year']})" if info.get("year") else ""

                r_title = info["title"]
                if len(r_title) > 32:
                    r_title = r_title[:29] + "..."

                gcs = "".join(
                    f'<span class="genre-chip {_genre_chip_class(g)}" style="font-size:0.6rem;padding:0.1rem 0.4rem;margin:0.1rem 0.1rem;">{g[:5]}</span>'
                    for g in info.get("genres", [])[:3]
                )

                detail_parts = []
                director = info.get("director", "")
                if director and director.lower() not in ("unknown", "nan", ""):
                    detail_parts.append(f"🎬 {director}")
                actors = info.get("actors", [])[:1]
                if actors:
                    detail_parts.append(f"🎭 {actors[0]}")
                detail_str = "<br>".join(detail_parts)

                wl_badge = " 📋" if mid in st.session_state.watchlist else ""

                st.markdown(
                    f"""
                <div class="sim-card" style="cursor:pointer;">
                    <div class="sim-card-title" style="font-size:0.85rem;">{r_title}{wl_badge}</div>
                    <div class="sim-card-year">{r_year}</div>
                    <div class="sim-card-genres">{gcs}</div>
                    <div style="font-size:0.65rem;color:var(--text-muted);line-height:1.4;margin-bottom:0.3rem;">{detail_str}</div>
                    <div class="sim-card-rating" style="color:{r_color};font-size:1rem;">{r_pred_str}
                        <span style="font-size:0.6rem;font-weight:400;color:var(--text-muted-2);"> /5.0</span>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                if st.button("View", key=f"combo_btn_{mid}_{i}"):
                    st.session_state.selected_movie_id = mid
                    st.session_state.search_query = info["title"]
                    st.rerun()


# ── Movie Night Generator ─────────────────────────────────────────────────────
