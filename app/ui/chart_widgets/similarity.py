"""Similarity breakdown chart."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st


def render_similarity_breakdown(movie_id: int, recs: list) -> None:
    if not recs:
        return

    st.markdown(
        """
    <div class="dash-section-header">
        <span class="h-icon">📐</span>
        <span class="h-title">Similarity Breakdown</span>
        <span class="h-subtitle">How each recommendation scored across similarity dimensions</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

    data = []
    for r in recs[:8]:
        display = r["title"][:35] + "…" if len(r["title"]) > 35 else r["title"]
        data.append(
            {
                "Movie": display,
                "Genre Match": r["genre_similarity"],
                "Tag Match": r["tag_similarity"],
                "Year Proximity": r["year_proximity"],
            }
        )

    df_sim = pd.DataFrame(data)
    fig = go.Figure()
    for col, color in [
        ("Genre Match", "#f7971e"),
        ("Tag Match", "#60a5fa"),
        ("Year Proximity", "#34d399"),
    ]:
        fig.add_trace(
            go.Bar(
                name=col,
                x=df_sim["Movie"],
                y=df_sim[col],
                marker={"color": color, "opacity": 0.85},
                text=df_sim[col].apply(lambda x: f"{x:.0%}"),
                textposition="inside",
                textfont={"size": 9, "color": "white"},
            )
        )

    fig.update_layout(
        barmode="group",
        height=300,
        margin={"l": 0, "r": 0, "t": 10, "b": 60},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "rgba(255,255,255,0.7)", "size": 10},
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
            "font": {"color": "rgba(255,255,255,0.6)", "size": 10},
        },
        xaxis={"showgrid": False, "tickangle": 45, "title": ""},
        yaxis={
            "showgrid": True,
            "gridcolor": "rgba(255,255,255,0.05)",
            "title": "Similarity Score",
            "tickformat": ".0%",
            "range": [0, 1.1],
        },
        hoverlabel={"bgcolor": "rgba(30,30,60,0.95)", "font": {"color": "white", "size": 12}},
    )
    st.plotly_chart(fig, use_container_width=True)


# ── Export ────────────────────────────────────────────────────────────────────


