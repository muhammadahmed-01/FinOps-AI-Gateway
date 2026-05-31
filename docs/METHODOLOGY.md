# Methodology — what is measured vs modeled

This document defines how to interpret every number in the portfolio. **Regenerate the summary table** after new runs:

```powershell
uv run finops-report-results
```

Output: [data/RESULTS.md](../data/RESULTS.md)

---

## 1. Routing decisions — **measured**

**Source:** `finops-load-test`, `finops-demo-tiers`, `finops-query-gateway`

The Groq classifier assigns each query to `simple | medium | complex`. Counts in Grafana panel **Routing Decision Breakdown** and `data/load_test_results.json` are **observed routing decisions**, not estimates.

Example (latest load test, n=12): **7/12 (58%)** routed to `simple` → Ollama.

---

## 2. Cost in Grafana — **simulated FinOps model (not actual spend)**

**Source:** [src/finops_gateway/routing/pricing.py](../src/finops_gateway/routing/pricing.py)

Grafana panel **Simulated Cost by Tier** applies **Claude Haiku/Sonnet list prices × token counts** returned by the answer model.

| Mode | Who answers medium/complex | Actual API spend | Grafana shows |
|------|----------------------------|------------------|---------------|
| **Demo** (default) | Groq free tier | **$0** | Simulated Claude cost |
| **Live** (`ANTHROPIC_API_KEY` set) | Real Claude | Real Anthropic bill | Same pricing formula on real tokens |

**Do not say** “we saved 76% on API spend” unless you ran with a real Anthropic key and measured bills.

**Do say:** “Tier routing sent 58% of queries to $0 local tier; the FinOps model estimates **~77% lower simulated cost** vs routing every query to the complex tier (Claude list rates × tokens). Actual API spend in demo mode was **$0**.”

Counterfactual “all-complex” uses the **average simulated cost of complex-tier queries in the same load test** × n — not a separate measured run.

---

## 3. Latency — **measured (wall clock)**

**Sources:** `data/load_test_results.json`, Prometheus histograms

| Component | Metric | Notes |
|-----------|--------|-------|
| End-to-end | `latency_s` per request | Includes queueing under concurrency |
| Retrieval | `finops_retrieval_latency_seconds` | Hybrid RAG + rerank |
| Classification | `finops_classification_latency_seconds` | Groq classifier |
| Generation | `finops_generation_latency_seconds{tier}` | Ollama (simple) or Groq/Claude (medium/complex) |

High p50 end-to-end latency on this machine is expected: **local Ollama on 4GB VRAM / CPU Docker is slow**. The breakdown shows retrieval is seconds-scale while **simple-tier generation is minutes-scale** — that is the cost/latency tradeoff, not a broken retriever.

---

## 4. RAGAS — **pilot eval (n=8)**

**Source:** [data/eval/ragas_results_8pair.json](../data/eval/ragas_results_8pair.json)

| Metric | Judge | Valid at n=8? |
|--------|-------|----------------|
| context_precision | Groq LLM (RAGAS) | **Directional yes** — lead metric |
| faithfulness | Groq LLM (RAGAS) | **High variance** — hybrid 1.0000 is not definitive |
| answer_relevancy | Local embedding cosine | Valid but not RAGAS LLM judge |

**Do not call n=8 “canonical” or “production benchmark.”** Expanding to 50 pairs requires judge quota (Groq free tier limits) or a paid judge API.

---

## 5. What this project demonstrates (honest pitch)

1. **Observable gateway** — classify → retrieve → route → metrics/traces  
2. **FinOps modeling** — tier-labeled simulated cost even when APIs are free in dev  
3. **Retrieval eval harness** — baseline vs hybrid with RAGAS + embedding proxy  
4. **Reproducible demo** — `docker compose up` + bootstrap script + Grafana  

It does **not** prove production SLA latency or measured dollar savings without a live Anthropic billing run.
