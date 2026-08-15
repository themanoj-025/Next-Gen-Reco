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

> 📸 **Screenshot placeholder:** Add a screenshot of the recommendations page showing similar movies.

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
