"""Run the LangGraph agent as an HTTP service."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import uvicorn

# Allow running both:
# 1) python -m agent.service
# 2) python agent/service.py
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Project LLM agent API service")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=8090, help="Bind port")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logs")
    args = parser.parse_args()

    setup_logging(args.verbose)
    logging.getLogger(__name__).info(
        "Starting service on http://%s:%d", args.host, args.port
    )

    uvicorn.run(
        "agent.api.server:app",
        host=args.host,
        port=args.port,
        access_log=True,
        log_level="debug" if args.verbose else "info",
        log_config=None,
    )


if __name__ == "__main__":
    main()

