# Blog draft: FinOps for AI gateways

**Working title:** *I built a FinOps control plane for LLM routing — 58% of queries never left my laptop*

---

## Hook

Cloud FinOps teams track EC2 and S3. AI teams often ship a single model endpoint and hope the bill is fine. I wanted something you can **show in a client call**: classify complexity, route cheap vs expensive models, and prove retrieval quality with numbers — not vibes.

## What I built

**FinOps AI Gateway** sits in front of a RAG pipeline over LangGraph documentation:

1. Groq classifies each query as simple, medium, or complex.
2. Hybrid retrieval (BM25 + pgvector + reranker) fetches context.
3. Simple queries answer on local Ollama; harder ones escalate to cloud models.
4. Every query pushes **cost, tier, tokens, and latency** to Grafana via Prometheus.

![Architecture](../docs/images/architecture.png)

## Two numbers that matter

### 1. Cost routing — 58% local, ~76% lower simulated spend

In a 12-request load test against real eval questions:

- **58%** of queries (7/12) routed to the **simple tier** — local Ollama at **$0** simulated cost.
- Total **simulated Claude-equivalent spend** with smart routing: **$0.015** for 12 queries.
- If every query had hit the **complex tier** (~$0.0052/query average): **~$0.062** total.
- That is **~76% lower simulated token spend** while still answering medium/complex questions on cloud fallback.

*Source: `data/load_test_results.json`, pricing model in `src/finops_gateway/routing/pricing.py`.*

> **Interview honesty:** Grafana uses Claude list prices for demo accounting. On my setup, medium/complex answers often run on Groq free tier — actual API spend was $0. The routing *decisions* and relative cost story are real.

### 2. Retrieval quality — context precision 0.60 → 0.79

Hybrid retrieval (BM25 + vector + cross-encoder rerank) vs cosine-only baseline, **8-pair RAGAS eval**:

| Metric | Baseline | Hybrid | Delta |
|--------|----------|--------|-------|
| **context_precision** | 0.6042 | **0.7917** | **+0.1875** |
| faithfulness | 0.7690 | 1.0000 | +0.2310 |

Better chunks → better answers without sending every query to the biggest model.

*Source: `data/eval/ragas_results_8pair.json` — canonical 8-pair benchmark.*

## Stack

- **Postgres + pgvector** — doc store and vector search
- **Redis** — multi-turn session cache
- **Ollama** — embeddings + simple-tier answers (Docker Compose or host GPU)
- **Groq** — classifier + demo fallback for medium/complex
- **Prometheus + Grafana** — cost by tier, routing breakdown, RAGAS panel
- **LangSmith** — per-query traces

## Reproduce it yourself

```powershell
git clone <repo>
copy .env.example .env   # GROQ_API_KEY + LANGCHAIN_API_KEY
.\scripts\bootstrap_demo.ps1
```

Open Grafana at http://localhost:3001 — dashboard **FinOps AI Gateway**.

First run takes ~15–25 minutes (doc ingest + load test on CPU Ollama). Saved RAGAS scores publish instantly via `finops-publish-results` — no paid judge API required for the demo.

## Limitations (on purpose)

- **8-pair RAGAS** — enough to prove hybrid > baseline; not a production SLA dataset.
- **Latency** — p50 ~56s on my 4GB GPU / CPU Docker Ollama; this project optimizes **cost observability**, not sub-second serving.
- **Simulated pricing** — FinOps dashboards should show *relative* tier cost even when APIs are free in dev.

## Call to action

Repo: *(add GitHub URL when published)*  
Questions welcome — especially on tier thresholds and when hybrid RAG pays for itself.

---

*Draft generated from committed benchmark artifacts. Update clone URL in [PUBLISH.md](PUBLISH.md) before posting.*
