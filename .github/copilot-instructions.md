# Next-Gen-Reco — Copilot Instructions

## Code conventions
- Python with 4-space indentation
- Streamlit for UI, scikit-learn for ML (RandomForest)
- App modules in `app/`, UI components in `app/ui/`
- Path resolution via `app/_paths.py` (anchored to file location)

## Key commands
- Launch: `streamlit run app.py`
- Tests: `pytest tests/ -v`
- Train model: `python scripts/train_fast.py`

## Architecture
- `app/model.py` — data loading + model inference
- `app/recommender.py` — MovieRecommender class
- `app/enrichment.py` — NDEnrichment data augmentation
- `app/ui/` — Streamlit page components
- Data in `data/`, models in `models/v1_test/`
