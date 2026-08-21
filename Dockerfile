# syntax=docker/dockerfile:1
# ═══════════════════════════════════════════════════════════════════════
# Next-Gen-Reco (MovieLens AI) — Streamlit movie recommender
#
# Build targets:
#   prod (default) — production Streamlit server (:8501)
#   dev            — hot reload for local development
#
# Usage:
#   docker build -t movielens-ai .
#   docker compose up -d
# ═══════════════════════════════════════════════════════════════════════

# ── Base stage ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS base

LABEL org.opencontainers.image.title="MovieLens AI"
LABEL org.opencontainers.image.description="Streamlit movie recommender using MovieLens 32M dataset"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.vendor="Next-Gen-Reco"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# tini for PID-1 signal handling
RUN apt-get update && apt-get install -y --no-install-recommends \
        tini \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Deps stage ─────────────────────────────────────────────────────────
FROM base AS deps

COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    # Upgrade build-time/transitive packages with known HIGH CVEs
    # (setuptools CVE-2025-47273, wheel CVE-2026-24049, msgpack GHSA-6v7p-g79w-8964,
    #  jaraco.context CVE-2026-23949) — flagged by the CI trivy gate.
    pip install --no-cache-dir --upgrade \
        "setuptools>=78.1.1" \
        "wheel>=0.46.2" \
        "msgpack>=1.2.1" \
        "jaraco-context>=6.1.0"

# ── Prod stage ─────────────────────────────────────────────────────────
FROM deps AS prod

RUN useradd --create-home --uid 10001 appuser && \
    mkdir -p /app/.cache && \
    chown -R appuser:appuser /app

# Application code
COPY app/ ./app/
COPY app.py ./
COPY data/ ./data/
COPY models/ ./models/
COPY .streamlit/ ./.streamlit/

USER appuser

EXPOSE 8501

# Streamlit health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -fsS http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["/usr/bin/tini", "--"]
STOPSIGNAL SIGTERM
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]

# ── Dev stage: hot reload + test tooling ───────────────────────────────
FROM deps AS dev

# pytest for the in-container test target (make test)
RUN pip install --no-cache-dir pytest

RUN useradd --create-home --uid 10001 appuser && \
    mkdir -p /app/.cache && \
    chown -R appuser:appuser /app

COPY app/ ./app/
COPY app.py ./
COPY data/ ./data/
COPY models/ ./models/
COPY .streamlit/ ./.streamlit/

USER appuser

EXPOSE 8501

# --server.fileWatcherType=polling works on bind-mounted source trees
STOPSIGNAL SIGTERM
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false", \
     "--server.fileWatcherType=polling", \
     "--server.runOnSave=true"]
