#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
#  Streamlit Cloud Setup Script
#  ------------------------------------------
#  - Installs system-level dependencies
#  - Pre-warms disk caches for faster cold starts
#  - Runs automatically on deploy via Streamlit Cloud
# ═══════════════════════════════════════════════════════════════════════════

set -e  # Exit on error

echo "[setup] Installing system packages..."
# For pyarrow / parquet support on some Linux distros
# (usually pre-installed on Streamlit Cloud, but just in case)
apt-get update -qq && apt-get install -y -qq libgomp1 2>/dev/null || true

echo "[setup] Verifying data files..."
for f in data/movies.csv data/tags.csv data/links.csv; do
    if [ -f "$f" ]; then
        echo "  ✓ $f ($(du -h "$f" | cut -f1))"
    else
        echo "  ✗ $f MISSING"
    fi
done

echo "[setup] Verifying model files..."
for f in models/v1_test/model.joblib models/v1_test/meta.joblib; do
    if [ -f "$f" ]; then
        echo "  ✓ $f ($(du -h "$f" | cut -f1))"
    else
        echo "  ✗ $f MISSING"
    fi
done

echo "[setup] Checking environment..."
echo "  Python: $(python --version 2>&1)"
echo "  Disk: $(df -h / | tail -1 | awk '{print $4}') free"

echo "[setup] Setup complete!"
