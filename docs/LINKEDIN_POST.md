# LinkedIn post draft

**Attach:** [docs/images/grafana-cost-by-tier.png](images/grafana-cost-by-tier.png)

---

I built an observable AI gateway that routes LangGraph doc queries by complexity — and I'm careful about which numbers are measured vs modeled.

**Measured:**
→ **58%** of queries routed to local Ollama (7/12 load test)
→ Retrieval p50 **~2s**; local generation p50 **~6 min** (4GB GPU) vs cloud **~seconds**
→ Hybrid retrieval **+0.19 context_precision** on an 8-pair pilot RAGAS eval

**Modeled (not actual spend):**
→ Grafana FinOps panel estimates **~77% lower simulated cost** vs all-complex-tier routing (Claude list rates × tokens). Actual API spend in demo mode: **$0** (Groq + Ollama).

Stack: Postgres/pgvector, Redis, Ollama, Groq, Prometheus, Grafana, LangSmith.

Clone + bootstrap script → reproducible Grafana dashboard.

Repo: *(add URL when published)*

#FinOps #LLM #RAG #Observability

---

See [METHODOLOGY.md](METHODOLOGY.md) before posting — do not drop the simulated/actual cost distinction.
