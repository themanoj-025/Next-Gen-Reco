"""
MovieLens Rating Predictor — Interactive Test Harness
======================================================
Usage:
    python test_model.py                  # Quick demo (trains model, shows examples)
    python test_model.py --load <name>    # Load saved model, run demo (no retrain!)
    python test_model.py --train          # Interactive mode (trains model first)
    python test_model.py --demo           # Same as default — quick demo
    python test_model.py --quick          # Fast mode (100K samples, no tuning)

Commands (interactive mode):
    search <query>     — Search movies by title
    predict <movieId>  — Predict rating for a movie
    compare <id1,id2>  — Compare two movies side-by-side
    genre <genre>      — List top-rated movies in a genre
    explain <movieId>  — Show which features drive the prediction
    browse             — Browse sample movies
    model              — Show model info and metrics
    help               — Show this help
    quit               — Exit
"""

import sys
import time
import warnings
from typing import Any

import pandas as pd

warnings.filterwarnings("ignore")

# ── Imports from model.py ─────────────────────────────────────────────────────
from app.model import (
    load_model,
    load_movies,
    load_ratings_sample,
    load_tags,
    predict_rating,
    train_model,
)

# ── Helpers ───────────────────────────────────────────────────────────────────


def _format_bar(value: float, width: int = 30, max_imp: float = 0.3) -> str:
    """Render an ASCII bar proportional to the value."""
    bar_len = min(int(value / max_imp * width), width)
    bar_str = "#" * bar_len + "." * width
    return bar_str[:width]


def _colorize(val: float, low: float = 2.0, high: float = 4.0) -> str:
    """Simple ANSI color for rating values."""
    if val >= high:
        return f"\033[92m{val:.2f}\033[0m"  # green
    elif val <= low:
        return f"\033[91m{val:.2f}\033[0m"  # red
    return f"\033[93m{val:.2f}\033[0m"  # yellow


def _clear_screen():
    """Clear terminal."""
    print("\033[2J\033[H", end="")


def _explain_prediction(
    movie_row: pd.Series,
    prediction: float,
    model,
    scaler,
    feature_cols: list[str],
    num_cols: list[str],
    importance_df: pd.DataFrame,
    tag_pivot: pd.DataFrame | None = None,
    rating_count: float = 50.0,
) -> str:
    """
    Build a feature-contribution explanation for a prediction.

    Builds the raw (unscaled) feature vector once, then for each
    important feature creates a copy with that feature zeroed out,
    re-scales, and measures the prediction delta.
    """
    present_num = [c for c in num_cols if c in feature_cols]
    genre_list = movie_row["genre_list"]

    def _build_raw() -> pd.DataFrame:
        """Build unscaled feature vector."""
        f = pd.DataFrame([0.0] * len(feature_cols), index=feature_cols).T
        for g in genre_list:
            if g in f.columns:
                f.at[0, g] = 1.0
        if tag_pivot is not None and len(tag_pivot) > 0:
            mt = tag_pivot[tag_pivot["movieId"] == movie_row["movieId"]]
            if len(mt) > 0:
                for c in tag_pivot.columns:
                    if c != "movieId" and c in f.columns:
                        try:
                            f.at[0, c] = float(mt.iloc[0][c])
                        except (ValueError, KeyError):
                            pass
        f.at[0, "genre_count"] = len(genre_list)
        f.at[0, "title_length"] = len(str(movie_row.get("title", "")))
        f.at[0, "title_words"] = len(str(movie_row.get("title", "")).split())
        f.at[0, "rating_count"] = rating_count
        yv = movie_row.get("year", 2000)
        if pd.isna(yv):
            yv = 2000
        f.at[0, "year"] = yv
        return f

    lines = []
    lines.append(f"  Predicted rating: {_colorize(prediction)} / 5.0")
    lines.append(f"  Assumed rating count: {int(rating_count)}")
    lines.append("")

    # Build and scale the full feature vector
    feats_raw = _build_raw()
    feats_scaled = feats_raw.copy()
    if present_num:
        feats_scaled[present_num] = scaler.transform(feats_scaled[present_num])
    full_pred = float(model.predict(feats_scaled)[0])

    # --- Compute per-feature effect ---
    contributions = []
    for feat_name in importance_df["feature"].head(30).tolist():
        if feat_name not in feats_raw.columns:
            continue

        # Only measure features that are "active" (non-zero) for this movie
        is_active = abs(feats_raw.at[0, feat_name]) > 0.01
        if not is_active and feat_name not in present_num:
            continue

        # Create a copy with this feature zeroed (in raw space)
        feats_copy = feats_raw.copy()
        feats_copy.at[0, feat_name] = 0.0

        # If it's a genre, also adjust genre_count
        if feat_name in genre_list:
            feats_copy.at[0, "genre_count"] = max(0, feats_raw.at[0, "genre_count"] - 1)

        # Scale numeric columns
        if present_num:
            feats_copy[present_num] = scaler.transform(feats_copy[present_num])

        pred_without = float(model.predict(feats_copy)[0])
        effect = full_pred - pred_without
        contributions.append((feat_name, effect))

    # Only keep features with non-trivial effect
    contributions = [(n, v) for n, v in contributions if abs(v) > 0.001]
    contributions.sort(key=lambda x: abs(x[1]), reverse=True)

    lines.append("  Top contributing features:")
    for feat_name, effect in contributions[:12]:
        display_name = feat_name.replace("tag_", "tag:")
        bar_len = int(min(abs(effect) / 0.5 * 30, 30))
        bar = "#" * bar_len + "." * (30 - bar_len)
        direction = "+" if effect > 0 else "-"
        lines.append(f"    {direction} {display_name:<30s} {bar}  {effect:+.4f}")

    lines.append("")
    lines.append(f"    (Baseline prediction: {full_pred:.4f})")

    return "\n".join(lines)


