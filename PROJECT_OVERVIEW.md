# MovieLens AI (Next-Gen-Reco)

> AI-powered movie rating predictions and content-based recommendations using the MovieLens 32M dataset with Streamlit UI.

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B.svg)](https://nextgenreco.streamlit.app)
[![Python 3.10](https://img.shields.io/badge/Python-3.10-3776AB.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Table of Contents

- [1. Executive Summary](#1-executive-summary)
- [2. Tech Stack & Core Technologies](#2-tech-stack--core-technologies)
- [3. High-Level Architecture](#3-high-level-architecture)
- [4. Complete Folder Structure Tree](#4-complete-folder-structure-tree)
- [5. Exhaustive File-by-File & Folder-by-Folder Breakdown](#5-exhaustive-file-by-file--folder-by-folder-breakdown)
- [6. Data Models & Schemas](#6-data-models--schemas)
- [7. API Surface](#7-api-surface)
- [8. Configuration & Environment Variables](#8-configuration--environment-variables)
- [9. Build, Run & Deployment Instructions](#9-build-run--deployment-instructions)
- [10. Data & Control Flow Walkthroughs](#10-data--control-flow-walkthroughs)
- [11. Dependency Graph Summary](#11-dependency-graph-summary)
- [12. Testing Strategy](#12-testing-strategy)
- [13. Known Issues, Technical Debt & Assumptions](#13-known-issues-technical-debt--assumptions)
- [14. Glossary](#14-glossary)
- [15. Appendix](#15-appendix)

---

## 1. Executive Summary

**MovieLens AI** is an AI-powered movie recommendation system that predicts ratings and suggests similar movies using the MovieLens 32M dataset (87K movies, 32M ratings, 2M user tags). It provides a polished Streamlit web app with search, recommendations, analytics, and a personalized dashboard.

**Target users**: Movie enthusiasts, data science learners, and anyone building recommendation systems.

**What problem it solves**: Finding movies you'll enjoy is hard with 87K+ options. MovieLens AI uses content-based filtering with genre matching (50%), tag matching (20%), year proximity (10%), and ML-predicted ratings (20%) to surface relevant recommendations.

**Why it exists**: To demonstrate a complete recommendation system pipeline from data processing to deployment, with a production-quality UI.

*Note: The hybrid similarity engine weights and ML model details are explicitly documented in the README.*

---

## 2. Tech Stack & Core Technologies

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Language | Python | 3.10+ | Primary language |
| Web UI | Streamlit | — | Interactive dashboard |
| ML | scikit-learn | — | Random Forest, XGBoost models |
| Data Processing | pandas | — | MovieLens data manipulation |
| Visualization | Plotly | — | Interactive charts |
| Similarity | Cosine/Jaccard | — | Genre and tag matching |
| Containerization | Docker | — | Multi-stage builds |

---

## 3. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Streamlit App (app.py)                            │
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │  Home    │  │  Search  │  │Dashboard │  │  Movie Detail    │   │
│  │  Page    │  │  Page    │  │  Page    │  │  + Recommendations│   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘   │
│       │              │              │                  │             │
│       └──────────────┼──────────────┼──────────────────┘             │
│                      │              │                                │
│                      ▼              ▼                                │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Recommendation Engine                      │   │
│  │                                                               │   │
│  │  Hybrid Similarity = 50% Genre + 20% Tags + 10% Year + 20% Rating │
│  │  ML Models: Random Forest + XGBoost (predict average rating)  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                      │                                              │
│                      ▼                                              │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              MovieLens 32M Dataset                            │   │
│  │  • 87K movies  • 32M ratings  • 2M user tags                 │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

**Architectural Pattern**: **Single-Page Streamlit App** with modular UI components. The recommendation engine is a self-contained module consumed by multiple UI pages.

---

## 4. Complete Folder Structure Tree

```
Next-Gen-Reco/
├── .devcontainer/
│   └── devcontainer.json
├── .dockerignore
├── .editorconfig
├── .gitattributes
├── .github/
│   ├── CODEOWNERS
│   ├── copilot-instructions.md
│   ├── dependabot.yml
│   ├── ISSUE_TEMPLATE/
│   ├── labeler.yml
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/
│       ├── ci.yml
│       ├── codeql.yml
│       ├── gitleaks.yml
│       ├── labeler.yml
│       ├── maintenance.yml
│       ├── stale.yml
│       └── welcome.yml
├── .gitignore
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.template
├── .vscode/
│   └── settings.json
├── AGENTS.md
├── app/
│   ├── __init__.py
│   ├── _paths.py
│   ├── data/
│   │   ├── __init__.py
│   │   └── loader.py
│   ├── enrichment.py
│   ├── main.py
│   ├── model.py
│   ├── recommender.py
│   └── ui/
│       ├── __init__.py
│       ├── combo_finder.py
│       ├── compare.py
│       ├── components.py
│       ├── dashboard.py
│       ├── decade_explorer.py
│       ├── explore.py
│       ├── for_you.py
│       ├── home.py
│       ├── movie_night.py
│       ├── poster_utils.py
│       ├── search.py
│       ├── session_utils.py
│       ├── stats.py
│       └── styles.py
├── app.py
├── data/
│   ├── links.csv
│   ├── movies.csv
│   ├── ND/
│   │   ├── main_data.csv
│   │   ├── movies.csv
│   │   └── reviews.txt
│   └── tags.csv
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── docker-compose.yml
├── Dockerfile
├── docs/
│   ├── community/
│   ├── design/
│   ├── product/
│   ├── project/
│   ├── reference/
│   └── technical/
├── LICENSE
├── Makefile
├── PROJECT_ANALYSIS.md
├── PROJECT_OVERVIEW.md
├── pyproject.toml
├── README.md
├── requirements.txt
├── runtime.txt
├── scripts/
│   ├── fix_regex.py
│   └── train_fast.py
├── setup.sh
└── tests/
    ├── __init__.py
    ├── test_model.py
    ├── test_pattern.txt
    └── test_syntax.py
```

---

## 5. Exhaustive File-by-File & Folder-by-Folder Breakdown

### Root Files

#### `Next-Gen-Reco/app.py`
- **Purpose**: Main Streamlit entry point. Routes to 10 page modules via sidebar navigation. Features IMDb-style top nav, dark/light theme toggle, and session state management.

#### `Next-Gen-Reco/app/recommender.py`
- **Purpose**: Core recommendation engine. Implements hybrid similarity scoring (genre 50%, tags 20%, year 10%, rating 20%) using cosine and Jaccard similarity.

#### `Next-Gen-Reco/app/model.py`
- **Purpose**: ML model for rating prediction. Uses Random Forest + XGBoost ensemble.

#### `Next-Gen-Reco/app/data/loader.py`
- **Purpose**: Loads and preprocesses MovieLens 32M dataset files.

### `Next-Gen-Reco/app/ui/` — UI Modules (10 pages)

| Module | Purpose |
|--------|---------|
| `home.py` | Landing page with featured movies |
| `search.py` | Instant movie search with predictions |
| `dashboard.py` | Personal ratings, watchlist, stats |
| `components.py` | Reusable UI components (movie cards, charts) |
| `compare.py` | Side-by-side movie comparison |
| `for_you.py` | Personalized recommendations |
| `decade_explorer.py` | Browse movies by decade |
| `combo_finder.py` | Find movie marathon combos |
| `movie_night.py` | Generate curated marathon lineups |
| `explore.py` | Surprise me + mood explorer |

### `Next-Gen-Reco/data/` — Dataset Files

| File | Content |
|------|---------|
| `movies.csv` | Movie titles and genres |
| `ratings.csv` | User ratings (32M) |
| `tags.csv` | User tags (2M) |
| `links.csv` | MovieLens ↔ IMDB/TMDB IDs |

---

## 6. Data Models & Schemas

### Movie Record

```json
{
  "movieId": "int — unique identifier",
  "title": "str — movie title with year",
  "genres": "str — pipe-separated genres",
  "avg_rating": "float — predicted average rating",
  "tag_vector": "sparse — TF-IDF tag features",
  "genre_vector": "sparse — one-hot genre features"
}
```

---

## 7. API Surface

No REST API — this is a Streamlit web application with direct user interaction.

---

## 8. Configuration & Environment Variables

| Variable | Purpose | Required |
|----------|---------|----------|
| `TMDB_API_KEY` | TMDB poster images | No (optional) |

---

## 9. Build, Run & Deployment Instructions

```bash
# Local
pip install -r requirements.txt
streamlit run app.py

# Docker
docker compose up -d
```

---

## 10. Data & Control Flow Walkthroughs

### Flow 1: Movie Search

1. User types movie name in search box
2. Fuzzy matching against 87K movie titles
3. Results display with predicted rating
4. Click movie → detail page with recommendations

### Flow 2: Get Recommendations

1. User clicks on a movie
2. `recommender.py` computes hybrid similarity scores
3. Top 12 similar movies returned
4. Displayed with radar charts, feature explanations

---

## 11. Dependency Graph Summary

```
app.py → app/ui/* → app/recommender.py → app/model.py → app/data/loader.py
```

---

## 12. Testing Strategy

- **Framework**: pytest
- **Files**: `test_model.py`, `test_syntax.py`
- **Coverage**: Basic model and syntax tests

---

## 13. Known Issues, Technical Debt & Assumptions

### Known Issues

1. **Large dataset**: MovieLens 32M requires significant memory.
2. **No API layer**: All logic is in the Streamlit process.

### Assumptions

1. **Pre-downloaded data**: Dataset files must be in `data/` directory.
2. **GPU optional**: Training works on CPU.

---

## 14. Glossary

| Term | Definition |
|------|-----------|
| **Cosine Similarity** | Measures angle between feature vectors |
| **Jaccard Similarity** | Measures overlap between tag sets |
| **TF-IDF** | Term Frequency-Inverse Document Frequency for tag weighting |
| **Content-Based** | Recommendations based on item features, not user behavior |

---

## 15. Appendix

### Dataset Citation

> F. Maxwell Harper and Joseph A. Konstan. 2015. The MovieLens Datasets: History and Context. ACM TiiS 5(4):19:1–19:19.

---

*This document was generated as part of a comprehensive project documentation effort. Last updated: August 8, 2026.*
