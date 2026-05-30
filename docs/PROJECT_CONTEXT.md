# FinOps AI Gateway — Project Context

Distilled reference for humans and AI assistants. Read this first when resuming work.

## What this is

An **observable, cost-routing AI gateway** over a document corpus (LangGraph/LangChain docs or custom seeds). It classifies query complexity, retrieves context with hybrid RAG, routes to cheap vs expensive LLMs, and exposes **tokens, cost, routing tier, and latency** in LangSmith + Grafana.

## Architecture (one query)

1. **Classify** (Groq `llama-3.1-8b-instant`) → `simple | medium | complex`
2. **Retrieve** — pgvector + BM25 → RRF fusion → cross-encoder rerank → top-k chunks
3. **Answer** — tier picks model:
   - `simple` → Ollama `qwen3:4b` (local, $0 actual)
   - `medium` → Claude Haiku 4.5 *or* Groq fallback if no Anthropic key
   - `complex` → Claude Sonnet 4.5 *or* Groq fallback
4. **Metrics** — push to Pushgateway → Prometheus → Grafana

## Billing model (important)

| What Grafana shows | What you actually pay |
|--------------------|------------------------|
| Claude Haiku/Sonnet **list prices** × tokens | Only if real `ANTHROPIC_API_KEY` is set |
| Simple tier $0 | Ollama local — always $0 |
| Medium/complex with placeholder Anthropic key | **Groq free tier** answers; Grafana still shows simulated Claude cost |

Pricing source: https://platform.claude.com/docs/en/about-claude/pricing  
- Haiku 4.5: $1 / $5 per MTok (in/out)  
- Sonnet 4.5: $3 / $15 per MTok (in/out)

**Cursor Pro does not provide API keys** for this repo. Use your own Groq / Anthropic / OpenAI keys in `.env`.

## Environment (this machine)

| Setting | Value |
|---------|--------|
| Postgres | `localhost:5433` (Docker; avoids local 5432 conflict) |
| LangSmith EU | `LANGCHAIN_ENDPOINT=https://eu.api.smith.langchain.com` |
| Grafana | http://localhost:3001 (admin/admin) |
| Prometheus | http://localhost:9090 |
| Pushgateway | http://localhost:9091 |
| Ollama embed | `nomic-embed-text` |
| Ollama simple | `qwen3:4b` (~2.5GB, 4GB VRAM OK) |
| Classifier + Groq fallback | `GROQ_API_KEY` |

## Key commands

```powershell
docker compose up -d
uv run finops-ingest-langgraph          # or custom seeds in langgraph_docs.py
uv run finops-query-gateway --question "..."
uv run finops-demo-tiers                # populate all 3 Grafana tiers
```

## Milestone status

- **M1** ✓ Python/uv, LangSmith, Postgres+pgvector, basic RAG, traces
- **M2** ✓ Hybrid RAG, reranker, classifier, router, Pushgateway, Grafana dashboard

## Repo layout

```
src/finops_gateway/
  routing/       classifier, router, pricing
  rag/           db, hybrid, reranker
  ingestion/     crawler/chunker
  scripts/       query_gateway, demo_tiers, ingest, trace_smoke
  metrics.py     Prometheus → Pushgateway
docker/          prometheus, grafana provisioning
```

## Gotchas

- Windows: avoid bare `curl` in PowerShell (hangs); use `docker exec ... wget -T 5` or `Invoke-WebRequest -TimeoutSec 10`
- Metrics persist via **Pushgateway**, not ephemeral port 9464
- `increase()` in Grafana fails on counter resets; dashboard uses raw counters + bar gauge for cost
- Groq free tier limits reset per-minute (RPM/TPM) and daily at midnight UTC (RPD)

## User preferences (Muhammad)

- Python tooling: **uv**
- Minimize scope; no drive-by refactors
- Don't git commit unless asked
- Shell commands need timeouts; don't leave background terminals hanging
