"""
ND Folder Data Enrichment Module
=================================
Integrates data from the ND/ folder into the existing MovieLens system:

  - ND/movies.csv (TMDB dataset) — overviews, budget, revenue, runtime,
    popularity, vote_average, tagline, director, cast, keywords
  - ND/main_data.csv             — director_name + top 3 actors per movie
  - ND/reviews.txt               — user text reviews

All data is cross-referenced to the main MovieLens dataset by matching
normalized movie titles.
"""

import pickle
import re
import warnings
from typing import Any

import pandas as pd

warnings.filterwarnings("ignore")

from app._paths import CACHE_DIR, ND_DIR

_LOG_PREFIX = "[ND-Enrich]"

# ── Paths ─────────────────────────────────────────────────────────────────────

TMDB_CSV = ND_DIR / "movies.csv"
MAIN_DATA_CSV = ND_DIR / "main_data.csv"
REVIEWS_TXT = ND_DIR / "reviews.txt"

# Cache
_CACHE_DIR = CACHE_DIR
_ENRICHMENT_CACHE = _CACHE_DIR / "nd_enrichment.pkl"


# ── Title normalization ───────────────────────────────────────────────────────


def _normalize(title: str) -> str:
    """Normalize a movie title for cross-referencing.

    - Lowercase
    - Strip whitespace
    - Remove trailing year like "(1995)"
    - Remove special characters like colons, apostrophes
    - Collapse multiple spaces
    """
    t = title.strip().lower()
    # Remove trailing year in parentheses: "toy story (1995)" -> "toy story"
    t = re.sub(r"\s*\(\d{4}\)\s*$", "", t)
    # Remove special characters (keep letters, digits, spaces)
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    # Collapse whitespace
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _tmdb_title(title: str) -> str:
    """Clean TMDB title for matching (lowercase, strip)."""
    t = title.strip().lower()
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


# ── Main enrichment class ─────────────────────────────────────────────────────


