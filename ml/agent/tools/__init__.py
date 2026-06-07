"""LangChain tool wrappers exposed to the ReAct graph."""

from __future__ import annotations

from typing import Any, Dict

from langchain_core.tools import tool

from .analytics_tool import run_analytics as _run_analytics_impl
from .code_executor import execute_code
from .escalate_tool import escalate_to_operator
from .rag_tool import rag_search as _rag_search_impl
from .review_tool import submit_review
from .web_guide_tool import record_web_guide as _record_web_guide_impl


@tool
def rag_search(query: str, top_k: int = 4) -> Dict[str, Any]:
    """Search the local Chroma knowledge base for relevant document chunks.

    Args:
        query: natural-language query.
        top_k: number of chunks to return.
    """
    return _rag_search_impl(query=query, top_k=top_k)


@tool
def run_analytics(task_description: str) -> Dict[str, Any]:
    """Generate Python (numpy) code for an analytics task and execute it.

    Use this when the user needs numerical analysis, aggregation, or
    statistics computed from data described in natural language.
    """
    return _run_analytics_impl(task_description=task_description)


@tool
async def record_web_guide(
    start_url: str,
    goal: str,
    headless: bool = False,
    max_steps: int = 30,
    model: str | None = None,
) -> Dict[str, Any]:
    """Drive a real browser to achieve a goal on a website and produce a step-by-step
    markdown guide with screenshots.

    Use this when the user wants to interact with a website: open a page, search
    something on Google/Yandex, fill a form, click buttons, extract info from a UI.
    The tool launches a browser (browser-use under the hood), navigates step by step
    toward the goal, captures screenshots, creates a voice-guided MP4 walkthrough
    in a separate videos folder and returns paths to generated artifacts plus
    the first ~2000 characters of the markdown guide as a preview.

    Args:
        start_url: starting URL, e.g. "https://google.com".
        goal: natural-language description of what to achieve on the site
              (Russian or English). For example: "search for 'python tutorials'
              and report the first 3 results".
        headless: run the browser without a visible window (default False).
        max_steps: hard cap on browser actions (default 30).
        model: optional model override for recorder's Ollama model.
    """
    return await _record_web_guide_impl(
        start_url=start_url,
        goal=goal,
        headless=headless,
        max_steps=max_steps,
        model=model,
    )


TOOLS = [rag_search, run_analytics, record_web_guide, escalate_to_operator, submit_review]

__all__ = ["TOOLS", "execute_code", "rag_search", "run_analytics", "record_web_guide", "escalate_to_operator", "submit_review"]
