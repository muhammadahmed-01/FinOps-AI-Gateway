# FinOps AI Gateway

An observable, cost-routing AI gateway: classify query complexity, retrieve with hybrid RAG, route to cheap vs expensive LLM tiers, and expose **routing, latency breakdown, modeled cost, and eval scores** in Grafana + LangSmith.

## 60-second demo

```powershell
copy .env.example .env   # GROQ_API_KEY + LANGCHAIN_API_KEY
.\scripts\bootstrap_demo.ps1
```

Open **http://localhost:3001** → dashboard **FinOps AI Gateway**.

**Numbers for interviews:** [data/RESULTS.md](data/RESULTS.md) (generated from committed JSON — run `uv run finops-report-results` after new benchmarks).

---

## Problem

Teams shipping RAG + LLM features face two blind spots:

1. **Cost visibility** — every query hits the same model tier with no per-request accounting.
2. **Retrieval quality** — BM25/reranker changes are hard to compare without structured eval.

This project is a **FinOps control plane for a gateway**: route by complexity, expose tier-labeled metrics, and compare retrieval pipelines — with explicit separation between **measured behavior** and **simulated cost modeling**.

---

## Architecture

![Architecture diagram](docs/images/architecture.png)

Editable source: [docs/architecture.excalidraw](docs/architecture.excalidraw)

**One query:** classify (Groq) → hybrid retrieve (pgvector + BM25 + rerank) → route (Ollama / Groq or Claude) → Pushgateway → Grafana + LangSmith.

Ollama: bundled in Docker Compose by default ([docs/OLLAMA.md](docs/OLLAMA.md)). Optional host GPU on Windows for faster local generation.

---

## Results

Full definitions: [docs/METHODOLOGY.md](docs/METHODOLOGY.md). Summary from latest committed artifacts:

### Routing (measured) — load test n=12

| Finding | Value |
|---------|-------|
| Simple tier (local Ollama) | **7 / 12 (58%)** |
| Medium | 3 / 12 |
| Complex | 2 / 12 |

### Latency (measured)

| Component | p50 (approx.) |
|-----------|----------------|
| End-to-end | **~276s** (concurrency=2, local Ollama) |
| Retrieval | **~2.3s** |
| Generation (simple tier) | **~356s** (local Ollama — dominates wall time) |
| Generation (medium/complex) | **~1–4s** (Groq in demo mode) |

Retrieval is fast; **local generation is slow and free**. See Grafana panel **Latency Breakdown p50**.

### Cost (simulated FinOps model — not actual API spend)

Default demo mode uses **Groq + Ollama ($0 actual)**. Grafana applies **Claude list rates × tokens** for medium/complex tiers.

| Metric | Value |
|--------|-------|
| Simulated spend (tier routing) | **$0.0143** (12 queries) |
| Simulated all-complex counterfactual | **$0.0609** |
| Modeled savings vs counterfactual | **~77%** (simulation only) |
| **Actual API spend (demo mode)** | **$0** |

### RAGAS pilot (n=8 — directional only)

| Metric | Baseline | Hybrid | Delta |
|--------|----------|--------|-------|
| **context_precision** | 0.6042 | **0.7917** | **+0.1875** |
| faithfulness | 0.7690 | 1.0000 | +0.2310 *(high variance at n=8)* |
| answer_relevancy | 0.7716 | 0.7947 | +0.0231 *(embedding proxy)* |

Source: [data/eval/ragas_results_8pair.md](data/eval/ragas_results_8pair.md)

---

## How to run

### Prerequisites

- Python 3.11+, [uv](https://docs.astral.sh/uv/), Docker Desktop
- Free [Groq](https://console.groq.com) + [LangSmith](https://smith.langchain.com) API keys

### Bootstrap

```powershell
copy .env.example .env
.\scripts\bootstrap_demo.ps1
```

Then regenerate the factual summary:

```powershell
uv run finops-report-results
uv run finops-publish-results
```

### URLs

| Service | URL |
|---------|-----|
| Grafana | http://localhost:3001 (admin / admin) |
| Prometheus | http://localhost:9090 |

### Tests

```powershell
uv sync --group dev
uv run pytest
```

---

## Further reading

| Doc | Topic |
|-----|-------|
| [docs/METHODOLOGY.md](docs/METHODOLOGY.md) | Measured vs simulated — read before interviews |
| [data/RESULTS.md](data/RESULTS.md) | Auto-generated numbers from JSON |
| [docs/RAGAS_EVAL.md](docs/RAGAS_EVAL.md) | RAGAS workflow |
| [docs/BLOG_DRAFT.md](docs/BLOG_DRAFT.md) | Blog copy (honest framing) |
| [docs/PUBLISH.md](docs/PUBLISH.md) | GitHub / LinkedIn checklist |

---

## Interview talking points

**Say:** “58% of queries routed to local Ollama; retrieval improved +0.19 context_precision on an 8-pair pilot; Grafana separates retrieval (~2s) from local generation (~6 min p50) vs cloud (~seconds).”

**Say:** “Cost panel is a FinOps **model** using Claude list rates — actual spend was $0 on Groq/Ollama demo mode.”

**Don't say:** “We cut API spend 76%” without a measured Anthropic bill.
