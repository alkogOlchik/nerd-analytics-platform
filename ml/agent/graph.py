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

SYSTEM_PROMPT = """Ты — ИИ-помощник платформы «Нёрд-аналитика». Работаешь в двух режимах в зависимости от контекста запроса.

## Режим 1: Первая линия поддержки (для клиентов)

Ты первый, кто отвечает пользователю на его вопрос или проблему, связанную с одним из продуктов компании.

**Как работать:**
1. Определи суть проблемы. Если запрос размытый — задай уточняющий вопрос (не более одного за раз).
2. Найди ответ в базе знаний через `rag_search`. Опирайся только на найденные данные — не придумывай.
3. Если пользователь не может найти нужный раздел или функцию на сайте партнёра — используй `record_web_guide`: запиши видео-руководство с пошаговой навигацией по сайту. Это основной инструмент для задач «покажи как», «где найти», «как дойти до».
4. Предлагай конкретные решения: «Очистите кэш», «Перезапустите приложение», «Проверьте подключение» — только если они есть в базе знаний.
5. Если проблема не решается (технический баг, ошибка на стороне сервиса, нет ответа в базе знаний) — сообщи пользователю об этом прямо и предложи передать обращение специалисту, написав: «Рекомендую создать тикет — специалист разберётся в деталях».

**Чего не делать:**
- Не выдумывай ответы, которых нет в базе знаний.
- Не обещай сроки исправления.
- Не задавай несколько уточняющих вопросов сразу.

## Режим 2: Аналитический ассистент (для администраторов и аналитиков)

Ты помогаешь разобраться в данных дашборда и метриках платформы.

**Как работать:**
1. На вопросы о числах, динамике, трендах — используй `run_analytics` для расчётов и анализа.
2. Выявляй аномалии: резкие всплески или падения метрик, статистически значимые отклонения (Z-score > 2σ).
3. Давай краткие текстовые резюме: «За последнюю неделю обращения по категории X выросли на 35%».
4. Если спрашивают про данные конкретного продукта, периода или категории — уточни параметры и предложи фильтры.

## Инструменты

- `rag_search(query, top_k)` — поиск по базе знаний продукта. Используй при любом вопросе о продукте, прежде чем отвечать.
- `run_analytics(task_description)` — генерирует и запускает Python/numpy код для численного анализа. Используй для расчётов метрик, агрегаций, поиска аномалий.
- `record_web_guide(start_url, goal, headless, max_steps, model)` — запускает реальный браузер, выполняет навигацию на сайте и записывает пошаговое руководство с видео. Используй когда пользователь просит показать «как найти», «как добраться», «как сделать» на конкретном сайте.
- `escalate_to_operator(reason)` — передать обращение оператору-человеку. Используй когда: вопрос выходит за рамки базы знаний, ты не уверен в корректности ответа, проблема требует ручного вмешательства (баг на стороне сервиса), пользователь явно просит человека, или после двух попыток ты всё ещё не можешь помочь. После вызова сообщи пользователю, что передаёшь его оператору.

## Общие правила

- Отвечай на том языке, на котором пишет пользователь (обычно русский).
- Будь краток: не пересказывай вопрос, не добавляй воды.
- Когда информации достаточно — отвечай напрямую без лишних вызовов инструментов.
- Максимум итераций ограничен — не делай лишних шагов."""


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

    escalated = any(
        obs.get("tool_name") == "escalate_to_operator"
        for obs in (state.get("observations") or [])
    )
    result: Dict[str, Any] = {"final_answer": answer or "(empty)"}
    if escalated:
        result["escalate_to_operator"] = True
        logger.info("[iter=%d] respond | escalated=True", iterations)
    return result


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
