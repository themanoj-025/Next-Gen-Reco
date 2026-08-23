<p align="center">
  <img src="https://img.shields.io/badge/NextGenReco-Movie%20Recommendations-red?style=for-the-badge" alt="NextGenReco Logo" />
</p>

<h1 align="center">🎬 NextGenReco</h1>

<p align="center">
  <strong>AI-Powered Movie Recommendations & Rating Predictions</strong>
</p>

<p align="center">
  <a href="https://nextgenreco.streamlit.app"><img src="https://img.shields.io/badge/Live%20Demo-Try%20It%20Now-brightgreen?style=flat-square" alt="Live Demo" /></a>
  <a href="https://github.com/themanoj-025/Next-Gen-Reco/actions"><img src="https://img.shields.io/github/actions/workflow/status/themanoj-025/Next-Gen-Reco/ci.yml?style=flat-square&label=CI" alt="CI Status" /></a>
  <a href="https://github.com/themanoj-025/Next-Gen-Reco/blob/main/LICENSE"><img src="https://img.shields.io/github/license/themanoj-025/Next-Gen-Reco?style=flat-square" alt="License" /></a>
  <a href="https://github.com/themanoj-025/Next-Gen-Reco/stargazers"><img src="https://img.shields.io/github/stars/themanoj-025/Next-Gen-Reco?style=social" alt="Stars" /></a>
</p>

---

<p align="center">
  <strong>Discover movies you'll love, powered by AI.</strong>
  <br />
  87K movies, 32M ratings, 2M user tags — all analyzed to find your perfect match.
</p>

---

## 📋 Table of Contents

