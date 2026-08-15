# Startup Flow — Next-Gen-Reco

## 1. App Boot (Streamlit)

```
streamlit run app.py            # local / Docker CMD / Streamlit Cloud entry
│
├─ 1. app.py inserts repo root into sys.path
├─ 2. Imports app.ui.styles (CSS), app.ui.poster_utils, app.ui.session_utils
├─ 3. init_session() — session state defaults
├─ 4. app.ui modules render the UI (home, dashboard, explore, search, ...)
└─ 5. Ready on :8501 (healthcheck curl /_stcore/health)
```

Data/artifacts are loaded lazily and cached through `app.recommender.MovieRecommender`
(which reads `data/` + `models/v1_test/` via `app._paths`).

## 2. Training Flow

```
python -m app.main --save        # CLI (app/main.py → app/model.main)
│
├─ 1. Load catalog + tags from data/ (via _paths)
├─ 2. Train model
└─ 3. Save meta.joblib + model.joblib to models/v1_test/
```

Fast variant: `python scripts/train_fast.py` (same artifact contract).

## 3. Docker Boot

- **prod target**: deps installed → `COPY app.py` + `COPY app/` + `COPY data/ models/
  scripts/ tests/` → `CMD ["streamlit", "run", "app.py", ...]` as non-root user;
  healthcheck `/_stcore/health`.
- **dev target**: same + `--server.fileWatcherType=polling --server.runOnSave=true`
  with bind mounts (`docker-compose.dev.yml`).
- **Makefile**: `up/down/build/test/lint/health/config/reset`.

## 4. CI (push/PR)

`ci.yml`: py_compile sweep over all `.py` → core import checks
(`app._paths`, `app.model`, `app.enrichment`, `app.recommender`) → UI-module AST
import check (no Streamlit runtime needed) → `pytest tests/` → Bandit → lychee →
Docker build + Trivy.

## 5. Environment

`.env.example` / `.env.template` list config (e.g. `TMDB_API_KEY` for poster URLs).
`.env` is gitignored. `.movie_user_data.json` is a gitignored runtime file created on
first user interaction.

## 6. Failure Modes

| Failure | Behavior |
| --- | --- |
| Model artifacts missing | Recommender fails fast with a clear message; regenerate via `scripts/train_fast.py` |
| TMDB key missing | Poster URLs degrade gracefully (no posters) |
| ND enrichment data missing | `NDEnrichment` skips enrichment rather than crashing |
| Tests fail | CI red — `pytest tests/` gates every push |
