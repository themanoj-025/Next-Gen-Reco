# Module Dependency — Next-Gen-Reco

The graph is **acyclic**: UI → recommender/enrichment → model/data → `_paths`. No
circular imports.

## 1. Dependency Graph

```
  app.py (bootstrap, RUN-only)
       │
       ▼
  app/ui/*.py ──────────────► app/recommender.py ──► app/model.py ──► app/_paths.py
       │                            │                      │
       │                            └──► app/enrichment.py ─┤
       ▼                                 │                  ▼
  app/ui/session_utils.py ──► app/data/loader.py    data/ + models/ (artifacts)
```

## 2. Dependency Matrix

| Module | Imports | Depends on | Consumed by |
| --- | --- | --- | --- |
| `app.py` | `app.ui.*` | streamlit | `streamlit run app.py` (Docker, Cloud) |
| `app/ui/*.py` (13 modules) | `app.ui.poster_utils`, `app.ui.components`, `app.ui.session_utils`, `app.recommender`, `app.data.loader` | streamlit, pandas, plotly | `app.py`, each other |
| `app/ui/poster_utils.py` | `app.ui.session_utils` | requests/urllib (TMDB) | all UI modules (leaf-ish) |
| `app/ui/session_utils.py` | `app.data.loader`, `app.recommender` | streamlit | `app.py`, UI modules |
| `app/recommender.py` | `app._paths`, `app.model`, `app.enrichment` | pandas, numpy, sklearn | UI modules |
| `app/model.py` | `app._paths` | pandas, numpy, sklearn, joblib | `app/recommender.py`, `python -m app.main` |
| `app/enrichment.py` | `app._paths` | pandas | `app/recommender.py` |
| `app/data/loader.py` | `app._paths` | json | `app/ui/components.py`, `dashboard.py`, `search.py`, `session_utils.py` |
| `app/main.py` | `app.model` | — | `python -m app.main --save` (CLI) |
| `app/_paths.py` | — (leaf constants) | — | everything |
| `scripts/fix_regex.py` | — | pandas | manual/ops |
| `scripts/train_fast.py` | `app.model` | pandas, sklearn, joblib | manual (regenerates models/) |
| `tests/test_model.py` | `app.model`, `app._paths` | pytest | CI |
| `tests/test_syntax.py` | compileall/ast | pytest | CI |

## 3. Why This Shape

- **Package-first imports**: `app/__init__.py` makes `from app.x import ...` stable;
  the root `app.py` is only ever executed (Streamlit requires an entry script), so
  there is no ambiguity at import time.
- **Single path source**: every module reads `app._paths` — relocations are cheap and
  path drift is impossible.
- **Leaf-first layering**: `_paths.py` at the bottom; UI modules at the top; nothing
  imports upward.

## 4. Change Warnings

- **Renaming `app/_paths.py`** breaks every module — grep `from app._paths` first.
- **Adding a new page/UI module** needs no registration (imported directly by `app.py`).
- **`app.py` must remain at root** — Dockerfile `COPY app.py` + CMD and Streamlit Cloud
  entry config reference it by name.
- Regenerating `models/v1_test/*.joblib` (via `scripts/train_fast.py`) changes
  committed binaries — do it in a dedicated commit.
