# Old Tree → New Tree — Next-Gen-Reco

Restructure performed **2026-08-11** (v6, Principal Architect protocol). The repo
already had the layered `app/` package, `scripts/`, `tests/`, `data/`, and `models/`;
this pass consolidates migration records and replaces the inaccurate stub docs with
the real Phase 6 suite. **Zero code/import/entry-point changes.**

## Before (2026-08-10)

```
Next-Gen-Reco/
├── app.py                        (Streamlit bootstrap)
├── app/ (paths, main, model, recommender, enrichment, data/loader, ui/*)
├── data/ (movies.csv, tags.csv, links.csv, ND/)
├── models/v1_test/ (joblib artifacts)
├── scripts/ (fix_regex.py, train_fast.py)
├── tests/ (test_model.py, test_syntax.py, test_pattern.txt)
├── docs/
│   ├── architecture.md           (STUB — 2 lines, inaccurate)
│   ├── folder_structure.md       (STUB — 9 lines, inaccurate)
│   ├── migration_summary.md      (root of docs/)
│   ├── community/ design/ product/ project/ reference/ technical/
├── .github/workflows/ · .devcontainer/ · .streamlit/ · .vscode/
├── Dockerfile · docker-compose*.yml · setup.sh · Makefile
├── pyproject.toml · requirements.txt · runtime.txt
├── README.md · PROJECT_OVERVIEW.md · PROJECT_ANALYSIS.md · AGENTS.md
└── .env.example · .env.template · .gitignore · .dockerignore · .editorconfig · .gitattributes
```

## After (2026-08-11)

```
Next-Gen-Reco/
├── app.py                        (unchanged — entry contract)
├── app/ · data/ · models/ · scripts/ · tests/   (all unchanged)
├── docs/
│   ├── architecture.md           (REWRITTEN — accurate)
│   ├── folder_structure.md       (REWRITTEN — accurate)
│   ├── module_dependency.md      (NEW)
│   ├── startup_flow.md           (NEW)
│   ├── package_overview.md       (NEW)
│   ├── migration/
│   │   ├── migration_summary.md  (MOVED from docs/)
│   │   ├── old_tree_to_new_tree.md (NEW — this file)
│   │   └── file_move_ledger.md   (NEW)
│   ├── community/ design/ product/ project/ reference/ technical/  (unchanged)
├── .github/workflows/ · .devcontainer/ · .streamlit/ · .vscode/     (unchanged)
├── Dockerfile · docker-compose*.yml · setup.sh · Makefile           (unchanged)
├── pyproject.toml · requirements.txt · runtime.txt                  (unchanged)
├── README.md · PROJECT_OVERVIEW.md · PROJECT_ANALYSIS.md · AGENTS.md (unchanged)
└── .env.example · .env.template · .gitignore · .dockerignore · .editorconfig · .gitattributes (unchanged)
```

## Summary

| Kind | Count |
| --- | --- |
| Files moved (`git mv`) | 1 |
| Docs rewritten (inaccurate stubs → accurate) | 2 |
| Docs added | 5 |
| Code / imports / entry points / CI / Docker changed | 0 |
| Deleted | 0 |
