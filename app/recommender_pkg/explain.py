"""Recommender — Prediction explanation and top picks mixin."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class ExplainMixin:
    """Feature breakdown, prediction explanation, and global top picks."""

    def get_feature_breakdown(self, movie_id: int) -> dict[str, Any] | None:
        """Get feature importance breakdown for a movie's prediction."""
        if movie_id not in self.movies_by_id or self.model_result is None:
            return None

        row = self.movies_by_id[movie_id]
        movie_info = self.get_movie_info(movie_id)
        if movie_info is None:
            return None

        pred = movie_info["predicted_rating"]
        if pred is None:
            return None

        try:
            explanation = self._explain_prediction(
                row,
                pred,
                self.model_result["best_model"],
                self.model_result["scaler"],
                self.model_result["feature_cols"],
                self.model_result["num_cols"],
                self.model_result["importance"],
            )
            return {"prediction": pred, "explanation": explanation}
        except (ValueError, KeyError, TypeError) as e:
            return {"prediction": pred, "explanation": None, "error": str(e)}

    def _explain_prediction(
        self,
        movie_row: pd.Series,
        prediction: float,
        model,
        scaler,
        feature_cols: list[str],
        num_cols: list[str],
        importance_df: pd.DataFrame,
    ) -> str:
        """Build a feature-contribution explanation for a prediction."""
        present_num = [c for c in num_cols if c in feature_cols]
        genre_list = movie_row["genre_list"]

        def _build_raw() -> pd.DataFrame:
            f = pd.DataFrame([0.0] * len(feature_cols), index=feature_cols).T
            for g in genre_list:
                if g in f.columns:
                    f.at[0, g] = 1.0
            if self.tag_pivot is not None and len(self.tag_pivot) > 0:
                mt = self.tag_pivot[self.tag_pivot["movieId"] == movie_row["movieId"]]
                if len(mt) > 0:
                    for c in self.tag_pivot.columns:
                        if c != "movieId" and c in f.columns:
                            try:
                                f.at[0, c] = float(mt.iloc[0][c])
                            except (ValueError, KeyError):
                                pass
            f.at[0, "genre_count"] = len(genre_list)
            f.at[0, "title_length"] = len(str(movie_row.get("title", "")))
            f.at[0, "title_words"] = len(str(movie_row.get("title", "")).split())
            f.at[0, "rating_count"] = 50.0
            yv = movie_row.get("year", 2000)
            if pd.isna(yv) or yv == 0:
                yv = 2000
            f.at[0, "year"] = yv
            return f

        feats_raw = _build_raw()
        feats_scaled = feats_raw.copy()
        if present_num:
            feats_scaled[present_num] = scaler.transform(feats_scaled[present_num])

        full_pred = float(model.predict(feats_scaled)[0])

        contributions = []
        for feat_name in importance_df["feature"].head(30).tolist():
            if feat_name not in feats_raw.columns:
                continue
            is_active = abs(feats_raw.at[0, feat_name]) > 0.01
            if not is_active and feat_name not in present_num:
                continue
            feats_copy = feats_raw.copy()
            feats_copy.at[0, feat_name] = 0.0
            if feat_name in genre_list:
                feats_copy.at[0, "genre_count"] = max(0, feats_raw.at[0, "genre_count"] - 1)
            if present_num:
                feats_copy[present_num] = scaler.transform(feats_copy[present_num])
            pred_without = float(model.predict(feats_copy)[0])
            effect = full_pred - pred_without
            contributions.append((feat_name, effect))

        contributions = [(n, v) for n, v in contributions if abs(v) > 0.001]
        contributions.sort(key=lambda x: abs(x[1]), reverse=True)

        lines = []
        lines.append(f"  Predicted rating: {prediction:.2f} / 5.0")
        lines.append("  Assumed rating count: 50")
        lines.append("")
        lines.append("  Top contributing features:")
        for feat_name, effect in contributions[:12]:
            display_name = feat_name.replace("tag_", "tag:")
            bar_len = min(int(abs(effect) / 0.5 * 30), 30)
            bar_str = "#" * bar_len + "." * (30 - bar_len)
            direction = "+" if effect > 0 else "-"
            lines.append(f"    {direction} {display_name:<30s} {bar_str}  {effect:+.4f}")

        lines.append("")
        lines.append(f"    (Baseline prediction: {full_pred:.4f})")
        return "\n".join(lines)

    def get_top_picks(
        self,
        genre: str | None = None,
        n: int = 20,
        min_year: int = 1990,
    ) -> list[dict[str, Any]]:
        """Get top predicted picks globally or filtered by genre."""
        candidates = self.movies

        if genre:
            mask = candidates["genres"].str.contains(genre, na=False, case=False)
            candidates = candidates[mask]

        if min_year:
            candidates = candidates[candidates["year"] >= min_year]

        # Predict ratings for top candidates (max 500 for speed)
        # Sort by rating_count (popularity proxy) to get better samples
        candidates = (
            candidates.sort_values("rating_count", ascending=False)
            if "rating_count" in candidates.columns
            else candidates
        )
        sample = candidates.head(500)
        scored = []
        for _, row in sample.iterrows():
            mid = row["movieId"]
            pred = self._predict_cached(mid)
            if pred is not None:
                scored.append((pred, mid))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for pred, mid in scored[:n]:
            info = self.get_movie_info(mid)
            if info:
                results.append({**info, "predicted_rating": pred})

        return results


# ── Quick test ────────────────────────────────────────────────────────────────
