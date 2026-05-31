"""Multi-turn Redis chat session demo and 5-turn context verification."""

from __future__ import annotations

import argparse
import sys

from finops_gateway.config import load_settings, validate_database, validate_embeddings
from finops_gateway.session.chat import chat_turn, extract_name_from_answer, verify_session_recall
from finops_gateway.session.redis_store import SessionStore

DEFAULT_TURNS = [
    "My name is Alex and I'm building a LangGraph agent with checkpointing.",
    "What is LangGraph and when should I use it?",
    "How do checkpoints work in LangGraph?",
    "What is my name?",
    "Summarize what we've discussed in two sentences.",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Redis-backed multi-turn chat session.")
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Run built-in 5-turn verification (checks name recall on turn 4).",
    )
    parser.add_argument("--session-id", default="", help="Reuse an existing session id.")
    parser.add_argument("--message", default="", help="Single message mode.")
    return parser.parse_args()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    load_settings()
    validate_database()
    validate_embeddings()

    store = SessionStore()
    if not store.ping():
        raise RuntimeError("Redis unavailable. Start docker compose (redis service).")

    args = parse_args()
    session_id = args.session_id or store.new_session_id()
    print(f"session_id={session_id}")

    if args.verify:
        for idx, turn in enumerate(DEFAULT_TURNS, start=1):
            print(f"\n--- Turn {idx} ---")
            print(f"User: {turn}")
            answer = chat_turn(store, session_id, turn)
            print(f"Assistant: {answer[:500]}{'...' if len(answer) > 500 else ''}")

        history_ok = verify_session_recall(store, session_id, "Alex")
        turn4_messages = store.get_messages(session_id)
        turn4_answer = ""
        if len(turn4_messages) >= 8:
            turn4_answer = turn4_messages[7].content
        name_in_turn4 = extract_name_from_answer(turn4_answer) == "Alex" or "alex" in turn4_answer.lower()

        print("\nVerification:")
        print(f"  history contains 'Alex': {history_ok}")
        print(f"  turn 4 recalls name: {name_in_turn4}")
        if history_ok and name_in_turn4:
            print("PASS: 5-turn session maintained context.")
        else:
            print("FAIL: session did not maintain context — check Redis and chat prompt.")
        return

    if not args.message:
        raise RuntimeError("Provide --message or use --verify.")

    answer = chat_turn(store, session_id, args.message)
    print(f"\nAssistant:\n{answer}")


if __name__ == "__main__":
    main()
