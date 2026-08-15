# Changelog

All notable changes to **Next-Gen-Reco** are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] — 2026-06-01

### Added

#### Recommendation Engine
- Hybrid similarity engine combining genre match (50%), tag match (20%), year proximity (10%), and rating boost (20%)
- Content-based recommendations using TF-IDF on movie metadata
- Collaborative filtering via SVD
- Random Forest + XGBoost model for rating prediction

#### Streamlit Application
- **Movie Search** — Type any movie name for instant results with predicted ratings
- **Similar Movies** — Content-based recommendations using genre vectors, tags, year proximity, and rating scores
- **Prediction Breakdown** — Feature-level explanation of rating predictions (genres, tags, year, etc.)
- **Analysis** — Interactive charts: genre distribution, rating comparison, similarity breakdown
- **Top Picks** — Highest-rated movies filtered by genre
- **User Dashboard** — Track ratings, watchlist, and personal stats
- **Decade Explorer** — Browse movies by decade with genre trends
- **Movie Night** — Curated marathon lineup generator

#### Data Pipeline
- MovieLens 32M dataset integration (87K movies, 32M ratings, 2M tags)
- TMDB API integration for movie poster images (optional)
- Centralized path resolution via `app/_paths.py`
- Versioned model storage under `models/v*_test/`

#### Training Pipeline
- Script-based model training (`scripts/train_fast.py`)
- Feature engineering with scikit-learn pipelines
- Model serialization with joblib
- Versioned model directories

#### Deployment
- Streamlit Community Cloud ready
- Pre-configured for ~154 MB disk footprint
- CI workflow with syntax and import validation

---

## [0.1.0] — Initial Development

### Added
- Project scaffolding and module structure
- MovieLens dataset loading
- Basic recommendation algorithm
- Streamlit app entry point
