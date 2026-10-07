# AGENTS.md — Next-Gen-Reco

> Canonical project instructions. Pointers like `CLAUDE.md` or
> `.github/copilot-instructions.md` should say "See AGENTS.md".

---

## Project overview

**Next-Gen-Reco** — a recommendation engine + dashboard. Core
components:

- **API** — FastAPI service exposing recommendations.
- **Model** — recommender model (collaborative filtering / content).
- **Dashboard** — Streamlit app for reviewing recommendations.
- **Web / Services** — backend services and job workers.

Stack: Python 3.11+ · FastAPI · pandas · scikit-learn · Streamlit.

---

## Exact commands

```bash
# Install
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Lint / typecheck / test
make lint
pre-commit run --all-files
python -m mypy . --ignore-missing-imports
python -m pytest tests/ -v --cov=. --cov-fail-under=70

# Run
uvicorn api.main:app --reload
streamlit run dashboard/app.py
```

---

## Folder map

| Path | Purpose |
|------|---------|
| `api/` | FastAPI application (routes, services) |
| `model/` | Recommender model + training |
| `dashboard/` | Streamlit dashboard |
| `services/` | Job workers, ingestion |
| `tests/` | pytest suite |
| `.github/workflows/` | CI (ruff, mypy, pytest, gitleaks, trivy) |

## Do / don't

- **Do** keep the model interface behind a stable service class.
- **Do not** commit `.env` files.
- **Do not** commit raw user interaction logs (PII).

## Security rules

- No secrets in the repository; `gitleaks` CI gate gates on hits.
- Interaction data must be anonymized before any file leaves the sandbox.

## AI-assistance convention

Commits authored by AI must carry the trailer:

```text
AI-Assisted: yes | no | partial
```

See `.gitmessage` for the template. Do not rewrite historic commits
retroactively.
