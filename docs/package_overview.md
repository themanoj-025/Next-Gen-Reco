# Package Overview — Next-Gen-Reco

Inventory of every module (post-restructure).

## 1. Application Package (`app/`)

| Module | Responsibility | Entry point |
| --- | --- | --- |
| `app/_paths.py` | Canonical path constants (`PROJECT_ROOT`, `DATA_DIR`, `MODELS_DIR`, `CACHE_DIR`, `ND_DIR`). | — (leaf) |
| `app/main.py` | Training CLI wrapper (`python -m app.main --save`). | `python -m app.main` |
| `app/model.py` | `load_movies`, `load_tags`, `load_model`, `predict_rating`, training `main()`. | — (library) |
| `app/recommender.py` | `MovieRecommender` — recommendation orchestration over data + model. | — (library) |
| `app/enrichment.py` | `NDEnrichment` — merge external ND dataset. | — (library) |
| `app/data/loader.py` | `_load_user_data` / `_save_user_data` (`.movie_user_data.json`). | — (library) |
| `app/ui/` | 13 presentation modules: `styles.py`, `poster_utils.py`, `session_utils.py`, `home.py`, `dashboard.py`, `explore.py`, `search.py`, `for_you.py`, `compare.py`, `stats.py`, `decade_explorer.py`, `movie_night.py`, `combo_finder.py`, `components.py`. | imported by `app.py` |

## 2. Entry Point (root)

| Module | Responsibility | Entry point |
| --- | --- | --- |
| `app.py` | Streamlit bootstrap: sys.path insert + UI render. | `streamlit run app.py` (Docker CMD, Streamlit Cloud) |

## 3. Scripts (`scripts/`)

| Module | Responsibility | Entry point |
| --- | --- | --- |
| `scripts/fix_regex.py` | Data cleanup utility. | `python scripts/fix_regex.py` |
| `scripts/train_fast.py` | Fast training — regenerates `models/v1_test/*.joblib`. | `python scripts/train_fast.py` |

## 4. Tests (`tests/`)

| Module | Responsibility |
| --- | --- |
| `tests/test_model.py` | Unit tests over `app.model` / paths. |
| `tests/test_syntax.py` | Syntax/compile checks. |
| `tests/test_pattern.txt` | Fixture for regex/pattern tests. |

## 5. Data & Artifacts

| Path | Responsibility |
| --- | --- |
| `data/movies.csv` · `data/tags.csv` · `data/links.csv` | MovieLens catalog + tags + links. |
| `data/ND/` | External enrichment dataset (`main_data.csv`, `movies.csv`, `reviews.txt`). |
| `models/v1_test/meta.joblib` + `model.joblib` | Committed trained artifacts. |

## 6. Infrastructure

`Dockerfile` (multi-stage), `docker-compose.yml`/`.dev.yml`/`.prod.yml`, `setup.sh`,
`Makefile`, `.github/workflows/ci.yml` (py_compile → import checks → pytest → Bandit →
lychee → Docker+Trivy), `.devcontainer/`.

## 7. Documentation (`docs/`)

Root suite: `architecture.md`, `folder_structure.md`, `module_dependency.md`,
`startup_flow.md`, `package_overview.md`. Migration records: `migration/`
(`migration_summary.md` ← v5.0, `old_tree_to_new_tree.md`, `file_move_ledger.md`).
Categorized: `community/`, `design/`, `product/`, `project/`, `reference/`,
`technical/`.

## 8. Test Coverage

`pytest tests/` (test_model + test_syntax) runs in CI and via `make test`.
