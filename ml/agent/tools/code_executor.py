"""Safe Python code execution utility for analytics tooling.

Executes user/LLM-generated code in a subprocess with a timeout and
restricted import policy.
"""

from __future__ import annotations

import ast
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from agent.config import settings


ALLOWED_IMPORTS = {"numpy", "math", "statistics", "json", "datetime"}


@dataclass(frozen=True)
class CodeExecutionResult:
    """Structured execution result returned to the agent/tools."""

    ok: bool
    stdout: str
    stderr: str
    return_code: int
    timed_out: bool = False
    error_type: str | None = None
    error_message: str | None = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "ok": self.ok,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "return_code": self.return_code,
            "timed_out": self.timed_out,
            "error_type": self.error_type,
            "error_message": self.error_message,
        }


def _truncate(text: str) -> str:
    """Trim long outputs to keep state compact and stable."""
    if len(text) <= settings.code_execution_max_output_chars:
        return text
    tail = "\n...[truncated]..."
    return text[: settings.code_execution_max_output_chars] + tail


def _validate_imports(code: str) -> List[str]:
    """Return a list of forbidden imported modules found in code."""
    forbidden: List[str] = []
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root not in ALLOWED_IMPORTS:
                    forbidden.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                forbidden.append("<relative-import>")
                continue
            root = node.module.split(".")[0]
            if root not in ALLOWED_IMPORTS:
                forbidden.append(node.module)
    return forbidden


def execute_code(code: str) -> Dict[str, object]:
    """Execute Python code with import checks and timeout protection."""
    try:
        forbidden = _validate_imports(code)
    except SyntaxError as err:
        result = CodeExecutionResult(
            ok=False,
            stdout="",
            stderr=str(err),
            return_code=1,
            error_type="SyntaxError",
            error_message=f"Invalid Python syntax: {err}",
        )
        return result.to_dict()

    if forbidden:
        result = CodeExecutionResult(
            ok=False,
            stdout="",
            stderr=f"Forbidden imports: {', '.join(sorted(set(forbidden)))}",
            return_code=1,
            error_type="ImportValidationError",
            error_message="Only numpy, math, statistics, json, datetime are allowed.",
        )
        return result.to_dict()

    with tempfile.TemporaryDirectory(prefix="agent_exec_") as tmp_dir:
        script_path = Path(tmp_dir) / "script.py"
        script_path.write_text(code, encoding="utf-8")

        try:
            completed = subprocess.run(
                [settings.code_execution_python_bin, str(script_path)],
                capture_output=True,
                text=True,
                timeout=settings.code_execution_timeout_seconds,
                check=False,
                cwd=tmp_dir,
            )
            result = CodeExecutionResult(
                ok=completed.returncode == 0,
                stdout=_truncate(completed.stdout or ""),
                stderr=_truncate(completed.stderr or ""),
                return_code=completed.returncode,
            )
            return result.to_dict()
        except subprocess.TimeoutExpired as err:
            stdout = _truncate((err.stdout or "") if isinstance(err.stdout, str) else "")
            stderr = _truncate((err.stderr or "") if isinstance(err.stderr, str) else "")
            result = CodeExecutionResult(
                ok=False,
                stdout=stdout,
                stderr=stderr,
                return_code=124,
                timed_out=True,
                error_type="TimeoutExpired",
                error_message=(
                    f"Code execution exceeded {settings.code_execution_timeout_seconds}s timeout."
                ),
            )
            return result.to_dict()
        except Exception as err:  # defensive guard so the graph never crashes
            result = CodeExecutionResult(
                ok=False,
                stdout="",
                stderr=str(err),
                return_code=1,
                error_type=type(err).__name__,
                error_message=f"Execution failure: {err}",
            )
            return result.to_dict()
