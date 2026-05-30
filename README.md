# FinOps AI Gateway

An observable, cost-routing AI gateway that routes queries between cheap and expensive LLM tiers based on complexity, with hybrid RAG over LangGraph/LangChain documentation.

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- LangSmith account and API key
- **Ollama** (recommended, free/local) **or** Groq free API key **or** paid OpenAI/Anthropic keys

## Setup

```powershell
cd "c:\Users\hassa\PycharmProjects\FinOps AI Gateway"

# Create virtual environment and install dependencies
uv venv
uv sync

# Configure secrets (do not commit .env)
copy .env.example .env
# Edit .env with your LANGCHAIN_API_KEY, OPENAI_API_KEY, etc.
```

## Postgres + pgvector (Docker)

Start the database:

```powershell
docker compose up -d
```

Verify `pgvector` is installed:

```powershell
docker compose exec postgres psql -U finops -d finops -c "CREATE EXTENSION IF NOT EXISTS vector; SELECT extname FROM pg_extension WHERE extname IN ('vector');"
```

Note: this project defaults to host port `5433` to avoid collisions with any local Postgres running on `5432`.

Stop and delete containers (keeps data volume):

```powershell
docker compose down
```

If you want to wipe the database volume:

```powershell
docker compose down -v
```

## Minimal RAG pipeline (Milestone #4)

1) Make sure Postgres is running:

```powershell
docker compose up -d
```

2) Ensure an embedding model is available in Ollama:

```powershell
ollama pull nomic-embed-text
```

3) Ingest LangGraph docs into pgvector:

```powershell
uv run finops-ingest-langgraph
```

4) Ask a query using cosine similarity retrieval + LLM answer:

```powershell
uv run finops-query-rag --question "What is LangGraph and when should I use it?"
```

Each step is traced to LangSmith. In the query run, check the `retrieve_chunks` and `answer_from_context` spans.

## Milestone 2 — Hybrid retrieval + cost routing

### Stack added

- **BM25 + pgvector** fused with reciprocal rank fusion (RRF)
- **Cross-encoder reranker**: `cross-encoder/ms-marco-MiniLM-L-6-v2` (CPU)
- **Complexity classifier** (structured LLM output → `simple|medium|complex`)
- **Router**:
  - `simple` → Ollama `qwen3:4b` ($0, ~2.5GB — fits 4GB VRAM)
  - `medium` → Claude Haiku (~$0.001/query)
  - `complex` → Claude Sonnet (~$0.015/query)
- **Prometheus metrics** + **Grafana dashboard** (via Pushgateway — metrics persist after queries finish)

### Setup

```powershell
docker compose up -d
ollama pull nomic-embed-text
ollama pull qwen3:4b
uv sync
```

Ensure `.env` has `GROQ_API_KEY` (classifier), `ANTHROPIC_API_KEY` (medium/complex tiers), and `DATABASE_URL`.

### Run gateway queries (metrics on :9464)

Simple factual query (routes to Ollama):

```powershell
uv run finops-query-gateway --question "What is LangGraph?"
```

Complex architecture query (routes to Sonnet):

```powershell
uv run finops-query-gateway --complex-question
```

Run all three tiers in one metrics session (best for Grafana):

```powershell
uv run finops-demo-tiers
```

Keep metrics alive between separate query runs:

```powershell
# Terminal 1
uv run finops-metrics-serve

# Terminal 2
uv run finops-query-gateway --question "What is a race condition?"
uv run finops-query-gateway --complex-question
```

### Grafana

1. Open [http://localhost:3001](http://localhost:3001) (`admin` / `admin`)
2. Dashboard: **FinOps AI Gateway**
3. Confirm panels:
   - **Cost by Tier (USD total)**
   - **Routing Decision Breakdown**
   - **Retrieval Latency p95**
   - **Tokens Used by Tier**

Prometheus UI: [http://localhost:9090](http://localhost:9090)  
Pushgateway UI: [http://localhost:9091](http://localhost:9091)

Metrics are pushed to Pushgateway after each query, so panels stay populated even after the CLI exits.

Exit criterion: run one simple + one complex query; Grafana shows different tiers and non-zero Sonnet/Haiku cost vs $0 Ollama.

## Free LLM options for the smoke test

| Provider | Cost | Setup |
|----------|------|--------|
| **ollama** (default) | Free, runs on your PC | Install [Ollama](https://ollama.com), then `ollama pull llama3.2` |
| **groq** | Free tier with rate limits | API key from [console.groq.com](https://console.groq.com), set `SMOKE_LLM_PROVIDER=groq` |
| openai / anthropic | API billing required | ChatGPT/Claude free plans do **not** include API quota |

Set `SMOKE_LLM_PROVIDER` in `.env` (default: `ollama`). LangSmith tracing works with all of them.

## LangSmith trace smoke test

After filling in `.env` (at minimum LangSmith keys; for Ollama, no LLM API key needed):

```powershell
uv run python -m finops_gateway.scripts.trace_smoke
```

Or use the console script:

```powershell
uv run finops-trace-smoke
```

## Verify tracing in LangSmith

1. Open [LangSmith](https://smith.langchain.com/) (or [EU dashboard](https://eu.smith.langchain.com/)) and sign in.
2. Go to **Projects** → select `finops-ai-gateway` (or whatever you set in `LANGCHAIN_PROJECT`).
3. Open the latest run from the smoke test.
4. Confirm:
   - **Latency** is shown per span (parent run + LLM child span).
   - **Tokens** (input/output) appear on the LLM span.
   - **Cost** is estimated on the LLM span for OpenAI models.

### Troubleshooting

| Symptom | Likely cause |
|---------|----------------|
| No runs in dashboard | `LANGCHAIN_TRACING_V2` not `true`, or `LANGCHAIN_API_KEY` missing/wrong |
| Runs in wrong project | `LANGCHAIN_PROJECT` mismatch vs dashboard filter |
| Latency only, no tokens/cost | Model provider not reporting usage; ensure OpenAI key is valid and model is `gpt-4o-mini` |
| `405` / `JSONDecodeError` on `eu.smith.langchain.com` | Wrong endpoint: use `https://eu.api.smith.langchain.com` (API), not `https://eu.smith.langchain.com` (dashboard) |
| OpenAI `429 insufficient_quota` | Use `SMOKE_LLM_PROVIDER=ollama` or `groq`, or add OpenAI billing credits |
| Ollama connection error | Start Ollama app / `ollama serve`, then `ollama pull llama3.2` |

## Milestone 1 progress

- [x] Python project (`pyproject.toml`, uv, virtual env)
- [x] LangSmith tracing enabled
- [x] Postgres + pgvector (Docker)
- [x] Doc ingestion and retrieval
- [x] End-to-end RAG query with full trace

## Milestone 2 progress

- [x] BM25 + pgvector RRF fusion
- [x] Cross-encoder reranking (ms-marco-MiniLM-L-6-v2)
- [x] Complexity classifier + tier router
- [x] Prometheus metrics (`tokens_used`, `cost_dollars`, `routing_tier`, `retrieval_latency`)
- [x] Grafana dashboard (cost by tier, routing breakdown)
