# RAGAS evaluation — baseline vs hybrid RAG

Compare **cosine-only** retrieval against **BM25 + pgvector + RRF + cross-encoder rerank** using [RAGAS](https://docs.ragas.io/) metrics.

**Portfolio numbers:** use the **n=8 pilot** in [ragas_results_8pair.md](../data/eval/ragas_results_8pair.md). Interpretation rules: [METHODOLOGY.md](METHODOLOGY.md).
## Metrics

| Metric | What it measures | Judge |
|--------|------------------|-------|
| `faithfulness` | Answer claims supported by retrieved context | RAGAS LLM |
| `answer_relevancy` | Answer addresses the question | Embedding cosine (local) |
| `context_precision` | Top retrieved chunks are relevant | RAGAS LLM |

## LLM providers (important)

**Do not use Groq for RAGAS batch eval** — free tier TPM/TPD limits cause timeouts and invalid scores.

| Role | Recommended | Env vars |
|------|-------------|----------|
| RAGAS judge (faithfulness, context_precision) | **Gemini** `gemini-2.0-flash` (free API) | `GOOGLE_API_KEY` + `RAGAS_LLM_PROVIDER=gemini` |
| RAGAS judge (offline) | **Ollama** `llama3.2:1b` (small, fast on 4GB VRAM) | `RAGAS_OLLAMA_MODEL=llama3.2:1b` |
| Eval answer generation | **Ollama** `qwen3:4b` | `EVAL_LLM_MODEL=qwen3:4b` |

If `GOOGLE_API_KEY` is set and `RAGAS_LLM_PROVIDER` is unset, Gemini is auto-selected for judging.

Groq remains fine for **classifier** and **gateway** (`GROQ_API_KEY`).

## Speed tips (RTX 3050 Ti / 4GB VRAM)

RAGAS is slow on local Ollama because each pair triggers **many** judge LLM calls (baseline + hybrid = 2× pipeline).

1. **Use Gemini for judging** — free at [Google AI Studio](https://aistudio.google.com/apikey); keeps GPU free for answer generation only.
2. **Separate judge model** — `llama3.2:1b` for RAGAS yes/no judging, `qwen3:4b` for answers (already default).
3. **Pipeline cache** — run retrieve+answer once, re-score many times:
   ```powershell
   uv run finops-ragas-eval --limit 5 --save-cache --log-file data/eval/ragas_run_limit5.log
   uv run finops-ragas-eval --limit 5 --use-cache --log-file data/eval/ragas_rescore.log
   ```
4. **Tighter generation** — `EVAL_NUM_PREDICT=256`, `RAGAS_NUM_PREDICT=128`, `OLLAMA_NUM_CTX=3072`, `OLLAMA_KEEP_ALIVE=30m`.
5. **Fastest local-only mode** — set `EVAL_LLM_MODEL=llama3.2:1b` (lower answer quality, ~2× faster).

## Setup

```powershell
docker compose up -d
ollama pull nomic-embed-text
ollama pull qwen3:4b
ollama pull llama3.2:1b

uv run finops-ingest-langgraph
uv run finops-generate-eval-dataset --count 50
```

Optional Gemini judge:

```powershell
# Add to .env: GOOGLE_API_KEY=... and RAGAS_LLM_PROVIDER=gemini
```

## Run evaluation

```powershell
uv run finops-ragas-eval --limit 5 --log-file data/eval/ragas_run_limit5.log
uv run finops-ragas-eval   # full 50 pairs — use Gemini judge or expect long Ollama runs
```

Exit criterion: hybrid **context_precision** > baseline.

Scores push to Pushgateway → Grafana panel **RAGAS Scores (baseline vs hybrid)**.

## Redis multi-turn chat

```powershell
docker compose up -d redis
uv run finops-chat-session --verify
```
