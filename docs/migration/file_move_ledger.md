# File Move Ledger — Next-Gen-Reco

Restructure date: **2026-08-11** (v6) · Method: `git mv` · Branch: `main`
(local commits, no push).

## Moved Files

| # | Old Path | New Path | Category | Reason | Risk | Verified? |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `docs/migration_summary.md` | `docs/migration/migration_summary.md` | Meta → Docs | Consolidate migration records under `docs/migration/` (protocol Phase 6) | Low (0 refs) | ✅ |

## Files Rewritten

| Path | Reason |
| --- | --- |
| `docs/architecture.md` | Inaccurate 2-line stub ("single-file app") → full architecture of the layered `app/` package. |
| `docs/folder_structure.md` | Inaccurate 9-line stub (claimed a non-existent `config/`) → accurate annotated tree. |

## Files Added

| Path | Reason |
| --- | --- |
| `docs/module_dependency.md` | Phase 6 deliverable. |
| `docs/startup_flow.md` | Phase 6 deliverable. |
| `docs/package_overview.md` | Phase 6 deliverable. |
| `docs/migration/old_tree_to_new_tree.md` | Phase 6 deliverable. |
| `docs/migration/file_move_ledger.md` | Phase 6 deliverable (this file). |

## Files Deliberately NOT MOVED (contract analysis)

| Path | Why it stays | Risk if moved |
| --- | --- | --- |
| `app.py` | Streamlit entry — Dockerfile `COPY app.py` + CMD (prod & dev), Streamlit Cloud entry, Makefile `compileall app app.py`, CI py_compile sweep | High |
| `app/` | Importable package — CI runs `from app.* import ...` checks; Makefile compiles it | High |
| `data/`, `models/`, `scripts/`, `tests/` | Already canonical; referenced by CI, Dockerfile COPY, Makefile | Medium |

## Flagged (follow-up backlog)

| Item | Flag |
| --- | --- |
| `.env.example` **and** `.env.template` | Duplicate env templates at root — consolidate to one (`.env.example`) in a dedicated commit after confirming the Cloud/Docker pipeline reads either. |
| `app.py` vs `app/` name collision | Benign today (package precedence; `app.py` is run-only) but confusing to newcomers — documented in `docs/architecture.md` §4. A future rename (e.g. `streamlit_app.py`) requires coordinated Docker/CI/Cloud updates. |
| `.movie_user_data.json` | Runtime file — already gitignored; no action. |

## Deletions

None in this restructure.
