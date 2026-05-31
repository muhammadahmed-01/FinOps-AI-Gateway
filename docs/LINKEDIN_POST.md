# LinkedIn post draft

**Attach:** [docs/images/grafana-cost-by-tier.png](images/grafana-cost-by-tier.png)

---

I built a FinOps-style AI gateway that routes queries by complexity instead of sending everything to the most expensive model.

On a 12-query load test over LangGraph docs:
→ **58%** of queries routed to local Ollama ($0 tier)
→ **~76%** lower simulated token spend vs routing everything to the complex tier

Hybrid retrieval (BM25 + vector + rerank) beat cosine-only baseline on RAGAS context precision: **0.60 → 0.79** (+0.19 on 8-pair eval).

Stack: Postgres/pgvector, Redis, Ollama, Groq, Prometheus, Grafana, LangSmith.

Clone + `docker compose up` + one bootstrap script reproduces the Grafana dashboard.

Repo: *(add GitHub URL)*

#FinOps #LLM #RAG #MLOps #AIEngineering

---

**Screenshot note:** Capture live from Grafana dashboard **FinOps AI Gateway** panels *Cost by Tier* and *Routing Decision Breakdown* after running `scripts/bootstrap_demo.ps1`, or use the committed PNG in this repo.
