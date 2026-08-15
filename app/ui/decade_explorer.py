import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.ui.poster_utils import _genre_chip_class, _rating_color


def render_decade_explorer():
    st.markdown(
        '<div class="section-title"><span class="icon">📅</span> Decade Explorer</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-subtitle">Travel through cinema history — explore the best movies from each decade</div>',
        unsafe_allow_html=True,
    )

    rec = st.session_state.recommender

    decades = [
        "1910s",
        "1920s",
        "1930s",
        "1940s",
        "1950s",
        "1960s",
        "1970s",
        "1980s",
        "1990s",
        "2000s",
        "2010s",
    ]
    decade_years = {
        "1910s": 1910,
        "1920s": 1920,
        "1930s": 1930,
        "1940s": 1940,
        "1950s": 1950,
        "1960s": 1960,
        "1970s": 1970,
        "1980s": 1980,
        "1990s": 1990,
        "2000s": 2000,
        "2010s": 2010,
    }

    selected_decade = st.select_slider(
        "Select a decade:",
        options=decades,
        value="1990s",
        key="decade_slider",
    )

    if not selected_decade:
        return

    dec_start = decade_years[selected_decade]

    with st.spinner(f"Loading movies from the {selected_decade}..."):
        decade_data = rec.get_movies_by_decade(dec_start, limit=24)

    if not decade_data or not decade_data["top_movies"]:
        st.info(f"No movies found from the {selected_decade}. Try a different decade!")
        return

    # ── Decade stats ──
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"""
        <div class="stat-card">
            <div class="value">{decade_data["count"]:,}</div>
            <div class="label">Movies in {selected_decade}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col2:
        avg_pred = sum(
            m.get("predicted_rating", 0) or 0 for m in decade_data["top_movies"][:10]
        ) / min(10, len(decade_data["top_movies"]))
        st.markdown(
            f"""
        <div class="stat-card">
            <div class="value" style="color:{_rating_color(avg_pred)};">{avg_pred:.2f}</div>
            <div class="label">Avg Top-10 Rating</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col3:
        genres_dist = decade_data.get("genre_distribution", {})
        top_genre = max(genres_dist, key=genres_dist.get) if genres_dist else "N/A"
        st.markdown(
            f"""
        <div class="stat-card">
            <div class="value" style="font-size:1.5rem;">{top_genre}</div>
            <div class="label">Most Popular Genre</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"""
        <div class="stat-card">
            <div class="value" style="font-size:1.5rem;">{len(decade_data.get("genre_distribution", {}))}</div>
            <div class="label">Unique Genres</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # ── Genre distribution chart ──
    genre_dist = decade_data.get("genre_distribution", {})
    if genre_dist:
        st.markdown(
            f'<div style="color:var(--text-muted);font-size:0.85rem;margin-bottom:0.5rem;">'
            f"Genre distribution in the {selected_decade}:</div>",
            unsafe_allow_html=True,
        )
        df_genre = pd.DataFrame(
            [{"Genre": g, "Count": c} for g, c in genre_dist.items()]
        ).sort_values("Count", ascending=True)

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                y=df_genre["Genre"],
                x=df_genre["Count"],
                orientation="h",
                marker=dict(
                    color=df_genre["Count"],
                    colorscale="Viridis",
                    line=dict(color="rgba(255,255,255,0.1)", width=1),
                ),
                text=df_genre["Count"],
                textposition="outside",
                textfont=dict(size=10, color="var(--text-secondary)"),
            )
        )
        fig.update_layout(
            height=max(250, len(df_genre) * 25 + 50),
            margin=dict(l=100, r=40, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="var(--text-secondary)", size=10),
            xaxis=dict(
                showgrid=True,
                gridcolor="rgba(255,255,255,0.05)",
                title="Number of Movies",
            ),
            yaxis=dict(title="", gridcolor="rgba(255,255,255,0.05)"),
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # ── Top movies grid ──
    st.markdown(
        f'<div style="color:var(--text-primary);font-size:1.1rem;font-weight:600;margin-bottom:0.5rem;">'
        f"🏆 Top Movies of the {selected_decade}</div>",
        unsafe_allow_html=True,
    )

    movies_list = decade_data["top_movies"]
    cols = st.columns(4)
    for i, info in enumerate(movies_list):
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

            # Director/actor if available
            detail = ""
            director = info.get("director", "")
            if director and director.lower() not in ("unknown", "nan", ""):
                detail = f'<div style="color:var(--text-muted-2);font-size:0.65rem;">🎬 {director[:25]}</div>'

            wl_badge = " 📋" if mid in st.session_state.watchlist else ""

            st.markdown(
                f"""
            <div class="sim-card" style="cursor:pointer;">
                <div style="display:flex;justify-content:space-between;">
                    <div style="font-size:0.7rem;color:var(--text-muted-3);font-weight:500;">#{i + 1}</div>
                    <div style="font-size:0.65rem;color:var(--text-muted-3);">{r_year}</div>
                </div>
                <div class="sim-card-title" style="font-size:0.85rem;">{r_title}{wl_badge}</div>
                {detail}
                <div class="sim-card-genres">{gcs}</div>
                <div class="sim-card-rating" style="color:{r_color};font-size:1rem;">{r_pred_str}
                    <span style="font-size:0.6rem;font-weight:400;color:var(--text-muted-2);"> /5.0</span>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            if st.button("View", key=f"dec_btn_{mid}_{i}"):
                st.session_state.selected_movie_id = mid
                st.session_state.search_query = info["title"]
                st.rerun()


# ── Combo Finder ──────────────────────────────────────────────────────────────
