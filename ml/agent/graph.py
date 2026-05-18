"""LangGraph ReAct graph: reason → act → reason → … → respond.

The reason node decides (via tool-calling) whether to invoke a tool or
answer directly. Tool errors are captured into `observations` and a
ToolMessage so they flow back into the next reason step instead of
crashing the graph.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from agent.llm import get_llm
from agent.state import AgentState, Observation
from agent.tools import TOOLS

logger = logging.getLogger(__name__)

MAX_REASONING_ITERATIONS = 10

SYSTEM_PROMPT = """You are a ReAct agent that solves user tasks step by step.

Available tools:
- rag_search(query, top_k): search the local knowledge base for relevant text.
- run_analytics(task_description): generate and execute Python (numpy) code
  for numerical analysis. Returns stdout of the code.
- record_web_guide(start_url, goal, headless=False, max_steps=30, model=None): drive a real
  browser to a goal on a website (open page, search, click, fill forms) and
  produce a step-by-step markdown guide with screenshots and a voice-guided
  walkthrough video. Use this whenever
  the user asks to "open a site", "search on Google/Yandex", "go to a URL",
  or otherwise interact with the web. Returns guide path, video path and preview.

Decide at each step whether to call a tool or to answer directly.
When you have enough information, produce the final answer with no tool calls.
Be concise."""


def _shorten(text: str, limit: int = 500) -> str:
    """Trim long strings for log output."""
    if text is None:
        return ""
    s = str(text).replace("\n", " ")
    return s if len(s) <= limit else s[:limit] + f"…[+{len(s)-limit} chars]"


def _format_tool_calls(tool_calls: List[Dict[str, Any]] | None) -> str:
    if not tool_calls:
        return "(none)"
    parts = []
    for tc in tool_calls:
        name = tc.get("name", "?")
        args = tc.get("args", {})
        parts.append(f"{name}({_shorten(args, 300)})")
    return "; ".join(parts)


def _ensure_system_prompt(messages: List[BaseMessage]) -> List[BaseMessage]:
    if messages and isinstance(messages[0], SystemMessage):
        return messages
    return [SystemMessage(content=SYSTEM_PROMPT), *messages]


async def reason_node(state: AgentState) -> Dict[str, Any]:
    """LLM step: decide tool call or final answer."""
    messages = _ensure_system_prompt(list(state.get("messages") or []))
    iterations = (state.get("iterations") or 0) + 1
    model_override = state.get("llm_model_override")

    logger.info(
        "[iter=%d] reason | start | history_len=%d model=%s",
        iterations,
        len(messages),
        model_override or "default",
    )

    try:
        llm = get_llm(model=model_override).bind_tools(TOOLS)
        response = await llm.ainvoke(messages)
    except Exception as exc:  # noqa: BLE001 — any LLM error becomes an observation
        logger.exception("[iter=%d] reason | llm error: %s", iterations, exc)
        obs: Observation = {
            "step": "reason",
            "tool_name": "_llm",
            "input": {},
            "output": {},
            "error": f"{type(exc).__name__}: {exc}",
        }
        return {
            "messages": [AIMessage(content="Reasoning failed; returning best-effort answer.")],
            "observations": [obs],
            "iterations": iterations,
        }

    raw_content = response.content if isinstance(response.content, str) else str(response.content)
    tool_calls = getattr(response, "tool_calls", None) or []
    logger.info(
        "[iter=%d] reason | content=%s",
        iterations,
        _shorten(raw_content, 800),
    )
    logger.info(
        "[iter=%d] reason | tool_calls=%s",
        iterations,
        _format_tool_calls(tool_calls),
    )

    return {"messages": [response], "iterations": iterations}


_tool_node = ToolNode(TOOLS)


async def act_node(state: AgentState) -> Dict[str, Any]:
    """Execute pending tool calls. Errors are captured, not raised."""
    iterations = state.get("iterations") or 0
    model_override = state.get("llm_model_override")
    last_msg = (state.get("messages") or [None])[-1]
    pending = getattr(last_msg, "tool_calls", None) or []
    if model_override:
        for tc in pending:
            if tc.get("name") != "record_web_guide":
                continue
            args = tc.get("args")
            if not isinstance(args, dict):
                continue
            if "model" not in args:
                args["model"] = model_override
                logger.info(
                    "[iter=%d] act | injected model=%s into record_web_guide",
                    iterations,
                    model_override,
                )
    for tc in pending:
        logger.info(
            "[iter=%d] act | calling %s args=%s",
            iterations,
            tc.get("name", "?"),
            _shorten(tc.get("args", {}), 500),
        )

    try:
        result = await _tool_node.ainvoke(state)
    except Exception as exc:  # noqa: BLE001 — defensive guard around ToolNode itself
        logger.exception("[iter=%d] act | ToolNode failure: %s", iterations, exc)
        last = (state.get("messages") or [None])[-1]
        tool_call_id = ""
        if isinstance(last, AIMessage) and getattr(last, "tool_calls", None):
            tool_call_id = (last.tool_calls[0] or {}).get("id", "") or ""
        err_msg = ToolMessage(
            content=f"Tool execution failed: {type(exc).__name__}: {exc}",
            tool_call_id=tool_call_id or "unknown",
        )
        return {
            "messages": [err_msg],
            "observations": [
                {
                    "step": "act",
                    "tool_name": "unknown",
                    "input": {},
                    "output": {},
                    "error": f"{type(exc).__name__}: {exc}",
                }
            ],
        }

    new_messages = result.get("messages", [])
    observations: List[Observation] = []
    for msg in new_messages:
        if not isinstance(msg, ToolMessage):
            continue
        content = msg.content if isinstance(msg.content, str) else str(msg.content)
        logger.info(
            "[iter=%d] act | %s -> %s",
            iterations,
            msg.name or "?",
            _shorten(content, 800),
        )
        observations.append(
            {
                "step": "act",
                "tool_name": msg.name or "",
                "input": {},
                "output": {"content": content[:2000]},
            }
        )

    delta: Dict[str, Any] = {"messages": new_messages}
    if observations:
        delta["observations"] = observations
    return delta


async def respond_node(state: AgentState) -> Dict[str, Any]:
    """Extract the final answer from the last AI message."""
    iterations = state.get("iterations") or 0
    messages = state.get("messages") or []
    answer = ""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and not getattr(msg, "tool_calls", None):
            content = msg.content
            answer = "\n".join(str(c) for c in content) if isinstance(content, list) else str(content)
            break
    logger.info("[iter=%d] respond | final_answer=%s", iterations, _shorten(answer, 800))
    return {"final_answer": answer or "(empty)"}


def _route_after_reason(state: AgentState) -> str:
    messages = state.get("messages") or []
    if not messages:
        return "respond"
    last = messages[-1]
    has_tool_calls = isinstance(last, AIMessage) and bool(getattr(last, "tool_calls", None))
    if not has_tool_calls:
        return "respond"
    if (state.get("iterations") or 0) >= MAX_REASONING_ITERATIONS:
        logger.warning("Iteration cap reached, forcing respond")
        return "respond"
    return "act"


def build_graph():
    """Build and compile the ReAct graph."""
    builder = StateGraph(AgentState)
    builder.add_node("reason", reason_node)
    builder.add_node("act", act_node)
    builder.add_node("respond", respond_node)

    builder.add_edge(START, "reason")
    builder.add_conditional_edges(
        "reason", _route_after_reason, {"act": "act", "respond": "respond"}
    )
    builder.add_edge("act", "reason")
    builder.add_edge("respond", END)

    return builder.compile()


graph = build_graph()
