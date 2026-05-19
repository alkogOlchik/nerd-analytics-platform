"""Analytics tool that generates NumPy code and executes it safely."""

from __future__ import annotations

import re
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage

from agent.llm import get_llm
from agent.tools.code_executor import execute_code


ANALYTICS_SYSTEM_PROMPT = """You are a senior Python data analyst.
Generate ONLY executable Python code for the task below.

Rules:
- Allowed imports: numpy, math, statistics, json, datetime
- Do not use files, network, subprocesses, or external packages.
- Print the final result to stdout.
- Keep code concise and deterministic.
- If assumptions are needed, encode them in the code and still produce output.
"""


def _extract_python_code(text: str) -> str:
    """Extract Python code from markdown fence or return raw text."""
    fence_match = re.search(r"```(?:python)?\s*(.*?)```", text, flags=re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()
    return text.strip()


def run_analytics(task_description: str) -> Dict[str, Any]:
    """Generate NumPy-based analysis code and execute it."""
    if not task_description or not task_description.strip():
        return {
            "ok": False,
            "tool_name": "run_analytics",
            "task_description": task_description,
            "error": "Task description is empty.",
        }

    try:
        llm = get_llm()
        messages = [
            SystemMessage(content=ANALYTICS_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    "Write Python code for this analytics task:\n"
                    f"{task_description.strip()}"
                )
            ),
        ]
        llm_response = llm.invoke(messages)
        raw_content = llm_response.content
        if isinstance(raw_content, list):
            raw_text = "\n".join(str(chunk) for chunk in raw_content)
        else:
            raw_text = str(raw_content)

        generated_code = _extract_python_code(raw_text)
        execution_result = execute_code(generated_code)

        return {
            "ok": bool(execution_result.get("ok", False)),
            "tool_name": "run_analytics",
            "task_description": task_description,
            "generated_code": generated_code,
            "execution_result": execution_result,
            "summary": (
                "Analytics code executed successfully."
                if execution_result.get("ok")
                else "Analytics code execution failed."
            ),
        }
    except Exception as err:
        return {
            "ok": False,
            "tool_name": "run_analytics",
            "task_description": task_description,
            "error_type": type(err).__name__,
            "error": str(err),
        }

