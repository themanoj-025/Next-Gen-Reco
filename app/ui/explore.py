"""Surprise Me and Mood Explorer."""

import pandas as pd
import streamlit as st

from app.ui.poster_utils import _genre_chip_class, _rating_color


def render_surprise_me():
    st.markdown(
        '<div class="section-title"><span class="icon">🎲</span> Surprise Me</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-subtitle">Discover a random movie from the database</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🎲 Pick a Random Movie!", use_container_width=True):
            rec = st.session_state.recommender
            random_movie = rec.movies.sample(1).iloc[0]
            st.session_state.selected_movie_id = random_movie["movieId"]
            st.session_state.search_query = random_movie["title"]
            st.rerun()

    with col2:
        # Show some popular genre quick-picks
        genres_surprise = ["Action", "Comedy", "Drama", "Sci-Fi", "Horror", "Romance"]
        st.markdown(
            '<div style="color:var(--text-muted);font-size:0.85rem;padding-top:0.3rem;">'
            "Or pick a random movie from:</div>",
            unsafe_allow_html=True,
        )
        genre_cols = st.columns(6)
        for i, g in enumerate(genres_surprise):
            with genre_cols[i]:
                if st.button(g, key=f"surprise_genre_{g}", use_container_width=True):
                    rec = st.session_state.recommender
                    mask = rec.movies["genres"].str.contains(g, na=False)
                    candidates = rec.movies[mask]
                    if len(candidates) > 0:
                        random_movie = candidates.sample(1).iloc[0]
                        st.session_state.selected_movie_id = random_movie["movieId"]
                        st.session_state.search_query = random_movie["title"]
                        st.rerun()


# ── Genre Explorer ────────────────────────────────────────────────────────────────


def render_mood_explorer():
    st.markdown(
        '<div class="section-title"><span class="icon">🎨</span> Genre Explorer</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-subtitle">Select genres you\'re in the mood for and discover movies</div>',
        unsafe_allow_html=True,
    )

    rec = st.session_state.recommender
    all_genres = sorted(rec.genre_cols)

    st.markdown("#### Select genres (up to 3):")
    cols = st.columns(5)
    selected = st.session_state.mood_genres.copy()

    for i, genre in enumerate(all_genres):
        with cols[i % 5]:
            is_active = genre in selected
            btn_type = "primary" if is_active else "secondary"
            label = f"✅ {genre}" if is_active else genre
            if st.button(label, key=f"mood_{genre}", use_container_width=True, type=btn_type):
                if is_active:
                    selected.remove(genre)
                else:
                    if len(selected) < 3:
                        selected.append(genre)
                st.session_state.mood_genres = selected
                st.rerun()

    if selected:
        st.markdown(
            f'<div style="color:var(--text-secondary);font-size:0.9rem;margin:0.5rem 0;">'
            f"Mood: {' + '.join(selected)}</div>",
            unsafe_allow_html=True,
        )

        # Find movies matching all selected genres
        with st.spinner("Finding movies for your mood..."):
            mask = pd.Series([True] * len(rec.movies))
            for g in selected:
                mask &= rec.movies["genres"].str.contains(g, na=False)
            candidates = rec.movies[mask]

            if len(candidates) > 0:
                sample = candidates.sample(min(12, len(candidates)))
                st.markdown(
                    f'<div style="color:var(--text-muted-2);font-size:0.8rem;margin-bottom:1rem;">'
                    f"Found {len(candidates):,} movies matching your mood. Showing {len(sample)} random picks:</div>",
                    unsafe_allow_html=True,
                )

                cols = st.columns(4)
                for i, (_, row) in enumerate(sample.iterrows()):
                    with cols[i % 4]:
                        mid = row["movieId"]
                        info = rec.get_movie_info(mid)
                        if info:
                            r_pred = info["predicted_rating"]
                            r_pred_str = f"{r_pred:.2f}" if r_pred is not None else "N/A"
                            r_color = _rating_color(r_pred)
                            r_year = f"({info['year']})" if info.get("year") else ""

                            r_title = info["title"]
                            if len(r_title) > 35:
                                r_title = r_title[:32] + "..."

                            gcs = "".join(
                                f'<span class="genre-chip {_genre_chip_class(g)}" style="font-size:0.6rem;padding:0.1rem 0.4rem;margin:0.1rem 0.1rem;">{g[:5]}</span>'
                                for g in info["genres"][:3]
                            )

                            st.markdown(
                                f"""
                            <div class="sim-card" style="cursor:pointer;">
                                <div class="sim-card-title">{r_title}</div>
                                <div class="sim-card-year">{r_year}</div>
                                <div class="sim-card-genres">{gcs}</div>
                                <div class="sim-card-rating" style="color:{r_color};">{r_pred_str}
                                    <span style="font-size:0.7rem;font-weight:400;color:var(--text-muted-2);"> /5.0</span>
                                </div>
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )

                            if st.button("Explore", key=f"mood_btn_{mid}_{i}"):
                                st.session_state.selected_movie_id = mid
                                st.session_state.search_query = info["title"]
                                st.rerun()
            else:
                st.info("No movies found matching all selected genres. Try fewer genres.")

    # Reset button
    if selected and st.button("🔄 Clear Mood Selection", use_container_width=False):
        st.session_state.mood_genres = []
        st.rerun()
