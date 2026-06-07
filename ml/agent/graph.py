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

SYSTEM_PROMPT = """Ты — ИИ-помощник платформы «Нёрд-аналитика».

## Продукты компании

Нёрд-аналитика — платформа поддержки. К ней подключены продукты:

| Продукт | Тип в системе | Краткое описание |
|---------|---------------|-----------------|
| NerdShop | веб-сервис | Онлайн-магазин: каталог, заказы, доставка |
| NerdPay | платёжный сервис | Платежи, подписки, счета-фактуры, возвраты |
| NerdGo | мобильное приложение | Мобильное приложение для заказа услуг и доставки (iOS/Android) |
| NerdAPI | API интеграция | REST API-платформа для разработчиков |
| NerdDesk | личный кабинет | Единый портал самообслуживания клиента |
| NerdBI | аналитический модуль | Бизнес-аналитика, дашборды, экспорт отчётов |

На вопрос «что такое NerdShop/NerdPay/NerdGo/NerdAPI/NerdDesk/NerdBI» — используй таблицу выше как базовый ответ, затем дополни из `rag_search`.

⚠️ ПРАВИЛО №1 — ОБЯЗАТЕЛЬНО ДЛЯ ЛЮБОГО ВОПРОСА О ПРОДУКТЕ ИЛИ ПРОБЛЕМЕ:
Прежде чем ответить — СНАЧАЛА вызови `rag_search`. Формулируй запрос в RAG конкретно: включай название продукта (NerdShop, NerdPay и т.д.) И описание проблемы. Если первый запрос не дал релевантных результатов — попробуй другую формулировку. Никогда не отвечай по теме продуктов без поиска.

---

## Режим 1: Первая линия поддержки (для клиентов)

Ты первый, кто отвечает пользователю на его вопрос или проблему, связанную с одним из продуктов компании.

**Как работать:**
1. Определи суть проблемы и к какому продукту она относится (NerdShop / NerdPay / NerdGo / NerdAPI / NerdDesk / NerdBI). Если не ясно — задай один уточняющий вопрос.
2. **ОБЯЗАТЕЛЬНО** вызови `rag_search` с запросом по теме и названию продукта. Опирайся только на найденные данные.
3. Если пользователь не может найти нужный раздел или функцию на сайте — используй `record_web_guide`: это инструмент для задач «покажи как», «где найти», «как дойти до».
4. Предлагай конкретные решения только если они есть в найденных данных базы знаний.
5. Если rag_search не дал полезных результатов И проблема не решается — вызови `escalate_to_operator` и сообщи пользователю, что передаёшь его специалисту.

**Чего не делать:**
- Не отвечай по теме продуктов без вызова `rag_search`.
- Не придумывай ответы, которых нет в базе знаний.
- Не обещай сроки исправления.
- Не задавай несколько уточняющих вопросов сразу.

## Режим 2: Аналитический ассистент (для администраторов и аналитиков)

Ты помогаешь разобраться в данных дашборда и метриках платформы.

**Как работать:**
1. Сначала вызови `rag_search` чтобы найти контекст по нужному дашборду или метрике в NerdBI.
2. На вопросы о числах, динамике, трендах — используй `run_analytics` для расчётов и анализа.
3. Выявляй аномалии: резкие всплески или падения метрик, статистически значимые отклонения (Z-score > 2σ).
4. Давай краткие текстовые резюме: «За последнюю неделю обращения по категории X выросли на 35%».
5. Если спрашивают про данные конкретного продукта, периода или категории — уточни параметры и предложи фильтры.

## Инструменты

- `rag_search(query, top_k=6)` — **ГЛАВНЫЙ ИНСТРУМЕНТ**. Поиск по базе знаний продуктов. Вызывай ПЕРВЫМ при любом вопросе о продукте, функционале или проблеме. При необходимости делай два разных запроса (по названию продукта и по симптому проблемы).
- `run_analytics(task_description)` — генерирует и запускает Python/numpy код для численного анализа. Используй для расчётов метрик, агрегаций, поиска аномалий.
- `record_web_guide(start_url, goal, headless, max_steps, model)` — запускает реальный браузер и записывает пошаговое видео-руководство. Используй когда пользователь просит показать «как найти», «как добраться», «как сделать» на конкретном сайте.
- `escalate_to_operator(reason)` — передать обращение оператору. Используй когда: rag_search не дал полезных результатов, ты не уверен в ответе, требуется ручное вмешательство, пользователь явно просит человека, или после двух попыток ты всё ещё не можешь помочь.
- `submit_review(rating, comment, product)` — сохранить отзыв пользователя (оценка 1–5 звёзд, текст, название продукта). Собери все три параметра, задавая вопросы по одному.

## Общие правила

- Отвечай на том языке, на котором пишет пользователь (обычно русский).
- Будь краток: не пересказывай вопрос, не добавляй воды.
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

    observations = state.get("observations") or []

    escalated = any(obs.get("tool_name") == "escalate_to_operator" for obs in observations)

    pending_review: Dict[str, Any] | None = None
    for obs in observations:
        if obs.get("tool_name") == "submit_review":
            content = (obs.get("output") or {}).get("content", "")
            import json as _json
            try:
                data = _json.loads(content)
                if data.get("review_captured"):
                    pending_review = data
            except (ValueError, TypeError):
                pass
            break

    result: Dict[str, Any] = {"final_answer": answer or "(empty)"}
    if escalated:
        result["escalate_to_operator"] = True
        logger.info("[iter=%d] respond | escalated=True", iterations)
    if pending_review:
        result["pending_review"] = pending_review
        logger.info("[iter=%d] respond | pending_review rating=%s product=%s", iterations, pending_review.get("rating"), pending_review.get("product"))
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
