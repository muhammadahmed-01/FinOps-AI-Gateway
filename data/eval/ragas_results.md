# RAGAS results (20 pairs, k=4)

> **Judge scores invalid** — local `qwen3:4b` failed RAGAS JSON parsing on all 40 judge jobs.
> Do not use faithfulness/context_precision below. Re-score with `--use-cache` + Groq
> `llama-3.3-70b-versatile` when quota resets. Valid benchmark: 8-pair run (hybrid
> context_precision +0.19 vs baseline).

| Metric | Baseline (cosine) | Hybrid+rerank | Delta |
|--------|-------------------|---------------|-------|
| faithfulness | 0.0000 ⚠️ | 0.0000 ⚠️ | +0.0000 |
| answer_relevancy | 0.5206 | 0.5206 | +0.0000 |
| context_precision | 0.0000 ⚠️ | 0.0000 ⚠️ | +0.0000 |

_answer_relevancy = embedding cosine (valid). RAGAS judge metrics require Groq/Gemini re-score._
