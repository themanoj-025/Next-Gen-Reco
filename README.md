# 🎬 NextGenReco

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

## 📋 Table of Contents

- [What it does](#what-it-does)
- [🚀 Live demo](#-live-demo)
- [✨ Features](#-features)
- [🧠 How it works](#-how-it-works)
- [🏗️ Architecture](#️-architecture)
- [🚀 Quick start](#-quick-start)
- [📁 Project structure](#-project-structure)
- [📊 Dataset](#-dataset)
- [🗺️ Roadmap](#️-roadmap)
- [🤝 Contributing](#-contributing)
- [📬 Support](#-support)
- [License](#license)

---

## What it does

NextGenReco finds your favorite movies using content-based AI: given a movie (or a free-text query), it searches the catalog with predicted ratings, recommends similar films by genre/tags/ratings, breaks down which features drove each prediction, and lets you explore trends by decade, genre, and rating.

> [!NOTE] The engine is content-based and runs entirely locally — no cloud or API keys are needed. The live demo is hosted on Streamlit Cloud.

## 🚀 Live demo

**Try it now:** [nextgenreco.streamlit.app](https://nextgenreco.streamlit.app)

## ✨ Features

| Feature | Description |
| --- | --- |
| 🔍 **Smart search** | Instant movie lookup with predicted ratings |
| 🎯 **Similar movies** | Content-based recommendations using genres, tags, and ratings |
| 📊 **Prediction breakdown** | See which features drove each prediction |
| 📈 **Analysis charts** | Interactive genre distribution, rating comparisons, and decade trends |
| 🏆 **Top picks** | Browse highest-rated movies by genre |
| 📋 **Personal dashboard** | Track your ratings, watchlist, and stats |
| 📅 **Decade explorer** | Browse movies by decade with genre trends |
| 🎬 **Movie Night** | Generate curated marathon lineups |

## 🧠 How it works

```text
NEXTGENRECO/
├── app/
│   ├── models.py           # Content-based recommender + ratings predictor
│   ├── recommender.py      # Movie search + similar-movies logic
│   ├── dashboard.py        # Streamlit app (8 pages)
│   └── data/               # Loaded dataset + embeddings
├── notebooks/              # Exploration + model cards
├── requirements.txt
└── README.md
```

The recommender builds a genre/tag/rating vector per movie, computes similarity against a catalog of 87K movies, and returns top-N neighbors plus a SHAP breakdown of the predicted rating.

## 🏗️ Architecture

```text
NEXTGENRECO/
├── app/
│   ├── models.py           # ML models + prediction
│   ├── recommender.py      # Search + neighbor search
│   └── dashboard.py        # Streamlit UI
├── data/                   # Dataset + metadata
├── notebooks/              # Exploration + model cards
├── tests/                  # pytest suite
├── requirements.txt
└── README.md
```

## 🚀 Quick start

### Prerequisites

- Python 3.11 or newer
- A machine with enough RAM to load the full 87K-movie catalog (the `bench` tier streams the catalog in chunks if your RAM is limited)

### Install & run

```bash
# 1. Clone the repository
git clone https://github.com/themanoj-025/Next-Gen-Reco.git
cd Next-Gen-Reco

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download the dataset (or let the app auto-seed it)
#    The catalog is ~87K movies; run once and cache the embeddings.
python -m app.data.download --out data/

# 5. Run the app
streamlit run app/dashboard.py
```

### Environment variables

| Variable | Default | Required | Description |
| --- | --- | --- | --- |
| `NEXTGENRECO_DATA_DIR` | `data/` | No | Directory for the cached catalog |
| `NEXTGENRECO_CACHEDIR` | `.cache/` | No | Local cache for intermediate embeddings |

## 📁 Project structure

```
Next-Gen-Reco/
├── app/
│   ├── models.py           # ML models + prediction
│   ├── recommender.py      # Search + neighbor search
│   └── dashboard.py        # Streamlit UI
├── data/                   # Dataset + metadata
├── notebooks/              # Exploration + model cards
├── tests/                  # pytest suite
├── requirements.txt
└── README.md
```

## 📊 Dataset

| Item | Value |
| --- | --- |
| Movies | 87,000+ |
| Ratings | 32,000,000+ |
| User tags | 2,000,000+ |
| Format | Pickled per-movie vectors + a metadata DataFrame |

> [!IMPORTANT] The dataset metrics above are the project's reported figures and should be re-verified on re-run. If the benchmark numbers change, the README's claims must match the `README`'s own `data/` snapshot, not a re-run on new data.

## 🗺️ Roadmap

> [!CAUTION] Checked items are built and verified. Unchecked items are tracked in the issue tracker.

- [x] Movie search with predicted ratings
- [x] Similar-movie recommendations
- [x] Prediction breakdown (feature contributions)
- [x] Analysis charts (genre, rating, decade)
- [x] Top-picks by genre
- [x] Personal dashboard (ratings, watchlist, stats)
- [x] Decade explorer
- [x] Movie Night lineup generator
- [ ] Collaborative filtering (tracked public issue)

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md).

## 📬 Support

- 🐛 [Report a bug](https://github.com/themanoj-025/Next-Gen-Reco/issues)
- 💡 [Request a feature](https://github.com/themanoj-025/Next-Gen-Reco/issues)
- 📧 Email the maintainer via the issue tracker

## License

MIT License — see [LICENSE](LICENSE).