# ── Interactive mode ──────────────────────────────────────────────────────────


class ModelTester:
    """Interactive test harness for the rating prediction model."""

    def __init__(self, result: dict[str, Any]):
        self.result = result
        self.movies = load_movies()
        self.tag_pivot = load_tags(top_k=100) if result.get("xgb_model") else None

        # Quick lookup by movieId
        self.movies_by_id = {row["movieId"]: row for _, row in self.movies.iterrows()}

        # Genre list
        all_genres = set()
        for glist in self.movies["genre_list"]:
            all_genres.update(glist)
        self.genres = sorted(all_genres)

        # Load ratings stats for real rating_counts
        ratings = load_ratings_sample(n=500_000)
        self.movie_rating_counts = dict(ratings.groupby("movieId")["rating"].count().items())

    def _get_rating_count(self, movie_id: int) -> float:
        return float(self.movie_rating_counts.get(movie_id, 50))

    def cmd_search(self, query: str):
        """Search movies by title keyword."""
        q = query.lower()
        matches = self.movies[self.movies["title"].str.lower().str.contains(q, na=False)]
        if len(matches) == 0:
            print(f"  No movies found matching '{query}'")
            return

        # Show top 20
        results = matches.head(20)
        print(f"  Found {len(matches):,} movies (showing first {len(results)}):")
        print(f"  {'ID':>7s}  {'Year':>4s}  {'Rating':>7s}  {'Count':>6s}  Title")
        print(f"  {'-' * 7}  {'-' * 4}  {'-' * 7}  {'-' * 6}  {'-' * 30}")
        for _, row in results.iterrows():
            movie_id = row["movieId"]
            rc = self._get_rating_count(movie_id)
            # Predict if we have it
            pred_str = "  ?  "
            if movie_id in self.movies_by_id:
                try:
                    pred = predict_rating(
                        row,
                        self.result["best_model"],
                        self.result["scaler"],
                        self.result["feature_cols"],
                        self.result["num_cols"],
                        tag_pivot=self.tag_pivot,
                        rating_count=rc,
                    )
                    pred_str = f"{pred:.2f}"
                except (ValueError, KeyError, TypeError):
                    pred_str = "  ?  "
            year_str = str(int(row["year"])) if pd.notna(row["year"]) else "?"
            print(
                f"  {movie_id:>7d}  {year_str:>4s}  {pred_str:>7s}  "
                f"{int(rc):>5d}  {row['title'][:50]}"
            )

    def cmd_predict(self, movie_id_str: str):
        """Predict rating for a specific movieId."""
        try:
            movie_id = int(movie_id_str)
        except ValueError:
            print("  Invalid movie ID. Use 'search <title>' to find IDs.")
            return

        if movie_id not in self.movies_by_id:
            print(f"  Movie ID {movie_id} not found.")
            return

        row = self.movies_by_id[movie_id]
        rc = self._get_rating_count(movie_id)

        print(f"\n  Movie: {row['title']}")
        print(f"  Genres: {', '.join(row['genre_list'])}")
        print(f"  Year: {int(row['year']) if pd.notna(row['year']) else '?'}")
        print(f"  Rating count in sample: {int(rc)}")

        # Predict with different rating_count assumptions
        print("\n  Predictions with different rating_count assumptions:")
        for rc_val in [5, 20, 50, 200, 1000, 5000]:
            pred = predict_rating(
                row,
                self.result["best_model"],
                self.result["scaler"],
                self.result["feature_cols"],
                self.result["num_cols"],
                tag_pivot=self.tag_pivot,
                rating_count=rc_val,
            )
            count_str = f"{rc_val:>5d}"
            print(f"    count={count_str} -> {_colorize(pred)}")

    def cmd_compare(self, ids_str: str):
        """Compare two movies side-by-side."""
        parts = ids_str.replace(",", " ").split()
        if len(parts) < 2:
            print("  Usage: compare <movieId1> <movieId2>")
            return

        try:
            id1, id2 = int(parts[0]), int(parts[1])
        except ValueError:
            print("  Invalid IDs.")
            return

        movies_data = []
        for mid in [id1, id2]:
            if mid in self.movies_by_id:
                row = self.movies_by_id[mid]
                rc = self._get_rating_count(mid)
                pred = predict_rating(
                    row,
                    self.result["best_model"],
                    self.result["scaler"],
                    self.result["feature_cols"],
                    self.result["num_cols"],
                    tag_pivot=self.tag_pivot,
                    rating_count=rc,
                )
                movies_data.append((row, pred, rc))
            else:
                print(f"  Movie ID {mid} not found.")
                return

        row1, pred1, rc1 = movies_data[0]
        row2, pred2, rc2 = movies_data[1]

        print()
        print(f"  {'Attribute':<20s}  {'Movie 1':<40s}  {'Movie 2':<40s}")
        print(f"  {'-' * 20}  {'-' * 40}  {'-' * 40}")
        print(f"  {'Title':<20s}  {row1['title'][:38]:<40s}  {row2['title'][:38]:<40s}")
        print(
            f"  {'Year':<20s}  {str(int(row1['year'])) if pd.notna(row1['year']) else '?':<40s}  {str(int(row2['year'])) if pd.notna(row2['year']) else '?':<40s}"
        )
        print(
            f"  {'Genres':<20s}  {', '.join(row1['genre_list'][:3]):<40s}  {', '.join(row2['genre_list'][:3]):<40s}"
        )
        print(f"  {'Rating count':<20s}  {int(rc1):<40d}  {int(rc2):<40d}")
        print(f"  {'Predicted':<20s}  {_colorize(pred1):<40s}  {_colorize(pred2):<40s}")

        diff = pred1 - pred2
        if abs(diff) > 0.1:
            winner = "Movie 1" if diff > 0 else "Movie 2"
            print(f"\n  >> {winner} predicted {abs(diff):.2f} points higher")

    def cmd_genre(self, genre_name: str):
        """List top-rated movies in a genre (by predicted rating)."""
        genre_match = genre_name.lower().strip()
        # Find matching genre
        matched = [g for g in self.genres if genre_match in g.lower()]
        if not matched:
            print(f"  No genres matching '{genre_name}'.")
            print(f"  Available genres: {', '.join(self.genres[:15])}...")
            return

        genre = matched[0]
        if len(matched) > 1:
            print(f"  Matching genres: {', '.join(matched)}")
            genre = matched[0]

        # Find movies with this genre
        mask = self.movies["genres"].str.contains(genre, na=False)
        candidates = self.movies[mask].copy()
        print(f"  Found {len(candidates):,} movies with genre '{genre}'")
        print("  Predicting top 15...")

        # Predict for a sample
        results = []
        sample = candidates.head(200)
        for _, row in sample.iterrows():
            mid = row["movieId"]
            rc = self._get_rating_count(mid)
            try:
                pred = predict_rating(
                    row,
                    self.result["best_model"],
                    self.result["scaler"],
                    self.result["feature_cols"],
                    self.result["num_cols"],
                    tag_pivot=self.tag_pivot,
                    rating_count=rc,
                )
                results.append((pred, row))
            except (ValueError, KeyError, TypeError):
                pass

        results.sort(key=lambda x: x[0], reverse=True)

        print(f"\n  {'Rank':>4s}  {'Pred':>5s}  {'Year':>4s}  Title")
        print(f"  {'-' * 4}  {'-' * 5}  {'-' * 4}  {'-' * 40}")
        for i, (pred, row) in enumerate(results[:15]):
            year_str = str(int(row["year"])) if pd.notna(row["year"]) else "?"
            print(f"  {i + 1:>4d}  {_colorize(pred):>5s}  {year_str:>4s}  " f"{row['title'][:55]}")

    def cmd_explain(self, movie_id_str: str):
        """Show feature-by-feature explanation of a prediction."""
        try:
            movie_id = int(movie_id_str)
        except ValueError:
            print("  Invalid movie ID.")
            return

        if movie_id not in self.movies_by_id:
            print(f"  Movie ID {movie_id} not found.")
            return

        row = self.movies_by_id[movie_id]
        rc = self._get_rating_count(movie_id)

        pred = predict_rating(
            row,
            self.result["best_model"],
            self.result["scaler"],
            self.result["feature_cols"],
            self.result["num_cols"],
            tag_pivot=self.tag_pivot,
            rating_count=rc,
        )

        print(f"\n  Movie: {row['title']}")
        print(f"  Genres: {', '.join(row['genre_list'])}")
        print(f"  Year: {int(row['year']) if pd.notna(row['year']) else '?'}")
        print(f"  Rating count: {int(rc)}")
        print()

        explanation = _explain_prediction(
            row,
            pred,
            self.result["best_model"],
            self.result["scaler"],
            self.result["feature_cols"],
            self.result["num_cols"],
            self.result["importance"],
            tag_pivot=self.tag_pivot,
            rating_count=rc,
        )
        print(explanation)

    def cmd_browse(self):
        """Browse a random sample of movies with predictions."""
        sample = self.movies.sample(n=20, random_state=int(time.time()) % 1000)
        print("\n  Random movie sample (predicted ratings):")
        print(f"  {'ID':>7s}  {'Year':>4s}  {'Pred':>5s}  {'Count':>5s}  Title")
        print(f"  {'-' * 7}  {'-' * 4}  {'-' * 5}  {'-' * 5}  {'-' * 40}")
        for _, row in sample.iterrows():
            mid = row["movieId"]
            rc = self._get_rating_count(mid)
            try:
                pred = predict_rating(
                    row,
                    self.result["best_model"],
                    self.result["scaler"],
                    self.result["feature_cols"],
                    self.result["num_cols"],
                    tag_pivot=self.tag_pivot,
                    rating_count=rc,
                )
                pred_str = _colorize(pred)
            except (ValueError, KeyError, TypeError):
                pred_str = "  ?  "
            year_str = str(int(row["year"])) if pd.notna(row["year"]) else "?"
            print(
                f"  {mid:>7d}  {year_str:>4s}  {pred_str:>5s}  "
                f"{int(rc):>5d}  {row['title'][:50]}"
            )

    def cmd_model(self):
        """Show model details."""
        result = self.result
        metrics = result["metrics"]
        imp = result["importance"]
        best_name = result["best_model_name"]

        print(f"\n  Model: {best_name}")
        print(f"  Features: {metrics['feature_count']:,}")
        print(f"  Training samples: {metrics['train_samples']:,}")
        print(f"  Test samples: {metrics['test_samples']:,}")
        print()

        for model_name in ["RandomForest", "XGBoost"]:
            if model_name in metrics:
                m = metrics[model_name]
                print(f"  {model_name}:")
                print(f"    R^2:   {m['R2']:.4f}")
                print(f"    RMSE: {m['RMSE']:.4f}")
                print(f"    MAE:  {m['MAE']:.4f}")

        if result.get("rf_params"):
            print(f"\n  Best RF params: {result['rf_params']}")

        print("\n  Top 10 Features:")
        for _, row in imp.head(10).iterrows():
            bar = _format_bar(row["importance"])
            display_name = row["feature"].replace("tag_", "tag:")
            print(f"    {bar}  {display_name:<30s}  {row['importance']:.4f}")

    def cmd_help(self):
        """Show help."""
        print(
            """
  Commands:
    search <query>     Search movies by title keyword
    predict <id>       Predict rating for a movie ID
    compare <id1 id2>  Compare two movies side-by-side
    genre <name>       Show top predicted movies in a genre
    explain <id>       Show feature contributions for a prediction
    browse             Show random movies with predictions
    model              Show model performance and features
    help               Show this help message
    quit               Exit
  Examples:
    search toy
    predict 1
    compare 1 2
    genre comedy
    explain 1
"""
        )

    def run_interactive(self):
        """Run the interactive REPL."""
        _clear_screen()
        header = "MovieLens Rating Predictor - Interactive Mode"
        print("/" + "-" * 58 + "\\")
        print(f"|  {header:<56s}|")
        print(f"|  Type 'help' for commands, 'quit' to exit{' ' * 26}|")
        print("\\" + "-" * 58 + "/")

        while True:
            try:
                cmd = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n  Goodbye!")
                break

            if not cmd:
                continue

            parts = cmd.split(maxsplit=1)
            action = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            if action in ("quit", "exit", "q"):
                print("  Goodbye!")
                break
            elif action == "help" or action == "?":
                self.cmd_help()
            elif action == "search":
                if arg:
                    self.cmd_search(arg)
                else:
                    print("  Usage: search <movie title>")
            elif action == "predict":
                if arg:
                    self.cmd_predict(arg)
                else:
                    print("  Usage: predict <movieId>")
            elif action == "compare":
                if arg:
                    self.cmd_compare(arg)
                else:
                    print("  Usage: compare <id1> <id2>")
            elif action == "genre":
                if arg:
                    self.cmd_genre(arg)
                else:
                    print("  Usage: genre <genre name>")
            elif action == "explain":
                if arg:
                    self.cmd_explain(arg)
                else:
                    print("  Usage: explain <movieId>")
            elif action == "browse":
                self.cmd_browse()
            elif action == "model":
                self.cmd_model()
            else:
                print(f"  Unknown command: {action}. Type 'help' for options.")


