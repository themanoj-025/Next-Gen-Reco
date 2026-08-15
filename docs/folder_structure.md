# Folder Structure — Next-Gen-Reco

Annotated tree of the **current (post-restructure)** layout, one-line purpose per entry.

```
Next-Gen-Reco/
├── .devcontainer/                 # Dev container definition
├── .github/
│   ├── CODEOWNERS / dependabot.yml / labeler.yml / ISSUE_TEMPLATE/
│   ├── copilot-instructions.md / PULL_REQUEST_TEMPLATE.md
│   └── workflows/                 # ci.yml, codeql, gitleaks, labeler, maintenance, stale, welcome
├── .gitignore / .dockerignore / .editorconfig / .gitattributes
├── .streamlit/                    # Streamlit config (dark theme)
├── .vscode/settings.json
├── AGENTS.md · LICENSE · README.md · PROJECT_ANALYSIS.md · PROJECT_OVERVIEW.md
├── app.py                         # Streamlit entry bootstrap (Cloud/Docker contract; RUN-only)
├── app/                           # Importable application package (takes precedence over app.py)
│   ├── __init__.py
│   ├── _paths.py                  # Canonical path config (single source of truth)
│   ├── main.py                    # Training CLI: python -m app.main --save
│   ├── model.py                   # load_movies/tags/model, predict_rating, training
│   ├── recommender.py             # MovieRecommender orchestration
│   ├── enrichment.py              # NDEnrichment (external catalog enrichment)
│   ├── data/
│   │   ├── __init__.py
│   │   └── loader.py              # user-data persistence (.movie_user_data.json)
│   └── ui/                        # 13 Streamlit UI modules (styles, poster_utils, session_utils,
│       │                          #   home, dashboard, explore, search, for_you, compare, stats,
│       │                          #   decade_explorer, movie_night, combo_finder, components)
├── data/                          # Datasets
│   ├── movies.csv · tags.csv · links.csv
│   └── ND/                        # Enrichment data (main_data.csv, movies.csv, reviews.txt)
├── models/
│   └── v1_test/                   # Committed artifacts: meta.joblib + model.joblib
├── docs/
│   ├── architecture.md · folder_structure.md · module_dependency.md
│   ├── startup_flow.md · package_overview.md
│   ├── migration/                 # migration_summary, old_tree_to_new_tree, file_move_ledger
│   ├── community/ design/ product/ project/ reference/ technical/
├── scripts/
│   ├── fix_regex.py               # Data cleanup utility
│   └── train_fast.py              # Fast model training (regenerates models/)
├── setup.sh                       # Streamlit Cloud bootstrap
├── tests/
│   ├── __init__.py
│   ├── test_model.py · test_syntax.py
│   └── test_pattern.txt           # Test fixture
├── Dockerfile                     # Multi-stage (prod/dev)
├── docker-compose.yml / .dev.yml / .prod.yml
├── Makefile                       # compose ergonomics + test/lint targets
├── pyproject.toml · requirements.txt · runtime.txt
└── .env.example · .env.template   # Env templates (see ledger — duplication flagged)
```

## Top-level folder purposes

| Path | Purpose |
| --- | --- |
| `app/` | All application logic — model, recommender, enrichment, data loader, UI. |
| `app.py` | Thin Streamlit-Cloud/Docker entry bootstrap (root, by contract). |
| `scripts/` | Operational/development Python utilities. |
| `tests/` | Pytest suite + fixtures. |
| `data/` | Datasets (catalog, tags, links, ND enrichment). |
| `models/` | Committed model artifacts. |
| `docs/` | Documentation suite. |
| `.github/` | CI/CD + community health. |
| Root files | Canonical metadata + runtime infra. |
