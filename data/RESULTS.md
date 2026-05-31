# Measured results (generated)

_Do not edit by hand. Regenerate with `uv run finops-report-results`._

## Load test

- Source: `C:/Users/hassa/PycharmProjects/FinOps AI Gateway/data/load_test_results.json`
- Requests: 12 (successful: 12)
- Concurrency: 2
- Wall time: 1656.0s (27.6 min)

### Routing (measured)

- complex: 2/12 (17%)
- medium: 3/12 (25%)
- simple: 7/12 (58%)

### End-to-end latency (measured, wall clock per request)

- p50: 276.2s (4.6 min)
- p95: 601.7s (10.0 min)
- mean: 256.0s (4.3 min)
- max: 638.9s (10.6 min)

### Latency breakdown (measured)

- Retrieval p50: 2.29s
- Classification: _not recorded in this JSON (re-run load test after upgrade)_
- Generation p50 (all tiers): 273.8s (4.6 min)
- Generation p50 (simple tier): 386.6s (6.4 min)
- Generation p50 (medium tier): 3.05s
- Generation p50 (complex tier): 3.83s

### Cost (simulated FinOps model — not actual API spend)

Grafana cost uses **Claude list prices × token counts** from the router. In default demo mode, medium/complex answers run on **Groq (free)** and simple on **Ollama (local)** — **actual API spend was $0**.

- Simulated spend with tier routing: **$0.0143** (12 queries)
- Simulated counterfactual (all 12 queries at avg complex-tier rate): **$0.0609**
- Modeled savings vs all-complex counterfactual: **77%** (simulation only)

## RAGAS pilot eval (n=8)

- Source: `C:/Users/hassa/PycharmProjects/FinOps AI Gateway/data/eval/ragas_results_8pair.json`
- Sample size: **8** Q&A pairs (pilot — not statistically powered)
- Judge (faithfulness, context_precision): Groq llama-3.1-8b-instant (RAGAS faithfulness + context_precision)
- Answer generation: Ollama qwen3:4b (both pipelines)
- answer_relevancy: embedding cosine proxy (not RAGAS LLM judge)

| Metric | Baseline | Hybrid+rerank | Delta |
|--------|----------|---------------|-------|
| context_precision | 0.6042 | 0.7917 | +0.1875 |
| faithfulness | 0.7690 | 1.0000 | +0.2310 |
| answer_relevancy | 0.7716 | 0.7947 | +0.0231 |

**Interpretation:** The reliable signal at n=8 is **context_precision** (retrieval quality). Treat **faithfulness** at 1.0000 as high-variance at small n — do not over-claim.

Small sample (n=8). faithfulness=1.0000 for hybrid has high variance — lead with context_precision delta.