# ── Quick demo ────────────────────────────────────────────────────────────────


def quick_demo(result: dict[str, Any]):
    """Show a curated demo of the model's capabilities."""
    _clear_screen()
    metrics = result["metrics"]
    imp = result["importance"]
    best_name = result["best_model_name"]

    print("\n" + "=" * 58)
    print("  MovieLens Rating Predictor — Quick Demo")
    print("=" * 58)

    # Model summary
    print(f"\n  Best Model: {best_name}")
    print(f"  Features:  {metrics['feature_count']:,}")
    print(f"  Samples:   {metrics['train_samples']:,} train / " f"{metrics['test_samples']:,} test")

    for model_name in ["RandomForest", "XGBoost"]:
        if model_name in metrics:
            m = metrics[model_name]
            print(
                f"  {model_name}:  R^2={m['R2']:.4f}  " f"RMSE={m['RMSE']:.4f}  MAE={m['MAE']:.4f}"
            )

    # Top features
    print("\n  Top 10 Features:")
    for _, row in imp.head(10).iterrows():
        bar = _format_bar(row["importance"])
        display_name = row["feature"].replace("tag_", "tag:")
        print(f"    {bar}  {display_name:<30s}  {row['importance']:.4f}")

    # Demo predictions on famous movies
    movies = load_movies()
    tag_pivot = load_tags(top_k=100)

    famous_movies = [
        "Toy Story (1995)",
        "The Shawshank Redemption (1994)",
        "The Godfather (1972)",
        "Pulp Fiction (1994)",
        "The Dark Knight (2008)",
        "Fight Club (1999)",
        "Forrest Gump (1994)",
        "The Matrix (1999)",
        "Star Wars: Episode IV - A New Hope (1977)",
        "Jurassic Park (1993)",
    ]

    print("\n  Sample Predictions:")
    print(f"  {'Title':<45s}  {'Pred':>5s}  {'Count':>6s}")
    print(f"  {'-' * 45}  {'-' * 5}  {'-' * 6}")

    # Load ratings once, reuse for all movies
    demo_ratings = load_ratings_sample(n=500_000)
    demo_rc_cache = dict(demo_ratings.groupby("movieId")["rating"].count().items())

    for title in famous_movies:
        match = movies[movies["title"] == title]
        if len(match) > 0:
            row = match.iloc[0]
            mid = row["movieId"]
            rc = float(demo_rc_cache.get(mid, 50))
            pred = predict_rating(
                row,
                result["best_model"],
                result["scaler"],
                result["feature_cols"],
                result["num_cols"],
                tag_pivot=tag_pivot,
                rating_count=rc,
            )
            print(f"  {title[:43]:<45s}  {_colorize(pred):>5s}  {int(rc):>5d} ")

    # Example explanation
    toy_story = movies[movies["title"] == "Toy Story (1995)"].iloc[0]
    ts_rc = float(demo_rc_cache.get(1, 50))
    pred = predict_rating(
        toy_story,
        result["best_model"],
        result["scaler"],
        result["feature_cols"],
        result["num_cols"],
        tag_pivot=tag_pivot,
        rating_count=ts_rc,
    )

    explanation = _explain_prediction(
        toy_story,
        pred,
        result["best_model"],
        result["scaler"],
        result["feature_cols"],
        result["num_cols"],
        imp,
        tag_pivot=tag_pivot,
        rating_count=50.0,
    )
    print(f"\n\n  Toy Story (1995) — Feature Breakdown:\n{explanation}")

    print("\n  " + "-" * 58)
    print("  Run 'python test_model.py --train' for interactive mode!")
    print("  " + "-" * 58 + "\n")


