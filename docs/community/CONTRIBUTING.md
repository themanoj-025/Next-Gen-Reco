# Contributing to Next-Gen-Reco

Thank you for your interest in contributing to Next-Gen-Reco, the movie recommendation engine!

## Getting Started

### Prerequisites
- Python 3.x
- pip

### Setup
1. Fork and clone the repository.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. (Optional) Set up TMDB API key for movie posters:
   ```bash
   cp .streamlit/secrets.toml.template .streamlit/secrets.toml
   # Edit .streamlit/secrets.toml and add your TMDB_API_KEY
   ```

### Running the Application
```bash
streamlit run app/main.py
```
Or using the legacy entry point:
```bash
streamlit run app.py
```

### Retraining the Model
```bash
python scripts/train_fast.py
```

### Secrets
| Variable | Source | Description |
| --- | --- | --- |
| `TMDB_API_KEY` | `.streamlit/secrets.toml` | API key for movie posters (optional) |

## Code Style

- Follow PEP 8 conventions.
- Use 4-space indentation.
- Add docstrings to all public functions and classes.
- Use pathlib for file path resolution (see `app/_paths.py`).

## Project Architecture

- **`app/main.py`** — Streamlit UI entry point
- **`app/model.py`** — Model loading, training, and feature engineering
- **`app/recommender.py`** — Recommendation engine (content + collaborative)
- **`app/_paths.py`** — Centralized path resolution (DATA_DIR, MODELS_DIR, CACHE_DIR)
- **`data/`** — MovieLens dataset CSVs (movies.csv, links.csv, tags.csv)
- **`models/`** — Trained model artifacts (joblib files)
- **`scripts/`** — Training and utility scripts

### Path Resolution
Always use `app/_paths.py` for resolving file paths:
```python
from app._paths import DATA_DIR, MODELS_DIR
data_path = DATA_DIR / "movies.csv"
model_path = MODELS_DIR / "v1_test" / "model.joblib"
```
This ensures consistent behavior across local development and Streamlit Cloud.

## Running Tests

```bash
pytest
```

Test files are in `tests/`. The primary test module is `test_model.py`.

## Submitting Changes

1. Create a feature branch:
   ```bash
   git checkout -b feat/my-feature
   ```
2. Make focused, minimal changes.
3. Run tests to verify nothing is broken.
4. If modifying the recommendation algorithm, verify against known test cases.
5. Commit with a descriptive message:
   - Format: `type(scope): description`
   - Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`
   - Example: `feat(model): add user-based collaborative filtering`
   - Example: `fix(ui): correct movie search with special characters`
6. Push and open a Pull Request.

## Reporting Issues

Include in your report:
- Steps to reproduce
- Error messages and stack traces
- Whether the model is trained (`models/v1_test/model.joblib` exists)
- Streamlit version

## Model Development Notes

- The hybrid model combines TF-IDF content-based similarity with SVD collaborative filtering.
- Feature engineering is done in `app/model.py` using scikit-learn pipelines.
- Models are serialized with joblib and stored in versioned directories under `models/`.
- When retraining, save new models to a new version directory (e.g., `models/v2_test/`).

## TMDB Integration

Movie posters are optional. To enable:
1. Get a free API key from [themoviedb.org](https://www.themoviedb.org/settings/api).
2. Copy `.streamlit/secrets.toml.template` to `.streamlit/secrets.toml`.
3. Add your key: `TMDB_API_KEY = "your_key_here"`.
4. The app will automatically use posters when available.

## Code of Conduct

This project and everyone participating in it is governed by the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.
