"""
Fast model training - saves to models/v1_test/ (where the recommender expects it)
"""

import os
import sys
import warnings

warnings.filterwarnings("ignore")

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.model import train_model

logger.info("=" * 55)
logger.info("  MovieLens - Training Fast Model (no tuning)")
logger.info("=" * 55)

result = train_model(
    sample_size=500_000,
    use_tags=True,
    top_tags=100,
    use_tuning=False,
    save_path="v1_test",  # Save directly to models/v1_test/
)

# Print summary
metrics = result["metrics"]
logger.info(f"\n{'=' * 55}")
logger.info(f"  >> Best Model: {result['best_model_name']}")
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
logger.info("\n[OK] Model saved to models/v1_test/")
