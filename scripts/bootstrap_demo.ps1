# FinOps AI Gateway — one-command interview demo bootstrap
# Prerequisites: Docker, uv, Python 3.11+, .env with GROQ_API_KEY + LANGCHAIN_API_KEY

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "=== FinOps AI Gateway demo bootstrap ===" -ForegroundColor Cyan

if (-not (Test-Path ".env")) {
    Write-Host "ERROR: Copy .env.example to .env and set GROQ_API_KEY + LANGCHAIN_API_KEY" -ForegroundColor Red
    exit 1
}

Write-Host "`n[1/8] Starting Docker stack (Postgres, Redis, Prometheus, Grafana, Ollama)..."
docker compose up -d

Write-Host "`n[2/8] Waiting for Postgres..."
$pgReady = $false
for ($i = 0; $i -lt 60; $i++) {
    docker compose exec -T postgres pg_isready -U finops -d finops 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { $pgReady = $true; break }
    Start-Sleep -Seconds 2
}
if (-not $pgReady) {
    Write-Host "ERROR: Postgres did not become ready in time" -ForegroundColor Red
    exit 1
}

Write-Host "`n[3/8] Waiting for Ollama..."
$ollamaReady = $false
for ($i = 0; $i -lt 60; $i++) {
    try {
        Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 5 -UseBasicParsing | Out-Null
        $ollamaReady = $true
        break
    } catch {
        Start-Sleep -Seconds 3
    }
}
if (-not $ollamaReady) {
    Write-Host "ERROR: Ollama did not become ready. See docs/OLLAMA.md" -ForegroundColor Red
    exit 1
}

Write-Host "`n[4/8] Pulling Ollama models (first run may take several minutes)..."
docker exec finops_ollama ollama pull nomic-embed-text
docker exec finops_ollama ollama pull qwen3:4b

Write-Host "`n[5/8] Installing Python dependencies..."
uv sync

Write-Host "`n[6/8] Ingesting LangGraph docs into pgvector..."
uv run finops-ingest-langgraph

Write-Host "`n[7/8] Running demo queries + load test (may take 10-20 min on CPU Ollama)..."
uv run finops-demo-tiers
uv run finops-load-test --requests 12 --concurrency 2

Write-Host "`n[8/8] Publishing saved RAGAS scores + load-test metrics to Grafana..."
uv run finops-publish-results

Write-Host "`n=== Demo ready ===" -ForegroundColor Green
Write-Host "Grafana:    http://localhost:3001  (admin / admin)"
Write-Host "Dashboard:  FinOps AI Gateway"
Write-Host "Prometheus: http://localhost:9090"
Write-Host "`nResults: data/load_test_results.md, data/eval/ragas_results_8pair.md"
