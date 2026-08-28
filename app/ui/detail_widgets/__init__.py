"""Detail widgets -- re-exports for backward compatibility."""

from app.ui.detail_widgets.info_widgets import (
    render_export,
    render_feature_explanation,
    render_metrics_card,
    render_similar_movies,
)
from app.ui.detail_widgets.movie_detail import render_movie_detail
from app.ui.detail_widgets.rating_widgets import (
    render_rating_widget,
    render_watchlist_button,
)

__all__ = [
    "render_export",
    "render_feature_explanation",
    "render_metrics_card",
    "render_movie_detail",
    "render_rating_widget",
    "render_similar_movies",
    "render_watchlist_button",
]
