# RAGAS results

## Pilot eval (n=8) — use for portfolio

See **[ragas_results_8pair.md](ragas_results_8pair.md)**. Lead with **context_precision** (+0.19); do not over-claim faithfulness at n=8.

## Invalid runs — do not cite

### 20 pairs — local Ollama judge failed (JSON parse)

| Metric | Baseline | Hybrid | Delta |
|--------|----------|--------|-------|
| faithfulness | 0.0000 | 0.0000 | +0.0000 |
| answer_relevancy | 0.5206 | 0.5206 | +0.0000 |
| context_precision | 0.0000 | 0.0000 | +0.0000 |

### 50 pairs — Groq quota exhausted mid-run

Hybrid faithfulness/context_precision invalid (0.0000). See `data/eval/ragas_full_50.log`.
