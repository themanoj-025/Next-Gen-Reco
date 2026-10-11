# DEAD-WEIGHT PURGE v2.0 AUDIT REPORT

**Repository**: `Next-Gen-Reco`  
**Mode**: `AUDIT_ONLY` (Zero repository modifications performed)  
**Baseline Commit SHA**: `9095697e9e8c8890c5ad00cde398201e4dd936c8`  
**Audit Date**: 2026-10-11  
**Verdict**: **YELLOW** (Dead weight detected; review recommended)

---

## 1. Executive Summary

- **Tracked Files in Git**: 184
- **Untracked Local Files**: 0
- **Total LOC**: 1,19,405
- **Analyzed Size**: 91.08 MB
- **Total Dead-Weight Candidates Identified**: 104
  - **Tier 0 (Provable Junk/Empty)**: 69
  - **Tier 1 (High Confidence)**: 1
  - **Tier 2 (Medium / Needs Verification)**: 34
  - **Tier 3 (Protected / Hard Vetoed)**: 0

## 2. Findings by Category

| Category | Description | Count |
|---|---|---|
| **A** | Empty & Near-Empty Files | 2 |
| **C** | Junk / Caches / Build Artifacts | 67 |
| **D** | Potential Orphan Modules | 35 |
| **H** | Exact Hash Duplicates | 0 |

### Top Tier-0 Items (Provable Deletion Candidates if EXECUTE_SAFE were used):
- [`A`] `app/py.typed`: 0-byte file with no content
- [`A`] `py.typed`: 0-byte file with no content
- [`C`] `.cache/`: Untracked build/dependency/cache artifact directory in workspace
- [`C`] `.cleanup-audit/`: Untracked build/dependency/cache artifact directory in workspace
- [`C`] `.cleanup-audit/.claude/`: Untracked build/dependency/cache artifact directory in workspace
- [`C`] `.github/copilot-instructions.md`: Untracked build/dependency/cache artifact directory in workspace
- [`C`] `.hypothesis/`: Untracked build/dependency/cache artifact directory in workspace
- [`C`] `.hypothesis/.gitignore`: Untracked build/dependency/cache artifact directory in workspace
- [`C`] `.hypothesis/unicode_data/`: Untracked build/dependency/cache artifact directory in workspace
- [`C`] `.movie_user_data.json`: Untracked build/dependency/cache artifact directory in workspace
- [`C`] `.mypy_cache/`: Untracked build/dependency/cache artifact directory in workspace
- [`C`] `.mypy_cache/.gitignore`: Untracked build/dependency/cache artifact directory in workspace
- [`C`] `.mypy_cache/3.11/`: Untracked build/dependency/cache artifact directory in workspace
- [`C`] `.mypy_cache/3.12/`: Untracked build/dependency/cache artifact directory in workspace
- [`C`] `.mypy_cache/CACHEDIR.TAG`: Untracked build/dependency/cache artifact directory in workspace
_...and 54 more listed in `manifest.csv`._

## 3. Next Steps & Recommended Actions

1. Review `.purge-reports/manifest.csv` and `.purge-reports/FLAGGED.md`.
2. If safe cleanup is desired, configure `MODE: EXECUTE_SAFE` or generate an approval `PLAN.yaml`.
3. Verify that all untracked artifacts (`__pycache__`, `.venv`, `.pytest_cache`) are properly covered in `.gitignore`.
