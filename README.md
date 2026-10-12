<p align="center">
  <img src="https://img.shields.io/badge/NextGenReco-Movie%20Recommendations-red?style=for-the-badge" alt="NextGenReco Logo" />
</p>

<h1 align="center">NextGenReco</h1>

<p align="center">
  <strong>Intelligent movie recommendation and rating prediction platform with interactive analytics and REST API serving.</strong>
</p>

<p align="center">
  <a href="https://github.com/themanoj-025/Next-Gen-Reco/actions"><img src="https://img.shields.io/github/actions/workflow/status/themanoj-025/Next-Gen-Reco/ci.yml?style=flat-square&label=CI" alt="CI Status" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License MIT" /></a>
  <a href="https://github.com/themanoj-025/Next-Gen-Reco/stargazers"><img src="https://img.shields.io/github/stars/themanoj-025/Next-Gen-Reco?style=social" alt="GitHub Stars" /></a>
  <a href="https://github.com/themanoj-025/Next-Gen-Reco/issues"><img src="https://img.shields.io/github/issues/themanoj-025/Next-Gen-Reco?style=flat-square" alt="GitHub Issues" /></a>
  <a href="https://github.com/themanoj-025/Next-Gen-Reco/pulls"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square" alt="PRs Welcome" /></a>
</p>

---

## Overview

NextGenReco delivers personalized film recommendations and rating predictions powered by content-based similarity models across the MovieLens dataset. The platform combines semantic genre and tag embeddings to calculate movie affinities, provides transparent breakdowns of feature drivers behind predicted ratings, and generates curated movie marathon lineups.

It can be accessed via an interactive Streamlit dashboard or programmatically via a FastAPI inference server.

> [!NOTE]
> The recommendation engine runs completely offline with no cloud or external API requirements.

---

## Table of Contents

- [Key Features](#key-features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation & Quick Start](#installation--quick-start)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Testing](#testing)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Security](#security)
- [License](#license)
- [Support](#support)

---

## Key Features

- **Semantic Title Search**: Fast catalog search with instant predicted user ratings and genre metadata.
- **Content-Based Affinity Matching**: Vectorized cosine distance scoring computed across genre tags, release era, and global rating statistics.
- **Explainable Rating Forecasts**: Visual breakdown of positive and negative feature attributions influencing every predicted score.
- **Interactive Cinema Analytics**: Multi-tab exploratory dashboard featuring genre correlations, decade trends, and rating distribution comparisons.
- **Movie Night Curator**: Generates personalized theme-based movie marathon lineups based on input mood preferences.

---

## Architecture

```text
               User Query / Film Selection
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
    Streamlit Dashboard (app.py)    FastAPI Service (app/api_server.py)
             │                           │
             └─────────────┬─────────────┘
                           │
                           ▼
          Content-Based Recommendation Engine
            (app/model.py & recommender.py)
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
  Nearest-Neighbor Similarity    Rating Prediction Model
  (Genre & Tag Vector Space)    (Feature Attributions)
             │                           │
             └─────────────┬─────────────┘
                           │
                           ▼
             Ranked Output & Visual Insights
```

---

## Project Structure

```text
Next-Gen-Reco/
├── app/
│   ├── ui/                 # Reusable Streamlit dashboard components
│   ├── api_server.py       # FastAPI REST endpoints for predictions
│   ├── circuit_breaker.py  # Error circuit breaker pattern
│   ├── enrichment.py       # Metadata enhancement and data formatting
│   ├── health.py           # Health and readiness check routes
│   ├── model.py            # Feature transformation and ML pipeline
│   └── recommender.py      # Nearest-neighbor recommendation queries
├── data/                   # Seed catalog and cached vector models
├── tests/                  # Pytest unit and recommendation test suite
├── app.py                  # Main Streamlit application entry point
├── Dockerfile              # Multi-stage container build specification
├── docker-compose.yml      # Local development container orchestration
├── pyproject.toml          # Build backend and Ruff configuration
├── requirements.txt        # Runtime dependencies
└── README.md               # Project documentation
```

---

## Prerequisites

- **Python**: `>= 3.11`
- **Memory**: Minimum 2 GB RAM recommended for loading vectorized film catalog embeddings

---

## Installation & Quick Start

### 1. Clone & Setup Environment

```bash
# Clone the repository
git clone https://github.com/themanoj-025/Next-Gen-Reco.git
cd Next-Gen-Reco

# Create and activate virtual environment
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

### 3. Run the Application

**Run Streamlit Interactive Interface**:
```bash
streamlit run app.py
```
*Access the UI at http://localhost:8501.*

**Run FastAPI Service**:
```bash
uvicorn app.api_server:app --host 0.0.0.0 --port 8000 --reload
```
*Access Swagger documentation at http://localhost:8000/docs.*

---

## API Reference

The FastAPI service exposes the following endpoints:

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service health status |
| `POST` | `/api/v1/recommend` | Retrieve top similar movie recommendations |
| `POST` | `/api/v1/predict-rating`| Predict expected score for user/movie pair |

---

## Configuration

| Environment Variable | Default | Purpose |
| :--- | :--- | :--- |
| `NEXTGENRECO_DATA_DIR` | `data/` | Path to dataset and pickled embedding vectors |
| `NEXTGENRECO_CACHEDIR` | `.cache/` | Local directory for intermediate computation caches |

---

## Testing

```bash
# Execute pytest suite
pytest tests/ -v
```

---

## Roadmap

- [x] Content-based recommendation pipeline
- [x] Multi-tab interactive Streamlit dashboard
- [x] FastAPI REST serving endpoints
- [x] Movie night marathon generator
- [ ] Collaborative filtering neural hybrid model <!-- TODO: Track via GitHub issue -->
- [ ] Direct TMDB poster API enrichment integration <!-- TODO: Track via GitHub issue -->

---

## Contributing

Contributions are welcomed! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

---

## Security

Please report vulnerabilities following the instructions in [SECURITY.md](SECURITY.md).

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Support

- 🐛 **Issue Tracker**: [GitHub Issues](https://github.com/themanoj-025/Next-Gen-Reco/issues)
- 💡 **Discussions & Feedback**: [GitHub Pull Requests](https://github.com/themanoj-025/Next-Gen-Reco/pulls)
