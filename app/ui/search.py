"""Search and search history page."""

from datetime import datetime

import streamlit as st

from app.data.loader import _save_user_data
from app.ui.poster_utils import _genre_chip_class, _rating_color


def render_search():
    rec = st.session_state.recommender

    st.markdown('<div style="max-width:700px;margin:0 auto;">', unsafe_allow_html=True)

    search_query = st.text_input(
        label="",
        placeholder="🔍 Search for any movie... (e.g. Toy Story, The Matrix, Inception)",
        label_visibility="collapsed",
        key="search_input",
        value=st.session_state.get("search_query", ""),
    )

    if search_query and len(search_query.strip()) >= 2:
        q = search_query.strip()

        # Track search history
        if q != st.session_state.search_query:
            st.session_state.search_history.insert(0, (q, datetime.now()))
            if len(st.session_state.search_history) > 20:
                st.session_state.search_history = st.session_state.search_history[:20]
            _save_user_data()

        # ── Advanced search filters ──────────────────────────────────────
        all_genres = sorted(rec.genre_cols)

        with st.expander("🔎 Search Filters", expanded=False):
            filt_col1, filt_col2, filt_col3 = st.columns(3)
            with filt_col1:
                selected_genre = st.selectbox(
                    "Genre",
                    ["All Genres"] + all_genres,
                    index=(["All Genres"] + all_genres).index(
                        st.session_state.search_genre_filter
                    )
                    if st.session_state.search_genre_filter
                    in ["All Genres"] + all_genres
                    else 0,
                    key="sf_genre",
                )
                st.session_state.search_genre_filter = selected_genre
            with filt_col2:
                year_range = st.slider(
                    "Year Range",
                    1900,
                    2026,
                    (
                        st.session_state.search_year_min,
                        st.session_state.search_year_max,
                    ),
                    key="sf_year",
                )
                st.session_state.search_year_min, st.session_state.search_year_max = (
                    year_range
                )
            with filt_col3:
                rating_min = st.slider(
                    "Min Predicted Rating",
                    1.0,
                    5.0,
                    st.session_state.search_rating_min,
                    0.5,
                    key="sf_rating",
                )
                st.session_state.search_rating_min = rating_min

        genre_param = selected_genre if selected_genre != "All Genres" else None
        year_min_param = (
            st.session_state.search_year_min
            if st.session_state.search_year_min > 1900
            else None
        )
        year_max_param = (
            st.session_state.search_year_max
            if st.session_state.search_year_max < 2026
            else None
        )
        rating_min_param = (
            st.session_state.search_rating_min
            if st.session_state.search_rating_min > 1.0
            else None
        )

        results = rec.search_movies_advanced(
            q,
            limit=10,
            genre_filter=genre_param,
            year_min=year_min_param,
            year_max=year_max_param,
            rating_min=rating_min_param,
        )
        if results:
            st.markdown(
                f'<div style="color:var(--text-muted);font-size:0.8rem;margin-bottom:0.5rem;">'
                f"Found {len(results)} movies. Click to explore:</div>",
                unsafe_allow_html=True,
            )
            for i, r in enumerate(results):
                with st.container():
                    r_pred = r["predicted_rating"]
                    r_pred_str = f"{r_pred:.2f}" if r_pred is not None else "N/A"
                    r_color = _rating_color(r_pred)
                    r_year = f"({r['year']})" if r.get("year") else ""

                    # Genre chips
                    gcs = "".join(
                        f'<span class="genre-chip {_genre_chip_class(g)}" style="font-size:0.65rem;padding:0.15rem 0.5rem;margin:0.1rem 0.15rem;">{g}</span>'
                        for g in r["genres"][:3]
                    )

                    # Show if in watchlist
                    wl_badge = (
                        " 📋" if r["movieId"] in st.session_state.watchlist else ""
                    )
                    wl_cat = ""
                    if r["movieId"] in st.session_state.watchlist:
                        wl_cat = f' <span style=" color:var(--text-muted-2);font-size:0.7rem;">({st.session_state.watchlist[r["movieId"]]})</span>'
                    # Show user rating if any
                    ur_badge = ""
                    if r["movieId"] in st.session_state.user_ratings:
                        ur = st.session_state.user_ratings[r["movieId"]]
                        ur_badge = f" ⭐{ur}"

                    # Calculate match info
                    search_score = r.get("_search_score", 0)
                    match_type = ""
                    if search_score >= 80:
                        match_type = "🎯 Perfect"
                    elif search_score >= 50:
                        match_type = "✨ Great"
                    elif search_score >= 20:
                        match_type = "📌 Good"
                    elif search_score > 0:
                        match_type = "🔗 Partial"

                    st.markdown(
                        f"""
                    <div class="sim-card" style="cursor:pointer;margin:0.5rem 0;padding:0.8rem 1.2rem;">
                        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                            <div style="flex:1;">
                                <div class="sim-card-title" style="font-size:1.05rem;">{r["title"]}{wl_badge}{ur_badge}</div>
                                <div class="sim-card-year">{r_year}</div>
                                <div class="sim-card-genres" style="margin-top:0.3rem;">{gcs}</div>
                            </div>
                            <div style="text-align:right;min-width:100px;">
                                <div style="font-size:1.3rem;font-weight:700;color:{r_color};">{r_pred_str}
                                    <span style="font-size:0.65rem;font-weight:400;color:var(--text-muted-2);"> /5</span>
                                </div>
                                {f'<div style="font-size:0.7rem;color:var(--text-muted);">{match_type}</div>' if match_type else ""}
                                {wl_cat}
                            </div>
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    if st.button(
                        f"🔍 View {r['title'][:30]}...",
                        key=f"search_result_{r['movieId']}_{i}",
                        use_container_width=True,
                    ):
                        st.session_state.selected_movie_id = r["movieId"]
                        st.session_state.search_query = r["title"]
                        st.rerun()
        else:
            st.markdown(
                '<div style="color:var(--text-muted-2);text-align:center;padding:1rem;font-size:0.95rem;">'
                "😕 No movies found matching your search.</div>",
                unsafe_allow_html=True,
            )

            # ── "Did you mean?" suggestions ────────────────────────────
            suggestions = rec.search_suggestions(q)
            if suggestions:
                st.markdown(
                    '<div style="color:var(--text-muted);font-size:0.85rem;margin-top:0.5rem;">'
                    "💡 Did you mean:</div>",
                    unsafe_allow_html=True,
                )
                for s in suggestions:
                    if st.button(
                        f"🔎 {s}", key=f"suggest_{hash(s)}", use_container_width=False
                    ):
                        st.session_state.search_query = s
                        st.rerun()

            # If no filters applied, show a helpful message
            if not genre_param and not year_min_param and not rating_min_param:
                st.markdown(
                    '<div style="color:var(--text-muted-2);text-align:center;padding:0.5rem;font-size:0.8rem;">'
                    "Try checking your spelling or use fewer words. You can also browse by genre or use the Surprise Me tab!</div>",
                    unsafe_allow_html=True,
                )

    st.markdown("</div>", unsafe_allow_html=True)


# ── Search History Sidebar ────────────────────────────────────────────────────


def render_search_history():
    if not st.session_state.search_history:
        return

    st.markdown("### 🔍 Recent Searches")
    shown = set()
    for query, ts in st.session_state.search_history:
        if query not in shown and len(shown) < 5:
            shown.add(query)
            if st.button(
                f"🔎 {query}", key=f"hist_{hash(query)}", use_container_width=True
            ):
                st.session_state.search_query = query
                st.rerun()


# ── User Rating Widget ────────────────────────────────────────────────────────
