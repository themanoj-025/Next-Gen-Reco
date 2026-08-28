"""Rating and watchlist widgets for movie detail pages."""

from __future__ import annotations

import streamlit as st

from app.data.loader import _save_user_data
from app.ui.poster_utils import _rating_color


def _stars_display(rating: float | None) -> str:
    if rating is None:
        return ""
    full = int(rating)
    half = 1 if rating - full >= 0.25 and rating - full < 0.75 else 0
    empty = 5 - full - half
    return "★" * full + ("½" if half else "") + "☆" * empty


# ── Rating Widget ─────────────────────────────────────────────────────────────


def render_rating_widget(movie_id: int) -> None:
    """Show interactive star rating for a movie with modern styling."""
    current = st.session_state.user_ratings.get(movie_id)

    st.markdown(
        """
    <div class="detail-side-widget">
        <div class="w-label">⭐ Your Rating</div>
    """,
        unsafe_allow_html=True,
    )

    cols = st.columns(5)
    rating_changed = False
    for i in range(5):
        val = i + 1
        is_filled = current is not None and val <= current
        star = "★" if is_filled else "☆"
        with cols[i]:
            if st.button(
                star,
                key=f"rate_{movie_id}_{val}",
                use_container_width=True,
                help=f"Rate {val}/5",
            ):
                if current == val:
                    del st.session_state.user_ratings[movie_id]
                else:
                    st.session_state.user_ratings[movie_id] = val
                rating_changed = True
                _save_user_data()

    if current:
        r_color = _rating_color(current)
        st.markdown(
            f'<div style="color:var(--text-muted);font-size:0.8rem;">'
            f'<span style="color:{r_color};">{"★" * current}{"☆" * (5 - current)}</span> ({current}/5)</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="color:var(--text-muted-2);font-size:0.75rem;">Click a star to rate</div>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    if rating_changed:
        st.rerun()


# ── Watchlist button ──────────────────────────────────────────────────────────

WATCHLIST_CATEGORIES = ["Want to Watch", "Watching", "Watched"]


def render_watchlist_button(movie_id: int) -> None:
    in_wl = movie_id in st.session_state.watchlist

    if not in_wl:
        if st.button("📋 Add to Watchlist", key=f"wl_add_{movie_id}", use_container_width=True):
            st.session_state.watchlist[movie_id] = "Want to Watch"
            _save_user_data()
            st.rerun()
    else:
        current_cat = st.session_state.watchlist[movie_id]
        st.markdown(
            f'<div style="margin-bottom:0.3rem;color:var(--text-muted);font-size:0.8rem;">'
            f'📋 In Watchlist: <strong style="color:#fbbf24;">{current_cat}</strong></div>',
            unsafe_allow_html=True,
        )

        new_cat = st.selectbox(
            "Status",
            WATCHLIST_CATEGORIES,
            index=(
                WATCHLIST_CATEGORIES.index(current_cat)
                if current_cat in WATCHLIST_CATEGORIES
                else 0
            ),
            key=f"wl_cat_{movie_id}",
            label_visibility="collapsed",
        )
        if new_cat != current_cat:
            st.session_state.watchlist[movie_id] = new_cat
            _save_user_data()
            st.rerun()

        if st.button(
            "🗑️ Remove",
            key=f"wl_rem_{movie_id}",
            use_container_width=True,
            type="secondary",
        ):
            del st.session_state.watchlist[movie_id]
            _save_user_data()
            st.rerun()


# ── Movie Detail ──────────────────────────────────────────────────────────────


