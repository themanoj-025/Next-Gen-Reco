"""Data loading utilities."""

import json
from datetime import datetime

import streamlit as st

from app._paths import PROJECT_ROOT

# ── User data persistence ─────────────────────────────────────────────────────

USER_DATA_FILE = PROJECT_ROOT / ".movie_user_data.json"


def _load_user_data():
    """Load user data (ratings, watchlist, search history) from local JSON file."""
    if not USER_DATA_FILE.exists():
        return
    try:
        with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Only restore if we have fresh session state
        if "user_ratings" in st.session_state and not st.session_state.user_ratings:
            ratings = data.get("ratings", {})
            st.session_state.user_ratings = {int(k): v for k, v in ratings.items()}
        if "watchlist" in st.session_state and not st.session_state.watchlist:
            wl = data.get("watchlist", {})
            st.session_state.watchlist = {int(k): v for k, v in wl.items()}
        if "search_history" in st.session_state and not st.session_state.search_history:
            hist = data.get("search_history", [])
            st.session_state.search_history = [
                (q, datetime.fromisoformat(ts)) for q, ts in hist
            ]
    except Exception:
        pass  # Silently ignore corrupt data files


def _save_user_data():
    """Save user data (ratings, watchlist, search history) to local JSON file."""
    try:
        wl = st.session_state.get("watchlist", {})
        # Ensure watchlist values are strings (default category if old format)
        wl_clean = {}
        for k, v in wl.items():
            if isinstance(v, bool) or v is None or v == "":
                wl_clean[int(k)] = "Want to Watch"
            else:
                wl_clean[int(k)] = str(v)

        hist = st.session_state.get("search_history", [])
        data = {
            "ratings": {
                str(k): v for k, v in st.session_state.get("user_ratings", {}).items()
            },
            "watchlist": {str(k): v for k, v in wl_clean.items()},
            "search_history": [(q, ts.isoformat()) for q, ts in hist] if hist else [],
        }
        with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass
