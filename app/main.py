"""
MovieLens AI - Model Training CLI
==================================
Use this module to train the ML model:
    python -m app.main --save

For the Streamlit app, run:
    streamlit run app.py
"""

import logging
import warnings

warnings.filterwarnings("ignore")

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

from app.model import main as train_model_cli

if __name__ == "__main__":
    train_model_cli()
