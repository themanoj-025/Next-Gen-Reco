"""CLI entry point for model training and comparison.

Extracted from model.py to keep the model module focused on
data loading, training, and prediction logic.
"""

from app.model import (
    load_model,
    load_movies,
    load_tags,
    predict_rating,
    train_model,
)
from app.utils import logger


def main() -> None:
    """Train models and show comparison."""
    import sys

    args = [a.lower() for a in sys.argv[1:]]
    do_save = "--save" in args or "-s" in args
    load_name = None
    for a in args:
        if a.startswith(("--load=", "-l=")):
            load_name = a.split("=", 1)[1]

    logger.info("=" * 55)
    logger.info("  MovieLens Rating Predictor — Improved ML Model")
    logger.info("=" * 55)

    if load_name:
        logger.info(f"\nLoading saved model '{load_name}'...")
        result = load_model(name=load_name)
    else:
        result = train_model(
            sample_size=500_000,
            use_tags=True,
            top_tags=100,
            use_tuning=True,
            save_path="v1" if do_save else None,
        )

    metrics = result["metrics"]
    imp = result["importance"]
    best_name = result["best_model_name"]

    logger.info(f"\n{'=' * 55}")
    logger.info(f"  >> Best Model: {best_name}")
    logger.info(f"{'=' * 55}")

    for model_name in ["RandomForest", "XGBoost"]:
        if model_name in metrics:
            m = metrics[model_name]
            logger.info(f"  {model_name}:")
            logger.info(f"    R^2:   {m['R2']:.4f}")
            logger.info(f"    RMSE: {m['RMSE']:.4f}")
            logger.info(f"    MAE:  {m['MAE']:.4f}")

    logger.info(f"\n  Training samples: {metrics['train_samples']:,}")
    logger.info(f"  Test samples:     {metrics['test_samples']:,}")
    logger.info(f"  Features:         {metrics['feature_count']:,}")

    logger.info(f"\n  Top 15 Features by Importance:\n  {'-' * 40}")
    for _, row in imp.head(15).iterrows():
        bar = "#" * int(row["importance"] * 200)
        logger.info(f"  {row['feature']:<35s} {row['importance']:.4f} {bar}")

    movies_example = load_movies()
    if "Toy Story (1995)" in movies_example["title"].values:
        toy_story = movies_example[movies_example["title"] == "Toy Story (1995)"].iloc[0]
        tag_pivot = load_tags(top_k=100)
        pred = predict_rating(
            toy_story,
            result["best_model"],
            result["scaler"],
            result["feature_cols"],
            result["num_cols"],
            tag_pivot=tag_pivot,
            rating_count=50.0,
        )
        logger.info(f"\n{'=' * 55}")
        logger.info("  Example: Toy Story (1995)")
        logger.info(f"  Predicted avg rating: {pred:.2f} / 5.0")
        logger.info(f"{'=' * 55}")

    logger.info("\n  Baseline (genre + year + count):     R^2 ~0.078")
    rf_r2 = metrics.get("RandomForest", {}).get("R2", 0)
    xgb_r2 = metrics.get("XGBoost", {}).get("R2", 0)
    best_r2 = max(rf_r2, xgb_r2)
    logger.info(f"  Improved (tags + tuning + more features): R^2 ~{best_r2:.4f}")
    if best_r2 > 0.08:
        logger.info(f"  Improvement: +{(best_r2 - 0.078) * 100:.1f}% explained variance")


if __name__ == "__main__":
    main()
