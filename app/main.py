"""
MovieLens AI - Model Training CLI
==================================
Use this module to train the ML model:
    python -m app.main --save

For the Streamlit app, run:
    streamlit run app.py
"""

import warnings

warnings.filterwarnings("ignore")

from app.model import main as train_model_cli

if __name__ == "__main__":
    train_model_cli()