- [🚀 Live Demo](#-live-demo)
- [✨ Features](#-features)
- [🧠 How It Works](#-how-it-works)
- [🏗️ Architecture](#️-architecture)
- [🚀 Quick Start](#-quick-start)
- [📁 Project Structure](#-project-structure)
- [📊 Dataset](#-dataset)
- [🗺️ Roadmap](#️-roadmap)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)
- [🙏 Acknowledgements](#-acknowledgements)

---

## 📸 Screenshots

> _To add screenshots: run `streamlit run app.py` or visit the [live demo](https://nextgenreco.streamlit.app), capture your screen, save images to `docs/assets/`, and reference them below._
>
> **Suggested screenshots:**
> - Recommendations page showing similar movies
> - Search with predicted ratings
> - Prediction breakdown with feature contributions
> - Movie Night marathon lineup generator

---

## 🚀 Live Demo

**Try it now:** [nextgenreco.streamlit.app](https://nextgenreco.streamlit.app)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Smart Search** | Instant movie lookup with predicted ratings |
| 🎯 **Similar Movies** | Content-based recommendations using genres, tags, and ratings |
| 📊 **Prediction Breakdown** | See which features drove each prediction |
| 📈 **Analysis Charts** | Interactive genre distribution, rating comparisons |
| 🏆 **Top Picks** | Browse highest-rated movies by genre |
| 📋 **Personal Dashboard** | Track your ratings, watchlist, and stats |
| 📅 **Decade Explorer** | Browse movies by decade with genre trends |
| 🎬 **Movie Night** | Generate curated marathon lineups |

---

## 🧠 How It Works

The system uses a hybrid similarity engine trained on 87K movies, 32M ratings, and 2M user tags:

| Component | Weight | Method |
|-----------|--------|--------|
| 🎭 Genre Match | 50% | Cosine similarity on genre vectors |
| 🏷️ Tag Match | 20% | Jaccard similarity on user tags |
| 📅 Year Proximity | 10% | Gaussian decay by release year |
| ⭐ Rating Boost | 20% | Predicted rating from RF/XGBoost model |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Streamlit Dashboard                           │
│  Search │ Recommendations │ Analysis │ Dashboard │ Explorer     │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              Recommendation Engine                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Content-Based│  │  ML Model    │  │  Hybrid      │          │
│  │  Similarity  │  │  (RF/XGBoost)│  │  Scoring     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                 MovieLens 32M Dataset                           │
│  87K Movies │ 32M Ratings │ 2M User Tags                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+

### Installation

```bash
# Clone the repository
git clone https://github.com/themanoj-025/Next-Gen-Reco.git
cd Next-Gen-Reco

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

---

## 📁 Project Structure

```
Next-Gen-Reco/
├── app.py                    # Streamlit app entry point
├── recommender.py            # Recommendation engine
├── requirements.txt          # Python dependencies
├── models/v1_test/           # Trained model artifacts
├── data/                     # MovieLens data files
├── scripts/                  # Training and utility scripts
├── tests/                    # Test files
└── docs/                     # Documentation
```

---

## 📊 Dataset

Uses the [MovieLens 32M Dataset](https://grouplens.org/datasets/movielens/32m/) by GroupLens Research.

> F. Maxwell Harper and Joseph A. Konstan. 2015. The MovieLens Datasets: History and Context. ACM Transactions on Interactive Intelligent Systems (TiiS) 5, 4: 19:1–19:19. https://doi.org/10.1145/2827872

---

## 🗺️ Roadmap

- [x] Content-based recommendations
- [x] ML rating predictions
- [x] Interactive dashboard
- [x] Search functionality
- [x] Movie night generator
- [ ] Collaborative filtering
- [ ] User authentication
- [ ] Watchlist sync
- [ ] Mobile optimization

---

## 🔌 REST API

The FastAPI server (`app/api_server.py`) exposes search, recommendation, and stats endpoints:

### Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/health` | Health check | No |
| GET | `/api/v1/movies/search?q=...&limit=20` | Search movies by title | Optional |
| GET | `/api/v1/movies/{id}` | Get movie details by ID | Optional |
| GET | `/api/v1/recommendations/{id}?n=10` | Get similar movie recommendations | Optional |
| GET | `/api/v1/stats` | Dataset statistics (movie count, year range) | Optional |

### Authentication

Set `NEXT_GEN_RECO_API_KEY` env var to enable Bearer token auth:

```bash
# Enable auth
export NEXT_GEN_RECO_API_KEY=your-secret-key-here

# Request with auth
curl -H "Authorization: Bearer your-secret-key-here" http://localhost:8000/api/v1/stats
```

### Rate Limiting

All endpoints are rate-limited to **60 requests per minute** per IP (via slowapi).

### Running the API Server

```bash
# Install dependencies
pip install -r requirements.txt

# Start the API server
uvicorn app.api_server:app --host 0.0.0.0 --port 8000
```

---

## 🔧 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_GEN_RECO_API_KEY` | (empty) | API key for Bearer token auth |
| `TMDB_API_KEY` | (empty) | TMDB API key for movie posters (optional) |

---

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_recommender.py -v
```

**Test coverage:** 313+ tests across 20 test files covering recommendation engine, data loading, UI components, and API endpoints.

---

## 🚀 Deployment

### Streamlit Cloud

1. Push to GitHub
2. Connect to [Streamlit Cloud](https://share.streamlit.io/)
3. Set `requirements.txt` as dependency
4. Deploy!

### Docker

```bash
docker-compose up -d
```

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md).

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

- [MovieLens](https://grouplens.org/datasets/movielens/) - Dataset
- [Streamlit](https://streamlit.io/) - Dashboard framework
- [scikit-learn](https://scikit-learn.org/) - ML framework
- [XGBoost](https://xgboost.readthedocs.io/) - Gradient boosting

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/themanoj-025">themanoj-025</a>
</p>

<p align="center">
  If you find this project useful, please give it a ⭐ star!
</p>
---

## ⭐ Star History

[![Last Commit](https://img.shields.io/github/last-commit/themanoj-025/Next-Gen-Reco?style=flat-square)](https://github.com/themanoj-025/Next-Gen-Reco)
[![Contributors](https://img.shields.io/github/contributors/themanoj-025/Next-Gen-Reco?style=flat-square)](https://github.com/themanoj-025/Next-Gen-Reco/graphs/contributors)

[![Star History Chart](https://api.star-history.com/svg?repos=themanoj-025/Next-Gen-Reco&type=Date)](https://star-history.com/#Next-Gen-Reco&Date)
