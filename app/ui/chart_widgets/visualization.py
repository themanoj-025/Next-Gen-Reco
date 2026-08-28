"""Visualization charts for movie analysis."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def render_visualization_charts(movie_id: int, info: dict, recs: list) -> None:
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
                marker={"color": "#f7971e", "line": {"color": "#ffd200", "width": 1}},
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
                marker={
                    "color": "rgba(96,165,250,0.6)",
                    "line": {"color": "rgba(96,165,250,0.8)", "width": 1},
                },
                text=df_genres["In Similar Movies"],
                textposition="outside",
            )
        )
        fig.update_layout(
            barmode="group",
            height=350,
            margin={"l": 0, "r": 0, "t": 10, "b": 0},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "rgba(255,255,255,0.7)", "size": 11},
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "right",
                "x": 1,
                "font": {"color": "rgba(255,255,255,0.6)", "size": 10},
            },
            xaxis={"showgrid": True, "gridcolor": "rgba(255,255,255,0.05)", "title": "Count"},
            yaxis={"title": "", "gridcolor": "rgba(255,255,255,0.05)"},
            hoverlabel={"bgcolor": "rgba(30,30,60,0.95)", "font": {"color": "white", "size": 12}},
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
                    marker={
                        "color": colors_list,
                        "line": {"color": "rgba(255,255,255,0.1)", "width": 1},
                    },
                    text=all_data["Rating"].apply(lambda x: f"{x:.2f}"),
                    textposition="outside",
                    hovertemplate="%{x}<br>Rating: %{y:.2f}<extra></extra>",
                )
            )
            fig2.update_layout(
                height=350,
                margin={"l": 0, "r": 0, "t": 10, "b": 60},
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font={"color": "rgba(255,255,255,0.7)", "size": 10},
                xaxis={"showgrid": False, "tickangle": 45, "title": ""},
                yaxis={
                    "showgrid": True,
                    "gridcolor": "rgba(255,255,255,0.05)",
                    "title": "Predicted Rating",
                    "range": [0, 5.5],
                },
                hoverlabel={"bgcolor": "rgba(30,30,60,0.95)", "font": {"color": "white", "size": 12}},
            )
            st.plotly_chart(fig2, use_container_width=True)


# ── Similarity Breakdown ──────────────────────────────────────────────────────


