"""Session state initialization and utilities."""

import traceback

import streamlit as st

from app.data.loader import _load_user_data
from app.recommender import MovieRecommender
from app.ui.poster_utils import TMDB_API_KEY


def _check_data_files() -> list[str]:
    """Check that all required data and model files exist.
    Returns a list of missing file descriptions, empty if all OK.
    Uses PROJECT_ROOT-based paths so it works on Streamlit Cloud.
    """
    from app._paths import PROJECT_ROOT

    missing = []
    required = {
        "data/movies.csv": "Movie database",
        "data/tags.csv": "Movie tags",
        "data/links.csv": "Movie links (TMDB IDs)",
        "models/v1_test/model.joblib": "ML model",
        "models/v1_test/meta.joblib": "Model metadata",
    }
    for rel_path, desc in required.items():
        if not (PROJECT_ROOT / rel_path).exists():
            missing.append(f"{desc} ({rel_path})")
    return missing


@st.cache_resource
def _load_recommender() -> MovieRecommender:
    """Load recommender once and cache across all sessions.

    Using @st.cache_resource ensures the heavy model + data loading
    happens only once per server process, not per session.  This
    prevents the repeated OOM / timeout crashes on Streamlit Cloud.
    """
    return MovieRecommender()


def init_session():
    if "recommender" not in st.session_state:
        # Pre-flight checks before attempting model load
        missing_files = _check_data_files()
        if missing_files:
            st.error("Missing required files for deployment")
            st.markdown(
                f"""
                ### 🚨 Deployment Error

                The following files are required but were not found:

                {"<br>".join(f"❌ **{m}**" for m in missing_files)}

                **Possible causes:**
                - Files were not pushed to git (check `.gitignore`)
                - Repository cloned/copied incorrectly
                - Model needs to be re-trained and saved

                **For Streamlit Cloud:** Check the app logs (⋮ → Settings → Logs)
                """,
                unsafe_allow_html=True,
            )
            st.stop()

        with st.spinner("Loading movie database and AI model..."):
            try:
                st.session_state.recommender = _load_recommender()
                st.session_state["_recommender_loaded"] = True
            except MemoryError:
                st.error("Out of memory loading the movie database")
                st.markdown(
                    """
                    ### 🚨 Out of Memory

                    The app ran out of memory while loading.

                    **Solutions:**
                    - Streamlit Cloud **Free Tier** has 1 GB RAM — the app needs ~512 MB
                    - If this error persists on the **paid tier**, check for memory leaks
                    - Try restarting the app from the Streamlit Cloud dashboard
                    """
                )
                st.stop()
            except FileNotFoundError as e:
                st.error(f"Missing data file: {e}")
                st.markdown(
                    """
                    ### 🚨 File Not Found

                    A required data file is missing from the deployment.

                    **Check that the file is tracked in git:**
                    ```
                    git ls-files data/ models/
                    ```

                    If it's not listed, add it with:
                    ```
                    git add <path>
                    git commit -m "add missing file"
                    git push
                    ```
                    """
                )
                st.stop()
            except (OSError, ValueError, KeyError) as e:
                st.error(f"Failed to initialize: {e}")
                st.markdown(
                    f"""
                    ### 🚨 Application Error

                    The app could not initialize. This is often due to:
                    - **Missing data files** — `movies.csv`, `tags.csv`, and `links.csv` must be in the app directory
                    - **Missing model files** — `models/v1_test/` must contain `model.joblib` and `meta.joblib`
                    - **Out of memory** — The app needs ~512 MB of available RAM
                    - **Dependency conflicts** — Check the requirements.txt

                    ```\n{traceback.format_exc()}```

                    Check the **Streamlit Cloud logs** (⋮ menu → Settings → Logs) for the full error traceback.
                    """
                )
                st.stop()

    # Core state
    if "selected_movie_id" not in st.session_state:
        st.session_state.selected_movie_id = None
    if "search_query" not in st.session_state:
        st.session_state.search_query = ""
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "Home"

    # User personalization
    if "user_ratings" not in st.session_state:
        st.session_state.user_ratings = {}  # movieId -> rating (1-5)
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = {}  # movieId -> category (e.g. "Want to Watch")
    if "search_history" not in st.session_state:
        st.session_state.search_history = []  # list of (query, timestamp)
    if "comparison_ids" not in st.session_state:
        st.session_state.comparison_ids = []
    if "mood_genres" not in st.session_state:
        st.session_state.mood_genres = []
    if "last_action" not in st.session_state:
        st.session_state.last_action = None
    if "search_genre_filter" not in st.session_state:
        st.session_state.search_genre_filter = "All Genres"
    if "search_year_min" not in st.session_state:
        st.session_state.search_year_min = 1900
    if "search_year_max" not in st.session_state:
        st.session_state.search_year_max = 2026
    if "search_rating_min" not in st.session_state:
        st.session_state.search_rating_min = 1.0

    # Theme preference
    if "theme" not in st.session_state:
        st.session_state.theme = "dark"

    # Load user data from disk
    _load_user_data()

    # TMDB poster integration
    if "tmdb_poster_cache" not in st.session_state:
        st.session_state.tmdb_poster_cache = {}
    if "use_tmdb_posters" not in st.session_state:
        st.session_state.use_tmdb_posters = bool(TMDB_API_KEY)
    if "tmdb_api_key" not in st.session_state:
        st.session_state.tmdb_api_key = TMDB_API_KEY


# ── Toast notification ────────────────────────────────────────────────────────


# ── Render functions ──────────────────────────────────────────────────────────
