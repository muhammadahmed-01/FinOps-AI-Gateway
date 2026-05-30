# CLAUDE.md — FinOps AI Gateway

Instructions for Claude (and similar assistants) working in this repository.

## Project

**FinOps AI Gateway** — cost-routing RAG gateway with LangSmith tracing and Grafana FinOps metrics.

Read [docs/PROJECT_CONTEXT.md](docs/PROJECT_CONTEXT.md) for architecture, env, and billing model.

## Stack

- Python 3.11+, **uv** (`uv sync`, `uv run …`)
- Postgres + pgvector (Docker, port **5433**)
- Ollama (local simple tier + embeddings), Groq (classifier + demo fallback), Anthropic optional
- LangSmith (EU: `eu.api.smith.langchain.com`)
- Prometheus + Pushgateway + Grafana (port **3001**)

## Core pipeline

`finops-query-gateway` → classify → hybrid retrieve (BM25+vector+RRF+rerank) → route by tier → answer → push metrics.

## Cost demo mode

Without a real `ANTHROPIC_API_KEY`, medium/complex use **Groq** for inference but Grafana records **Claude list pricing** from `routing/pricing.py`. Do not claim real Anthropic spend unless keys are configured.

**Cursor Pro subscription ≠ API access** for this project.

## Conventions

- Package: `src/finops_gateway/`
- Config: `.env` (never commit); template in `.env.example`
- Prefer extending existing modules over new abstractions
- Match existing style; minimal diffs
- Only commit when user explicitly asks

## Commands

```powershell
uv run finops-demo-tiers
uv run finops-query-gateway --question "..."
uv run finops-ingest-langgraph
uv run pytest
docker compose up -d
```

## Subagents (`.cursor/agents/`)

- `llm-best-practices-reviewer` — readonly audit vs Anthropic/LangChain/LangSmith docs
- `test-verifier` — runs `uv run pytest -v` and reports results

## Windows

- Use `;` not `&&` in PowerShell
- Always timeout HTTP checks; prefer `docker exec finops_prometheus wget -T 5 …`

## Do not

- Edit plan files in `.cursor/plans/` unless asked
- Use dashboard URL as `LANGCHAIN_ENDPOINT`
- Commit `.env` or secrets
