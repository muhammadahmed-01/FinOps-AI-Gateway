# RAGAS results — 8 pairs (canonical)

Authoritative benchmark for portfolio / blog numbers. Hybrid beats baseline on all metrics.

| Metric | Baseline (cosine) | Hybrid+rerank | Delta |
|--------|-------------------|---------------|-------|
| faithfulness | 0.7690 | 1.0000 | +0.2310 |
| answer_relevancy | 0.7716 | 0.7947 | +0.0231 |
| context_precision | 0.6042 | 0.7917 | **+0.1875** |

**Exit criterion met:** hybrid `context_precision` > baseline.

Structured source: [ragas_results_8pair.json](ragas_results_8pair.json)

Publish to Grafana without re-running the judge:

```powershell
uv run finops-publish-results
```
