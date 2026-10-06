"""Home page."""

import streamlit as st

from app.ui.poster_utils import (
    _genre_chip_class,
    _poster_gradient,
    _poster_initials,
    _rating_color,
    _rating_stars,
)


def render_home() -> None:
    """IMDb-style home page with hero section and movie grids."""
    rec = st.session_state.recommender

    st.markdown('<div class="page-content">', unsafe_allow_html=True)

    # Hero section with top pick
    featured = rec.get_top_picks(n=1)
    if featured:
        f = featured[0]
        f_pred = f.get("predicted_rating")
        _rating_color(f_pred)
        _rating_stars(f_pred)
        f_overview = f.get("overview", "") or ""
        f_year = f"({f['year']})" if f.get("year") else ""
        f_director = f.get("director", "")
        f_genres = "".join(
            f'<span class="genre-chip {_genre_chip_class(g)}">{g}</span>'
            for g in f.get("genres", [])[:4]
        )

        st.markdown(
            f"""
        <div class="hero-section">
            <div class="hero-gradient"></div>
            <div class="hero-content">
                <div class="hero-badge">&#9733; Featured Movie</div>
                <h1 class="hero-title">{f["title"]}</h1>
                <div class="hero-meta">
                    <span>{f_year}</span>
                    <span class="rating">&#9733; {f_pred:.2f if f_pred else "N/A"} <span>/ 5.0</span></span>
                    {f"<span>&#127916; {f_director[:30]}</span>" if f_director and f_director.lower() not in ("unknown", "nan", "") else ""}
                </div>
                <div style="margin:0.3rem 0 0.5rem;">{f_genres}</div>
                {f'<div class="hero-overview">{f_overview[:200]}{"..." if len(f_overview) > 200 else ""}</div>' if f_overview else ""}
                <div class="hero-actions">
                    <button class="hero-btn hero-btn-primary">&#9654; View Details</button>
                    <button class="hero-btn hero-btn-secondary">+ Watchlist</button>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Search
    # Hero action buttons (functional)
    if featured:
        f = featured[0]
        hc1, hc2 = st.columns([1, 1])
        with hc1:
            if st.button(
                f"\u25b6 View {f['title'][:30]}",
                key="hero_view",
                use_container_width=True,
                type="primary",
            ):
                st.session_state.selected_movie_id = f["movieId"]
                st.session_state.search_query = f["title"]
                st.rerun()
        with hc2:
            wl_label = (
                "Remove from Watchlist"
                if f["movieId"] in st.session_state.watchlist
                else "+ Add to Watchlist"
            )
            if st.button(wl_label, key="hero_wl", use_container_width=True):
                if f["movieId"] in st.session_state.watchlist:
                    del st.session_state.watchlist[f["movieId"]]
                else:
                    st.session_state.watchlist[f["movieId"]] = "Want to Watch"
                st.rerun()

    search_val = st.text_input(
        "Search movies",
        placeholder="🔍 Search movies, actors, genres...",
        label_visibility="collapsed",
        key="home_search_input",
    )
    if search_val and len(search_val.strip()) >= 2:
        st.session_state.search_query = search_val.strip()
        st.session_state.active_tab = "Search"
        st.rerun()

    # Top Picks
    st.markdown(
        '<div class="section-header"><div class="accent-line"></div><h2>&#127942; Top Picks</h2></div>',
        unsafe_allow_html=True,
    )
    top_picks = rec.get_top_picks(n=12)
    if top_picks:
        cols = st.columns(4)
        for i, info in enumerate(top_picks):
            with cols[i % 4]:
                mid = info["movieId"]
                r_pred = info.get("predicted_rating")
                r_pred_str = f"{r_pred:.2f}" if r_pred is not None else "N/A"
                r_year = f"({info['year']})" if info.get("year") else ""
                r_title = info["title"][:27] + "..." if len(info["title"]) > 30 else info["title"]
                gcs = "".join(
                    f'<span class="imdb-card-genre-chip">{g[:6]}</span>' for g in info["genres"][:2]
                )
                wl_badge = " &#128203;" if mid in st.session_state.watchlist else ""

                st.markdown(
                    f"""
                <div class="imdb-card">
                    <div class="imdb-card-poster" style="background:{_poster_gradient(mid)};">
                        {_poster_initials(info["title"])}
                    </div>
                    <div class="imdb-card-body">
                        <div class="imdb-card-title">{r_title}{wl_badge}</div>
                        <div class="imdb-card-meta">
                            <span class="imdb-card-rating">&#9733; {r_pred_str}</span>
                            <span class="imdb-card-year">{r_year}</span>
                        </div>
                        <div class="imdb-card-genres">{gcs}</div>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
                if st.button("View", key=f"home_top_{mid}_{i}"):
                    st.session_state.selected_movie_id = mid
                    st.session_state.search_query = info["title"]
                    st.rerun()

    # Browse by Genre
    st.markdown(
        '<div class="section-header"><div class="accent-line"></div><h2>&#127917; Browse by Genre</h2></div>',
        unsafe_allow_html=True,
    )
    all_genres = sorted(rec.genre_cols)
    pop_genres = [
        "Action",
        "Comedy",
        "Drama",
        "Sci-Fi",
        "Horror",
        "Romance",
        "Thriller",
        "Adventure",
    ]
    gcols = st.columns(4)
    for i, g in enumerate(pop_genres):
        if g in all_genres:
            with gcols[i % 4]:
                if st.button(f"&#127916; {g}", key=f"home_genre_{g}", use_container_width=True):
                    st.session_state.mood_genres = [g]
                    st.session_state.active_tab = "Genre"
                    st.rerun()

    # Feeling Lucky
    st.markdown(
        '<div class="section-header"><div class="accent-line"></div><h2>&#127922; Feeling Lucky?</h2></div>',
        unsafe_allow_html=True,
    )
    ca, cb = st.columns(2)
    with ca:
        if st.button("&#127922; Surprise Me!", use_container_width=True, type="primary"):
            rm = rec.movies.sample(1).iloc[0]
            st.session_state.selected_movie_id = rm["movieId"]
            st.session_state.search_query = rm["title"]
            st.rerun()
    with cb:
        if st.button("&#128197; Explore Decades", use_container_width=True):
            st.session_state.active_tab = "Decades"
            st.rerun()

    # Stats
    st.markdown(
        '<div class="section-header"><div class="accent-line"></div><h2>&#128202; Database Stats</h2></div>',
        unsafe_allow_html=True,
    )
    n_movies = len(rec.movies)
    n_genres = len(rec.genre_cols)
    n_rated = len(st.session_state.user_ratings)
    n_wl = len(st.session_state.watchlist)
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown(
            f'<div class="stat-card"><div class="value">{n_movies:,}</div><div class="label">Movies</div></div>',
            unsafe_allow_html=True,
        )
    with s2:
        st.markdown(
            f'<div class="stat-card"><div class="value">{n_genres}</div><div class="label">Genres</div></div>',
            unsafe_allow_html=True,
        )
    with s3:
        st.markdown(
            f'<div class="stat-card"><div class="value">{n_rated}</div><div class="label">Your Ratings</div></div>',
            unsafe_allow_html=True,
        )
    with s4:
        st.markdown(
            f'<div class="stat-card"><div class="value">{n_wl}</div><div class="label">Watchlist</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)
