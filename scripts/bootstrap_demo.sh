#!/usr/bin/env bash
# FinOps AI Gateway — one-command interview demo bootstrap
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== FinOps AI Gateway demo bootstrap ==="

if [[ ! -f .env ]]; then
  echo "ERROR: Copy .env.example to .env and set GROQ_API_KEY + LANGCHAIN_API_KEY"
  exit 1
fi

echo
echo "[1/8] Starting Docker stack..."
docker compose up -d

echo
echo "[2/8] Waiting for Postgres..."
for _ in $(seq 1 60); do
  if docker compose exec -T postgres pg_isready -U finops -d finops >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

echo
echo "[3/8] Waiting for Ollama..."
for _ in $(seq 1 60); do
  if curl -sf http://localhost:11434/api/tags >/dev/null; then
    break
  fi
  sleep 3
done

echo
echo "[4/8] Pulling Ollama models..."
docker exec finops_ollama ollama pull nomic-embed-text
docker exec finops_ollama ollama pull qwen3:4b

echo
echo "[5/8] Installing Python dependencies..."
uv sync

echo
echo "[6/8] Ingesting LangGraph docs..."
uv run finops-ingest-langgraph

echo
echo "[7/8] Demo queries + load test..."
uv run finops-demo-tiers
uv run finops-load-test --requests 12 --concurrency 2

echo
echo "[8/8] Publishing metrics to Grafana..."
uv run finops-publish-results

echo
echo "=== Demo ready ==="
echo "Grafana:    http://localhost:3001  (admin / admin)"
echo "Dashboard:  FinOps AI Gateway"
