#!/usr/bin/env bash
# Bring up the CPU test stack, run integration tests, tear down.
# Usage: scripts/test-integration.sh [--keep]   (--keep leaves the stack running)
set -euo pipefail
cd "$(dirname "$0")/.."

ENV_FILE=.env.ci
set -a; source "$ENV_FILE"; set +a
COMPOSE=(docker compose --env-file "$ENV_FILE" --profile cpu)

cleanup() { [[ "${1:-}" == "--keep" ]] || "${COMPOSE[@]}" down -v; }
trap 'cleanup "${KEEP:-}"' EXIT
[[ "${1:-}" == "--keep" ]] && KEEP=--keep

"${COMPOSE[@]}" up -d ollama postgres
echo "Pulling $TEST_MODEL ..."
"${COMPOSE[@]}" exec -T ollama ollama pull "$TEST_MODEL"

"${COMPOSE[@]}" up -d open-webui
echo "Waiting for Open WebUI ..."
for _ in $(seq 1 180); do
  curl -sf "http://localhost:${WEBUI_PORT}/health" >/dev/null && break
  sleep 5
done
curl -sf "http://localhost:${WEBUI_PORT}/health" >/dev/null || { "${COMPOSE[@]}" logs --tail 100 open-webui; exit 1; }

python3 -m pip install -q -r tests/requirements.txt
WEBUI_BASE="http://localhost:${WEBUI_PORT}" python3 -m pytest -v tests/integration