# ── Entry point ───────────────────────────────────────────────────────────────


def main():
    args = [a.lower() for a in sys.argv[1:]]

    is_interactive = "--train" in args
    is_quick = "--quick" in args

    # Check for --load flag
    load_name = None
    for i, a in enumerate(args):
        if a in ("--load", "-l") and i + 1 < len(args):
            load_name = args[i + 1]
        elif a.startswith(("--load=", "-l=")):
            load_name = a.split("=", 1)[1]

    if load_name:
        print(f"Loading saved model '{load_name}'...")
        result = load_model(name=load_name)
        if is_interactive:
            tester = ModelTester(result)
            tester.run_interactive()
        else:
            quick_demo(result)
        return

    if is_quick:
        print("Quick mode: 100K samples, no tuning, no tags\n")
        result = train_model(
            sample_size=100_000,
            use_tags=False,
            use_tuning=False,
        )
        quick_demo(result)
        return

    if is_interactive:
        result = train_model(
            sample_size=500_000,
            use_tags=True,
            top_tags=100,
            use_tuning=True,
        )

        tester = ModelTester(result)
        tester.run_interactive()
    else:
        # Default: train + quick demo
        result = train_model(
            sample_size=500_000,
            use_tags=True,
            top_tags=100,
            use_tuning=True,
        )
        quick_demo(result)


if __name__ == "__main__":
    main()
