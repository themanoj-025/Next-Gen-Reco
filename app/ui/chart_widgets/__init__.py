"""Chart widgets -- re-exports for backward compatibility."""

from app.ui.chart_widgets.similarity import render_similarity_breakdown
from app.ui.chart_widgets.visualization import render_visualization_charts

__all__ = [
    "render_similarity_breakdown",
    "render_visualization_charts",
]
