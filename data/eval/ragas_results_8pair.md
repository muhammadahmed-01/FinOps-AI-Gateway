# RAGAS results — pilot eval (n=8)

**Not a production benchmark.** Eight pairs is enough to compare retrieval pipelines directionally; it is not statistically powered for strong faithfulness claims.

| Metric | Baseline (cosine) | Hybrid+rerank | Delta |
|--------|-------------------|---------------|-------|
| **context_precision** | 0.6042 | **0.7917** | **+0.1875** |
| faithfulness | 0.7690 | 1.0000 | +0.2310 |
| answer_relevancy | 0.7716 | 0.7947 | +0.0231 |

## Methodology

| Setting | Value |
|---------|--------|
| Sample size | 8 Q&A pairs, k=4 chunks |
| Judge (faithfulness, context_precision) | Groq `llama-3.1-8b-instant` |
| Answer generation (both pipelines) | Ollama `qwen3:4b` |
| answer_relevancy | Embedding cosine proxy (local, not RAGAS LLM) |

**How to cite:** Hybrid retrieval improved **context_precision by +0.19** on an 8-pair pilot eval. Treat hybrid faithfulness **1.0000** as noisy at n=8.

Structured source: [ragas_results_8pair.json](ragas_results_8pair.json)

Publish to Grafana without re-running the judge:

```powershell
uv run finops-publish-results
```
