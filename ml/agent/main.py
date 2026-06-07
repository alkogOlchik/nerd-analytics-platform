"""CLI entry point for the ReAct agent.

Usage:
    python -m agent.main --query "What is the average of [3, 5, 7, 9]?"
"""

from __future__ import annotations

import argparse
import asyncio
import logging

from langchain_core.messages import HumanMessage

from agent.graph import graph


def setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


async def run(query: str) -> None:
    initial = {"messages": [HumanMessage(content=query)]}
    result = await graph.ainvoke(initial)
    answer = result.get("final_answer") or "(no answer)"
    print(answer)


def main() -> None:
    parser = argparse.ArgumentParser(description="ReAct agent")
    parser.add_argument("--query", required=True, help="User query")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    setup_logging(args.verbose)
    asyncio.run(run(args.query))


if __name__ == "__main__":
    main()
