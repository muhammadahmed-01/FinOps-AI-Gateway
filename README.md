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
- [ ] Postgres + pgvector (Docker)
- [ ] Doc ingestion and retrieval
- [ ] End-to-end RAG query with full trace