class NDEnrichment:
    """Loads and cross-references ND folder data to the main MovieLens dataset.

    Usage:
        enrich = NDEnrichment()
        metadata = enrich.get_metadata(movie_id)
        cast = enrich.get_cast(movie_id)
        reviews = enrich.get_reviews(movie_id)
    """

    def __init__(self, movies_df: pd.DataFrame | None = None):
        """Initialize enrichment by loading ND data.

        Parameters
        ----------
        movies_df : pd.DataFrame, optional
            The main MovieLens movies DataFrame (with columns movieId, title, genres).
            If provided, the ND data is cross-referenced immediately.
            If None, data is loaded but not indexed — call index_data(movies_df) later.
        """
        self._metadata_map: dict[int, dict[str, Any]] = {}  # movieId -> tmdb metadata
        self._cast_map: dict[int, dict[str, Any]] = {}  # movieId -> director + actors
        self._reviews_map: dict[int, list[str]] = {}  # movieId -> list of review texts
        self._director_to_movies: dict[str, list[int]] = (
            {}
        )  # director name -> list of movieIds (sorted after index_data)
        self._actor_to_movies: dict[str, list[int]] = (
            {}
        )  # actor name -> list of movieIds (sorted after index_data)

        self._loaded = False
        self._tfidf = None  # For keyword-based similarity (future)

        if movies_df is not None:
            # Try loading from cache first
            if self._try_load_cache(movies_df):
                print(f"{_LOG_PREFIX} Loaded enrichment from cache")
            else:
                self.index_data(movies_df)

    @property
    def is_loaded(self) -> bool:
        return self._loaded and bool(self._metadata_map)

    # ── Data loading ──────────────────────────────────────────────────────

    def _load_tmdb_data(self) -> pd.DataFrame:
        """Load ND/movies.csv (TMDB data). Returns DataFrame with normalized titles."""
        if not TMDB_CSV.exists():
            print(f"{_LOG_PREFIX} TMDB CSV not found at {TMDB_CSV}")
            return pd.DataFrame()

        try:
            df = pd.read_csv(TMDB_CSV, low_memory=False)
            if "title" not in df.columns:
                print(f"{_LOG_PREFIX} TMDB CSV missing 'title' column. Columns: {list(df.columns)}")
                return pd.DataFrame()

            # Normalize titles for matching
            df["_norm_title"] = df["title"].apply(_tmdb_title)
            print(f"{_LOG_PREFIX} Loaded {len(df)} TMDB movies")
            return df
        except Exception as e:
            print(f"{_LOG_PREFIX} Failed to load TMDB CSV: {e}")
            return pd.DataFrame()

    def _load_main_data(self) -> pd.DataFrame:
        """Load ND/main_data.csv (directors and actors)."""
        if not MAIN_DATA_CSV.exists():
            print(f"{_LOG_PREFIX} Main data CSV not found at {MAIN_DATA_CSV}")
            return pd.DataFrame()

        try:
            df = pd.read_csv(MAIN_DATA_CSV, low_memory=False)
            if "movie_title" not in df.columns:
                print(f"{_LOG_PREFIX} Main data CSV missing 'movie_title' column")
                return pd.DataFrame()

            df["_norm_title"] = df["movie_title"].apply(_normalize)
            print(f"{_LOG_PREFIX} Loaded {len(df)} rows of director/actor data")
            return df
        except Exception as e:
            print(f"{_LOG_PREFIX} Failed to load main data CSV: {e}")
            return pd.DataFrame()

    def _load_reviews(self) -> pd.DataFrame:
        """Load ND/reviews.txt (user text reviews)."""
        if not REVIEWS_TXT.exists():
            print(f"{_LOG_PREFIX} Reviews file not found at {REVIEWS_TXT}")
            return pd.DataFrame()

        try:
            # Tab-separated: movie_original_id \t review_text
            # Reviews have their own movie ID scheme (not our movieId)
            rows = []
            with open(REVIEWS_TXT, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if "\t" in line:
                        parts = line.split("\t", 1)
                        rows.append(
                            {
                                "review_movie_id": parts[0].strip(),
                                "review_text": parts[1].strip(),
                            }
                        )
            df = pd.DataFrame(rows)
            print(f"{_LOG_PREFIX} Loaded {len(df)} user reviews")
            return df
        except Exception as e:
            print(f"{_LOG_PREFIX} Failed to load reviews: {e}")
            return pd.DataFrame()

    # ── Cross-referencing ─────────────────────────────────────────────────

    def _try_load_cache(self, movies_df: pd.DataFrame) -> bool:
        """Try to load pre-computed enrichment from disk cache.

        Returns True if cache was loaded successfully, False otherwise.
        """
        if not _ENRICHMENT_CACHE.exists():
            return False

        # Check that source files haven't changed
        source_paths = [TMDB_CSV, MAIN_DATA_CSV, REVIEWS_TXT]
        cache_mtime = _ENRICHMENT_CACHE.stat().st_mtime
        for sp in source_paths:
            if sp.exists() and sp.stat().st_mtime > cache_mtime:
                print(f"{_LOG_PREFIX} Source file {sp.name} changed, invalidating cache")
                return False

        # Load full data from cache
        try:
            with open(_ENRICHMENT_CACHE, "rb") as f:
                data = pickle.load(f)
            self._metadata_map = data["_metadata_map"]
            self._cast_map = data["_cast_map"]
            self._reviews_map = data["_reviews_map"]
            self._director_to_movies = data["_director_to_movies"]
            self._actor_to_movies = data["_actor_to_movies"]
            self._loaded = True
            return True
        except Exception as e:
            print(f"{_LOG_PREFIX} Cache load failed: {e}")
            return False

    def _save_cache(self):
        """Save the current enrichment data to disk cache."""
        try:
            _CACHE_DIR.mkdir(exist_ok=True)
            data = {
                "_metadata_map": self._metadata_map,
                "_cast_map": self._cast_map,
                "_reviews_map": self._reviews_map,
                "_director_to_movies": self._director_to_movies,
                "_actor_to_movies": self._actor_to_movies,
            }
            with open(_ENRICHMENT_CACHE, "wb") as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
            print(f"{_LOG_PREFIX} Saved enrichment cache ({_ENRICHMENT_CACHE})")
        except Exception as e:
            print(f"{_LOG_PREFIX} Warning: could not save enrichment cache ({e})")

    def index_data(self, movies_df: pd.DataFrame):
        """Cross-reference ND data with the main MovieLens movies DataFrame.

        Performance: uses pandas vectorized ops and dict lookups instead of
        O(N*M) nested iteration. All loops are O(N) with O(1) dict lookups.
        Results are cached to disk for fast subsequent loads.
        """
        if movies_df is None or len(movies_df) == 0:
            print(f"{_LOG_PREFIX} No movies DataFrame provided, skipping indexing")
            return

        # Build normalized title lookup using pandas groupby (much faster)
        titles_normalized = movies_df["title"].apply(_normalize)
        norm_series = pd.Series(titles_normalized.values, index=movies_df["movieId"])
        norm_to_id: dict[str, list[int]] = (
            norm_series.groupby(norm_series).apply(lambda x: x.index.tolist()).to_dict()
        )

        # ── 1. Index TMDB metadata (vectorized merge approach) ────────────
        tmdb_df = self._load_tmdb_data()
        tmdb_matched = 0

        if len(tmdb_df) > 0:
            # Build a reverse lookup: norm -> list of TMDB rows (as dicts)
            tmdb_norm_groups = {}
            for _, tmdb_row in tmdb_df.iterrows():
                norm = tmdb_row.get("_norm_title", "")
                if not norm:
                    continue
                tmdb_norm_groups.setdefault(norm, []).append(tmdb_row)

            # Only iterate over norms that actually match
            for norm, tmdb_rows in tmdb_norm_groups.items():
                matched_ids = norm_to_id.get(norm)
                if not matched_ids:
                    continue
                for tmdb_row in tmdb_rows:
                    metadata = {
                        "overview": tmdb_row.get("overview", ""),
                        "tagline": tmdb_row.get("tagline", ""),
                        "budget": self._safe_int(tmdb_row.get("budget")),
                        "revenue": self._safe_int(tmdb_row.get("revenue")),
                        "runtime": self._safe_int(tmdb_row.get("runtime")),
                        "popularity": self._safe_float(tmdb_row.get("popularity")),
                        "vote_average": self._safe_float(tmdb_row.get("vote_average")),
                        "vote_count": self._safe_int(tmdb_row.get("vote_count")),
                        "homepage": str(tmdb_row.get("homepage", "")),
                        "original_language": str(tmdb_row.get("original_language", "")),
                        "production_companies": str(tmdb_row.get("production_companies", "")),
                        "production_countries": str(tmdb_row.get("production_countries", "")),
                        "keywords": str(tmdb_row.get("keywords", "")),
                        "status": str(tmdb_row.get("status", "")),
                        "tmdb_id": self._safe_int(tmdb_row.get("id")),
                        "release_date": str(tmdb_row.get("release_date", "")),
                        "director": str(tmdb_row.get("director", "")),
                        "cast": str(tmdb_row.get("cast", "")),
                    }
                    for mid in matched_ids:
                        if mid not in self._metadata_map:
                            self._metadata_map[mid] = metadata
                    tmdb_matched += len(matched_ids)

        print(f"{_LOG_PREFIX} TMDB: {tmdb_matched} movies matched out of {len(tmdb_df)}")

        # ── 2. Index director / actor data ────────────────────────────────
        cast_df = self._load_main_data()
        cast_matched = 0

        if len(cast_df) > 0:
            # Group cast rows by normalized title to minimize dict lookups
            cast_norm_groups = {}
            for _, cast_row in cast_df.iterrows():
                norm = cast_row.get("_norm_title", "")
                if not norm:
                    continue
                cast_norm_groups.setdefault(norm, []).append(cast_row)

            for norm, cast_rows in cast_norm_groups.items():
                matched_ids = norm_to_id.get(norm)
                if not matched_ids:
                    continue
                for cast_row in cast_rows:
                    director = str(cast_row.get("director_name", "")).strip()
                    actor1 = str(cast_row.get("actor_1_name", "")).strip()
                    actor2 = str(cast_row.get("actor_2_name", "")).strip()
                    actor3 = str(cast_row.get("actor_3_name", "")).strip()
                    actors = [a for a in [actor1, actor2, actor3] if a and a.lower() != "unknown"]

                    for mid in matched_ids:
                        if mid not in self._cast_map:
                            self._cast_map[mid] = {
                                "director": director,
                                "actors": actors,
                                "actors_raw": [actor1, actor2, actor3],
                            }
                        if director and director.lower() != "unknown":
                            self._director_to_movies.setdefault(director, set()).add(mid)
                        for actor in actors:
                            if actor and actor.lower() != "unknown":
                                self._actor_to_movies.setdefault(actor, set()).add(mid)

                    cast_matched += len(matched_ids)

            # Convert sets to sorted lists
            self._director_to_movies = {k: sorted(v) for k, v in self._director_to_movies.items()}
            self._actor_to_movies = {k: sorted(v) for k, v in self._actor_to_movies.items()}

        print(f"{_LOG_PREFIX} Cast: {cast_matched} movies matched out of {len(cast_df)}")
        print(f"{_LOG_PREFIX}   {len(self._director_to_movies)} unique directors indexed")
        print(f"{_LOG_PREFIX}   {len(self._actor_to_movies)} unique actors indexed")

        # ── 3. Index reviews ─────────────────────────────────────────────
        reviews_df = self._load_reviews()
        reviews_matched = 0
        if len(reviews_df) > 0:
            review_groups = reviews_df.groupby("review_movie_id")
            print(f"{_LOG_PREFIX}   {len(review_groups)} unique movies in reviews")

            # Heuristic keyword matching for popular movies
            known_movie_keywords = {
                "da vinci code": "da vinci code",
                "mission impossible": "mission impossible",
                "avatar": "avatar",
                "titanic": "titanic",
                "inception": "inception",
                "the matrix": "the matrix",
                "star wars": "star wars",
                "the dark knight": "the dark knight",
                "harry potter": "harry potter",
                "pirates of the caribbean": "pirates of the caribbean",
                "lord of the rings": "lord of the rings",
                "the hunger games": "the hunger games",
                "transformers": "transformers",
            }

            review_to_norm: dict[str, str] = {}
            for rev_id, group in review_groups:
                combined = " ".join(group["review_text"].iloc[:5].tolist()).lower()
                for keyword, title in known_movie_keywords.items():
                    if keyword in combined:
                        review_to_norm[rev_id] = title
                        break

            for rev_id, norm_title in review_to_norm.items():
                matched_ids = norm_to_id.get(norm_title) or norm_to_id.get(_normalize(norm_title))
                if matched_ids:
                    texts = review_groups.get_group(rev_id)["review_text"].tolist()
                    for mid in matched_ids:
                        if mid not in self._reviews_map:
                            self._reviews_map[mid] = texts[:20]
                        else:
                            self._reviews_map[mid].extend(texts[:20])
                            self._reviews_map[mid] = self._reviews_map[mid][:20]
                    reviews_matched += 1

            print(f"{_LOG_PREFIX} Reviews: {reviews_matched} movies matched with reviews")
        else:
            print(f"{_LOG_PREFIX} No reviews to index")

        self._loaded = True

        # Save to cache after indexing completes
        self._save_cache()

    # ── Lookup methods ───────────────────────────────────────────────────

    def get_metadata(self, movie_id: int) -> dict[str, Any] | None:
        """Get TMDB-enriched metadata for a movie.

        Returns dict with keys: overview, tagline, budget, revenue, runtime,
        popularity, vote_average, vote_count, homepage, original_language,
        production_companies, keywords, director, cast, release_date, status.
        Returns None if no data available.
        """
        return self._metadata_map.get(movie_id)

    def get_cast(self, movie_id: int) -> dict[str, Any] | None:
        """Get director and actor info for a movie.

        Returns {'director': str, 'actors': list[str], 'actors_raw': list[str]}.
        Returns None if no data available.
        """
        return self._cast_map.get(movie_id)

    def get_reviews(self, movie_id: int) -> list[str] | None:
        """Get user review texts for a movie.

        Returns list of review text strings, or None.
        """
        return self._reviews_map.get(movie_id)

    def get_movies_by_director(self, director: str) -> list[int]:
        """Get list of movieIds directed by a given person."""
        return self._director_to_movies.get(director, [])

    def get_movies_by_actor(self, actor: str) -> list[int]:
        """Get list of movieIds featuring a given actor."""
        return self._actor_to_movies.get(actor, [])

    def has_data(self, movie_id: int) -> bool:
        """Check if any enrichment data exists for this movie."""
        return (
            movie_id in self._metadata_map
            or movie_id in self._cast_map
            or movie_id in self._reviews_map
        )

    # ── Utility ──────────────────────────────────────────────────────────

    def get_cache_size_estimate(self) -> int:
        """Get approximate number of movies with enrichment data."""
        return len(self._metadata_map)

    @staticmethod
    def _safe_int(val) -> int | None:
        try:
            v = int(float(str(val).strip()))
            return v if v > 0 else None
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _safe_float(val) -> float | None:
        try:
            v = float(str(val).strip())
            return v if v > 0 else None
        except (ValueError, TypeError):
            return None

    def format_budget(self, movie_id: int) -> str:
        """Format budget as human-readable string."""
        meta = self.get_metadata(movie_id)
        if not meta or not meta.get("budget"):
            return ""
        b = meta["budget"]
        if b >= 1_000_000_000:
            return f"${b / 1_000_000_000:.1f}B"
        elif b >= 1_000_000:
            return f"${b / 1_000_000:.0f}M"
        elif b >= 1_000:
            return f"${b / 1_000:.0f}K"
        return f"${b}"

    def format_revenue(self, movie_id: int) -> str:
        """Format revenue as human-readable string."""
        meta = self.get_metadata(movie_id)
        if not meta or not meta.get("revenue"):
            return ""
        r = meta["revenue"]
        if r >= 1_000_000_000:
            return f"${r / 1_000_000_000:.1f}B"
        elif r >= 1_000_000:
            return f"${r / 1_000_000:.0f}M"
        elif r >= 1_000:
            return f"${r / 1_000:.0f}K"
        return f"${r}"

    def format_runtime(self, movie_id: int) -> str:
        """Format runtime as hours and minutes."""
        meta = self.get_metadata(movie_id)
        if not meta or not meta.get("runtime"):
            return ""
        mins = meta["runtime"]
        h = mins // 60
        m = mins % 60
        if h > 0 and m > 0:
            return f"{h}h {m}m"
        elif h > 0:
            return f"{h}h"
        return f"{m}m"

    def get_status_summary(self, movie_id: int) -> dict[str, Any]:
        """Get a concise summary dict of all enrichment data for a movie."""
        meta = self.get_metadata(movie_id)
        cast = self.get_cast(movie_id)
        reviews = self.get_reviews(movie_id)

        summary = {}
        if meta:
            if meta.get("overview"):
                summary["overview"] = meta["overview"]
            if meta.get("tagline"):
                summary["tagline"] = meta["tagline"]
            if meta.get("runtime"):
                summary["runtime"] = self.format_runtime(movie_id)
            if meta.get("budget"):
                summary["budget"] = self.format_budget(movie_id)
            if meta.get("revenue"):
                summary["revenue"] = self.format_revenue(movie_id)
            if meta.get("vote_average"):
                summary["rating"] = meta["vote_average"]
            if meta.get("popularity"):
                summary["popularity"] = f"{meta['popularity']:.1f}"

        if cast:
            if (
                cast.get("director")
                and cast["director"].lower() != "unknown"
                and cast["director"].lower() != "nan"
            ):
                summary["director"] = cast["director"]
            if cast.get("actors"):
                summary["actors"] = cast["actors"]

        if reviews:
            summary["reviews"] = len(reviews)

        return summary


# ── Quick test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"{_LOG_PREFIX} Testing ND enrichment...")

    # Quick test with minimal movies DataFrame
    test_movies = pd.DataFrame(
        {
            "movieId": [1, 2, 3],
            "title": ["Toy Story (1995)", "Avatar (2009)", "The Dark Knight (2008)"],
            "genres": [
                "Animation|Children|Comedy",
                "Action|Adventure|Fantasy",
                "Action|Crime|Drama",
            ],
        }
    )

    enrich = NDEnrichment(test_movies)

    print(f"\nLoaded: {enrich.is_loaded}")
    print(f"Movies with metadata: {len(enrich._metadata_map)}")
    print(f"Movies with cast: {len(enrich._cast_map)}")
    print(f"Unique directors: {len(enrich._director_to_movies)}")
    print(f"Unique actors: {len(enrich._actor_to_movies)}")

    # Test lookup
    for mid in [1, 2, 3]:
        meta = enrich.get_metadata(mid)
        cast = enrich.get_cast(mid)
        if meta:
            print(f"\n--- Movie {mid} ---")
            if meta.get("overview"):
                print(f"  Overview: {meta['overview'][:80]}...")
            if meta.get("tagline"):
                print(f"  Tagline: {meta['tagline']}")
            if meta.get("runtime"):
                print(f"  Runtime: {enrich.format_runtime(mid)}")
            if meta.get("budget"):
                print(f"  Budget: {enrich.format_budget(mid)}")
        if cast:
            if cast.get("director"):
                print(f"  Director: {cast['director']}")
            if cast.get("actors"):
                print(f"  Actors: {', '.join(cast['actors'][:3])}")

    print(f"\n{_LOG_PREFIX} Enrichment test complete!")
