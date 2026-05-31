# RAGAS results

## Canonical benchmark — use this for README / blog

See **[ragas_results_8pair.md](ragas_results_8pair.md)** (8 pairs, valid judge scores).

## Latest full run — 20 pairs (judge invalid)

> **Judge scores invalid** — local `qwen3:4b` failed RAGAS JSON parsing on all judge jobs.
> Do not cite faithfulness/context_precision below. Re-score with `--use-cache` + Groq when quota allows.

| Metric | Baseline (cosine) | Hybrid+rerank | Delta |
|--------|-------------------|---------------|-------|
| faithfulness | 0.0000 | 0.0000 | +0.0000 |
| answer_relevancy | 0.5206 | 0.5206 | +0.0000 |
| context_precision | 0.0000 | 0.0000 | +0.0000 |

_answer_relevancy = embedding cosine (valid). RAGAS judge metrics require Groq/Gemini re-score._
