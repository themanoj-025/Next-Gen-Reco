# Architecture — Next-Gen-Reco

> Streamlit movie-recommendation application (MovieLens dataset) with a layered
> `app/` package, a thin Cloud bootstrap entry point, pre-trained model artifacts,
> and a real test suite.

---

## 1. System Overview

```
                     ┌────────────────────────────────────────────────┐
                     │  app.py (root)  — Streamlit bootstrap          │
                     │  Streamlit Cloud / Docker entry (RUN-only)     │
                     └──────────────────────┬─────────────────────────┘
                                            │ imports
                                            ▼
                     ┌────────────────────────────────────────────────┐
                     │  app/  (importable package — takes precedence  │
                     │         over app.py for `import app`)          │
                     │                                                │
                     │  app/ui/*.py      — 13 presentation modules    │
                     │  app/recommender.py — MovieRecommender         │
                     │  app/model.py     — load/train/predict         │
                     │  app/enrichment.py— NDEnrichment (extra data)  │
                     │  app/data/loader.py — user-data persistence    │
                     │  app/_paths.py    — canonical path config      │
                     └──────────┬──────────────────┬──────────────────┘
                                │                  │
                                ▼                  ▼
                        data/ (movies.csv,    models/ (joblib artifacts)
                        tags.csv, links.csv,
                        ND/ enrichment data)
```

## 2. Major Components

| Component | Location | Responsibility |
| --- | --- | --- |
| Entry bootstrap | `app.py` | Streamlit entry (`streamlit run app.py`). Inserts repo root on `sys.path`, imports `app.ui.*`, renders the app. **Run-only** — never imported as a module (the `app/` package wins name resolution). |
| Path config | `app/_paths.py` | Single source of truth: `PROJECT_ROOT`, `DATA_DIR`, `MODELS_DIR`, `CACHE_DIR`, `ND_DIR`. |
| Model layer | `app/model.py` | `load_movies`, `load_tags`, `load_model`, `predict_rating`, plus the training CLI (`main`) invoked via `python -m app.main --save`. |
| Recommender | `app/recommender.py` | `MovieRecommender` — orchestrates data + model for recommendations. |
| Enrichment | `app/enrichment.py` | `NDEnrichment` — merges the external ND dataset into the catalog. |
| Data persistence | `app/data/loader.py` | `_load_user_data` / `_save_user_data` (`.movie_user_data.json`, gitignored). |
| UI layer | `app/ui/*.py` | 13 modules: styles, poster_utils, session_utils, home, dashboard, explore, search, for_you, compare, stats, decade_explorer, movie_night, combo_finder, components. |
| Datasets | `data/` | `movies.csv`, `tags.csv`, `links.csv`, `ND/` (main_data.csv, movies.csv, reviews.txt). |
| Model artifacts | `models/v1_test/` | `meta.joblib` + `model.joblib` (committed; regenerable via `scripts/train_fast.py`). |
| Operational scripts | `scripts/` | `fix_regex.py` (data cleanup), `train_fast.py` (fast training). |
| Tests | `tests/` | `test_model.py`, `test_syntax.py` + fixture `test_pattern.txt`. |
| Infra | Dockerfile (multi-stage), compose (base/dev/prod), `setup.sh`, Makefile, `.github/workflows/ci.yml` | Build/run/CI (py_compile + import checks + pytest + Bandit + Docker/Trivy). |

## 3. Runtime Model

- **Single process**: one Streamlit server on :8501. No REST API, no workers.
- **State**: user watchlist/history persisted to `.movie_user_data.json` (gitignored,
  runtime file); Streamlit session state for ephemeral UI state.
- **Data loading**: catalog + tags + model artifacts load via `app._paths`-anchored
  paths; ND enrichment applied lazily.

## 4. Key Design Points

1. **`app.py` vs `app/`**: the root bootstrap exists for Streamlit Cloud (entry script
   must be a file, and it sys.path-inserts the repo root). Import resolution always
   favors the `app/` package, so `from app.ui... import ...` inside `app.py` hits the
   package — the collision is benign but documented here to prevent future confusion.
2. **Path centrality**: everything resolves through `app/_paths.py` — no scattered
   hardcoded relative paths.
3. **Train/recommend separation**: `app/model.py` owns artifact I/O + training;
   `app/recommender.py` owns the recommendation orchestration.
4. **Committed artifacts + regenerable pipeline**: `models/v1_test/*.joblib` are
   committed so the app runs offline; `scripts/train_fast.py` regenerates them.

## 5. Configuration

`.env.example` / `.env.template` document vars (e.g. TMDB API key used by
`app/ui/poster_utils.py` for poster URLs). `.env` is gitignored.

## 6. Deployment

- **Docker**: multi-stage build; prod + dev targets both `COPY app.py` + `app/`,
  `CMD ["streamlit", "run", "app.py", ...]`; healthcheck `/_stcore/health`.
- **Streamlit Cloud**: entry = `app.py`, `setup.sh` bootstraps deps.
- **CI** (`ci.yml`): py_compile sweep → core-module import checks
  (`app._paths`, `app.model`, `app.enrichment`, `app.recommender`) → UI-module AST
  import check → `pytest tests/` → Bandit → lychee → Docker build + Trivy.

See also: `docs/module_dependency.md`, `docs/startup_flow.md`, `docs/package_overview.md`,
`docs/migration/old_tree_to_new_tree.md`.
