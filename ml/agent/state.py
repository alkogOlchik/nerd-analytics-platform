"""Types for LangGraph agent state."""

from __future__ import annotations

from operator import add
from typing import Annotated, Any, Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage


class Observation(TypedDict, total=False):
    """Single observation entry captured after tool/action execution."""

    step: str
    tool_name: str
    input: Dict[str, Any]
    output: Dict[str, Any]
    error: str


class AgentState(TypedDict, total=False):
    """Shared state passed between LangGraph nodes.

    `messages` and `observations` use the `add` reducer so nodes can return
    deltas (e.g. a single AIMessage) instead of the full list.
    """

    messages: Annotated[List[BaseMessage], add]
    observations: Annotated[List[Observation], add]
    iterations: int
    llm_model_override: Optional[str]
    final_answer: Optional[str]
    escalate_to_operator: Optional[bool]
    pending_review: Optional[Dict[str, Any]]
