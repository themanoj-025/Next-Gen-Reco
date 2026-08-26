import streamlit as st

from app.ui.poster_utils import _genre_chip_class, _rating_color


def render_movie_night() -> None:
    st.markdown(
        '<div class="section-title"><span class="icon">🎬</span> Movie Night Generator</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-subtitle">Plan a movie marathon — pick your criteria and get a curated lineup</div>',
        unsafe_allow_html=True,
    )

    rec = st.session_state.recommender
    all_genres = sorted(rec.genre_cols)

    with st.container():
        col1, col2, col3 = st.columns(3)

        with col1:
            genre = st.selectbox(
                "🎭 Genre Focus",
                ["Any Genre"] + all_genres,
                index=0,
                key="night_genre",
            )

        with col2:
            movie_count = st.select_slider(
                "📽️ Number of Movies",
                options=[1, 2, 3, 4, 5],
                value=3,
                key="night_count",
            )

        with col3:
            max_runtime = st.select_slider(
                "⏱️ Total Runtime Budget",
                options=[90, 120, 150, 180, 210, 240, 300, 360],
                value=240,
                key="night_runtime",
            )

        col_a, col_b = st.columns(2)
        with col_a:
            year_range = st.slider(
                "📅 Year Range",
                1900,
                2026,
                (1990, 2024),
                key="night_year",
            )
        with col_b:
            prefer_action = st.checkbox(
                "🔥 Prefer high-energy movies",
                value=False,
                key="night_action",
                help="If checked, favors action/adventure/thriller movies",
            )

        generate_clicked = st.button(
            "🎬 Generate Movie Night!", use_container_width=True, type="primary"
        )

    if generate_clicked:
        genre_param = genre if genre != "Any Genre" else None
        if prefer_action:
            genre_param = "Action|Adventure|Thriller|Sci-Fi"

        with st.spinner("🎬 Curating the perfect movie lineup..."):
            lineup = rec.movie_night_generator(
                genre=genre_param,
                max_runtime_minutes=int(max_runtime),
                movie_count=int(movie_count),
                min_year=year_range[0],
                max_year=year_range[1],
                prefer_action=prefer_action,
            )

        if not lineup:
            st.markdown(
                '<div class="empty-state"><div class="icon">🎬</div>'
                '<div class="text">Couldn\'t assemble a lineup with those criteria. Try increasing the runtime budget or broadening your filters!</div></div>',
                unsafe_allow_html=True,
            )
            return

        # Calculate total runtime
        total_runtime = 0
        runtime_parts = []
        for info in lineup:
            meta = rec.get_enriched_metadata(info["movieId"])
            if meta and meta.get("runtime"):
                total_runtime += meta["runtime"]
                h = meta["runtime"] // 60
                m = meta["runtime"] % 60
                rt_str = f"{h}h {m}m" if h > 0 else f"{m}m"
            else:
                rt_str = "~2h"
                total_runtime += 120
            runtime_parts.append(rt_str)

        st.markdown(
            f'<div style="background:linear-gradient(135deg,rgba(247,151,30,0.1),rgba(255,210,0,0.05));border:1px solid rgba(247,151,30,0.3);border-radius:16px;padding:1.2rem 1.5rem;margin-bottom:1.5rem;text-align:center;">'
            f'<div style="font-size:1.5rem;font-weight:700;color:var(--star-color);">🎬 Your Movie Night Lineup</div>'
            f'<div style="color:var(--text-secondary);font-size:0.9rem;margin-top:0.3rem;">'
            f"{len(lineup)} movie{'s' if len(lineup) != 1 else ''}  ·  "
            f"⏱️ {total_runtime // 60}h {total_runtime % 60}m total  ·  "
            f"Runtime: {' + '.join(runtime_parts)}"
            f"</div></div>",
            unsafe_allow_html=True,
        )

        for i, info in enumerate(lineup):
            mid = info["movieId"]
            r_pred = info.get("predicted_rating")
            r_pred_str = f"{r_pred:.2f}" if r_pred is not None else "N/A"
            r_color = _rating_color(r_pred)
            r_year = f"({info['year']})" if info.get("year") else ""

            # Get runtime
            meta = rec.get_enriched_metadata(mid)
            runtime_str = ""
            if meta and meta.get("runtime"):
                h = meta["runtime"] // 60
                m = meta["runtime"] % 60
                runtime_str = f"{h}h {m}m" if h > 0 else f"{m}m"

            tagline = info.get("tagline", "")
            overview = info.get("overview", "")
            director = info.get("director", "")
            actors = info.get("actors", [])

            gcs = "".join(
                f'<span class="genre-chip {_genre_chip_class(g)}" style="font-size:0.65rem;padding:0.15rem 0.5rem;margin:0.1rem 0.15rem;">{g}</span>'
                for g in info.get("genres", [])[:4]
            )

            # Precompute conditional HTML outside the triple-quoted f-string so
            # the expressions never nest double quotes inside it (Python 3.10
            # tokenizer rejects that; only 3.12+ PEP 701 allows it).
            tagline_html = (
                f'<div style="font-style:italic;font-size:0.85rem;color:var(--text-secondary);">“{tagline}”</div>'
                if tagline
                else ""
            )
            overview_html = (
                f'<div style="color:var(--text-muted);font-size:0.8rem;margin-top:0.2rem;">{overview[:250]}{"..." if len(overview) > 250 else ""}</div>'
                if overview
                else ""
            )
            runtime_html = f"<span>⏱ {runtime_str}</span>" if runtime_str else ""
            director_html = (
                f"<span>🎬 {director}</span>"
                if director and director.lower() not in ("unknown", "nan", "")
                else ""
            )
            actors_html = f"<span>🎭 {actors[0] if actors else ''}</span>" if actors else ""

            with st.container():
                st.markdown(
                    f"""
                <div class="movie-card" style="padding:1.2rem 1.5rem;">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                        <div style="flex:1;">
                            <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.2rem;">
                                <span style="background:linear-gradient(135deg,#f7971e,#ffd200);color:#1a1a2e;font-weight:700;font-size:0.75rem;padding:0.15rem 0.6rem;border-radius:999px;">Movie {i + 1}</span>
                                <div class="movie-title" style="font-size:1.2rem;">{info["title"]}</div>
                                <span class="movie-year">{r_year}</span>
                            </div>
                            <div style="margin:0.3rem 0;">{gcs}</div>
                            {tagline_html}
                            {overview_html}
                            <div style="display:flex;gap:1rem;margin-top:0.3rem;font-size:0.8rem;color:var(--text-muted);">
                                {runtime_html}
                                {director_html}
                                {actors_html}
                            </div>
                        </div>
                        <div style="text-align:center;min-width:80px;">
                            <div style="font-size:2rem;font-weight:800;color:{r_color};">{r_pred_str}</div>
                            <div style="font-size:0.65rem;color:var(--text-muted-2);">PREDICTED</div>
                        </div>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                if st.button(
                    f"🎬 Explore '{info['title'][:30]}'",
                    key=f"night_btn_{mid}_{i}",
                    use_container_width=True,
                ):
                    st.session_state.selected_movie_id = mid
                    st.session_state.search_query = info["title"]
                    st.rerun()


# ── Enhanced Movie Detail Stats ───────────────────────────────────────────────
