"""FinOps AI Gateway query pipeline with hybrid RAG + cost routing."""



from __future__ import annotations



import argparse
import sys
import time



from langsmith import get_current_run_tree, traceable



from finops_gateway.config import load_settings, routing_mode, validate_gateway

from finops_gateway.context import build_context_blocks

from finops_gateway.metrics import record_query_metrics

from finops_gateway.rag.hybrid import hybrid_retrieve

from finops_gateway.routing.router import answer_with_router, route_query





def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(

        description="Query gateway with hybrid retrieval and cost routing."

    )

    parser.add_argument(

        "--question",

        default="What is LangGraph?",

        help="Question to ask.",

    )

    parser.add_argument(

        "--complex-question",

        action="store_true",

        help="Use a built-in complex query to force Sonnet routing.",

    )

    parser.add_argument("--k", type=int, default=4, help="Final chunks after rerank.")

    return parser.parse_args()





def _configure_stdout() -> None:

    if hasattr(sys.stdout, "reconfigure"):

        sys.stdout.reconfigure(encoding="utf-8", errors="replace")





def _attach_run_metadata(result: dict) -> None:

    run = get_current_run_tree()

    if run is None:

        return

    usage = result["usage"]

    run.metadata.update(

        {

            "routing_tier": result["tier"],

            "routing_mode": usage.get("routing_mode", routing_mode()),

            "complexity_score": result["complexity_score"],

            "needs_human_review": result.get("needs_human_review", False),

            "cost_usd": float(usage["cost_usd"]),

            "input_tokens": int(usage["input_tokens"]),

            "output_tokens": int(usage["output_tokens"]),

            "ls_provider": usage.get("ls_provider"),

            "ls_model_name": usage.get("ls_model_name"),

            "retrieval_latency_s": result["retrieval_latency_s"],
            "classification_latency_s": result["classification_latency_s"],
            "generation_latency_s": result["generation_latency_s"],
        }
    )

    run.tags.extend(["finops-gateway", f"tier:{result['tier']}", f"mode:{routing_mode()}"])





@traceable(name="gateway_query", tags=["finops-gateway"])

def run_gateway(question: str, k: int) -> dict:
    classify_start = time.perf_counter()
    routing = route_query(question)
    classification_latency_s = time.perf_counter() - classify_start

    retrieval = hybrid_retrieve(question, final_k=k)

    context_blocks = build_context_blocks(retrieval.chunks)
    gen_start = time.perf_counter()
    answer, usage = answer_with_router(question, context_blocks, routing.tier)
    generation_latency_s = time.perf_counter() - gen_start

    record_query_metrics(
        tier=routing.tier,
        input_tokens=int(usage["input_tokens"]),
        output_tokens=int(usage["output_tokens"]),
        cost_usd=float(usage["cost_usd"]),
        retrieval_latency_s=retrieval.retrieval_latency_s,
        classification_latency_s=classification_latency_s,
        generation_latency_s=generation_latency_s,
    )

    result = {
        "question": question,
        "tier": routing.tier,
        "complexity_score": routing.complexity_score,
        "reasoning": routing.reasoning,
        "needs_human_review": routing.needs_human_review,
        "answer": answer,
        "sources": retrieval.chunks,
        "usage": usage,
        "retrieval_latency_s": retrieval.retrieval_latency_s,
        "classification_latency_s": classification_latency_s,
        "generation_latency_s": generation_latency_s,
    }

    _attach_run_metadata(result)

    return result





def main() -> None:

    _configure_stdout()

    load_settings()

    validate_gateway()



    args = parse_args()

    question = args.question

    if args.complex_question:

        question = (

            "Design a LangGraph architecture for a multi-agent research workflow "

            "with checkpointing, human-in-the-loop approval, and fallback routing "

            "when tool calls fail. Explain tradeoffs."

        )



    result = run_gateway(question, args.k)



    print("\nRouting:")

    print(f"  tier={result['tier']} score={result['complexity_score']:.2f}")

    print(f"  mode={result['usage'].get('routing_mode', routing_mode())}")

    print(f"  reason={result['reasoning']}")

    if result.get("needs_human_review"):

        print("  needs_human_review=True")

    print(f"  retrieval_latency={result['retrieval_latency_s']:.3f}s")
    print(f"  classification_latency={result['classification_latency_s']:.3f}s")
    print(f"  generation_latency={result['generation_latency_s']:.3f}s")
    print(f"  tokens={result['usage']['total_tokens']} cost=${result['usage']['cost_usd']:.6f}")



    print("\nAnswer:\n")

    print(result["answer"])



    print("\nTop sources:")

    for row in result["sources"]:

        print(f"- {row.title} :: {row.url} (score={row.score:.4f})")



    print(

        "\nMetrics pushed to Pushgateway — refresh Grafana: http://localhost:3001"

    )





if __name__ == "__main__":

    main()


