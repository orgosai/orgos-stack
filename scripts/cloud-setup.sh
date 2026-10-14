#!/usr/bin/env bash
# Setup script for a Claude Code cloud environment (runs as root before the session starts).
# Pre-pulls images so they are cached in the environment snapshot.
set -euo pipefail
cd "$(dirname "$0")/.." 2>/dev/null || true
pip install -q pytest==8.4.2 requests==2.32.5
docker compose --env-file .env.ci --profile cpu pull ollama postgres open-webui || true
