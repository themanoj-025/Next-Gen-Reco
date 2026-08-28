"""Shared UI components -- re-exports for backward compatibility."""

from __future__ import annotations

from app.ui.chart_widgets import (
    render_similarity_breakdown,
    render_visualization_charts,
)
from app.ui.detail_widgets import (
    render_export,
    render_feature_explanation,
    render_metrics_card,
    render_movie_detail,
    render_rating_widget,
    render_similar_movies,
    render_watchlist_button,
)

__all__ = [
    "render_export",
    "render_feature_explanation",
    "render_metrics_card",
    "render_movie_detail",
    "render_rating_widget",
    "render_similarity_breakdown",
    "render_similar_movies",
    "render_visualization_charts",
    "render_watchlist_button",
]
