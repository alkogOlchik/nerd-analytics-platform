"""FastAPI service wrapper for the LangGraph agent.

Supports both synchronous query execution and background jobs for long tasks.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from agent.graph import graph
from agent.tools.web_guide_tool import (
    DEFAULT_TIMEOUT_SECONDS,
    record_web_guide as record_web_guide_tool,
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Project LLM Agent API")

_JOBS: Dict[str, Dict[str, Any]] = {}
_JOBS_LOCK = asyncio.Lock()


class LlmModel(str, Enum):
    GEMMA4_E4B = "gemma4:e4b"
    GEMMA4_E2B = "gemma4:e2b"


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User query")
    model: LlmModel = Field(
        LlmModel.GEMMA4_E4B,
        description="LLM model to use for this request",
    )


class RecordWebGuideRequest(BaseModel):
    url: str = Field(..., min_length=1, description="Start URL")
    goal: str = Field(..., min_length=1, description="Navigation goal")
    model: LlmModel = Field(
        LlmModel.GEMMA4_E4B,
        description="VLM/LLM model to use for this recording request",
    )
    headless: bool = Field(False, description="Run browser in headless mode")
    max_steps: int = Field(30, ge=1, le=200)
    timeout_seconds: int = Field(DEFAULT_TIMEOUT_SECONDS, ge=30, le=3600)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _set_job(job_id: str, **fields: Any) -> None:
    async with _JOBS_LOCK:
        _JOBS.setdefault(job_id, {}).update(fields)


async def _get_job_or_404(job_id: str) -> Dict[str, Any]:
    async with _JOBS_LOCK:
        job = _JOBS.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return dict(job)


async def _run_query(query: str, model: LlmModel) -> Dict[str, Any]:
    logger.info("query | start | chars=%d model=%s", len(query), model.value)
    initial = {
        "messages": [HumanMessage(content=query)],
        "llm_model_override": model.value,
    }
    result = await graph.ainvoke(initial)
    answer = result.get("final_answer") or "(no answer)"
    iterations = int(result.get("iterations") or 0)
    observations = len(result.get("observations") or [])
    logger.info(
        "query | done | iterations=%d observations=%d answer_chars=%d",
        iterations,
        observations,
        len(answer),
    )
    return {
        "answer": answer,
        "model": model.value,
        "iterations": iterations,
        "observations_count": observations,
    }


async def _run_web_guide(req: RecordWebGuideRequest) -> Dict[str, Any]:
    logger.info(
        "web_guide | start | url=%s max_steps=%d headless=%s",
        req.url,
        req.max_steps,
        req.headless,
    )
    result = await record_web_guide_tool(
        start_url=req.url,
        goal=req.goal,
        headless=req.headless,
        max_steps=req.max_steps,
        timeout_seconds=req.timeout_seconds,
        model=req.model.value,
    )
    if result.get("error"):
        logger.error("web_guide | error=%s", result["error"])
        raise RuntimeError(str(result["error"]))
    logger.info(
        "web_guide | done | guide=%s video=%s",
        result.get("guide_path", ""),
        result.get("video_path", ""),
    )
    return result


async def _run_query_job(job_id: str, query: str, model: LlmModel) -> None:
    await _set_job(job_id, status="running", started_at=_now_iso())
    try:
        payload = await _run_query(query, model)
        await _set_job(
            job_id,
            status="done",
            finished_at=_now_iso(),
            result=payload,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Job %s failed", job_id)
        await _set_job(
            job_id,
            status="failed",
            finished_at=_now_iso(),
            error=f"{type(exc).__name__}: {exc}",
        )


async def _run_web_guide_job(job_id: str, req: RecordWebGuideRequest) -> None:
    await _set_job(job_id, status="running", started_at=_now_iso())
    try:
        payload = await _run_web_guide(req)
        await _set_job(
            job_id,
            status="done",
            finished_at=_now_iso(),
            result=payload,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Web-guide job %s failed", job_id)
        await _set_job(
            job_id,
            status="failed",
            finished_at=_now_iso(),
            error=f"{type(exc).__name__}: {exc}",
        )


def _job_result_path(job: Dict[str, Any], key: str) -> Path:
    result = job.get("result")
    if not isinstance(result, dict):
        raise HTTPException(status_code=409, detail="Job has no result payload")
    value = result.get(key)
    if not value:
        raise HTTPException(status_code=404, detail=f"No '{key}' artifact for this job")
    path = Path(str(value)).expanduser().resolve()
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail=f"Artifact not found on disk: {path}")
    return path


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/query")
async def query(req: QueryRequest) -> Dict[str, Any]:
    return await _run_query(req.query, req.model)


@app.post("/jobs")
async def create_job(
    req: QueryRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, str]:
    job_id = str(uuid.uuid4())
    await _set_job(
        job_id,
        status="queued",
        created_at=_now_iso(),
        kind="query",
        query=req.query,
        model=req.model.value,
    )
    background_tasks.add_task(_run_query_job, job_id, req.query, req.model)
    return {
        "job_id": job_id,
        "status": "queued",
        "status_url": f"/jobs/{job_id}",
    }


@app.post("/record")
async def record_web_guide(
    req: RecordWebGuideRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, str]:
    job_id = str(uuid.uuid4())
    await _set_job(
        job_id,
        status="queued",
        created_at=_now_iso(),
        kind="web_guide",
        url=req.url,
        goal=req.goal,
        model=req.model.value,
    )
    background_tasks.add_task(_run_web_guide_job, job_id, req)
    return {
        "job_id": job_id,
        "status": "queued",
        "status_url": f"/jobs/{job_id}",
        "guide_url": f"/jobs/{job_id}/guide",
        "video_url": f"/jobs/{job_id}/video",
    }


@app.post("/web-guide/jobs")
async def create_web_guide_job(
    req: RecordWebGuideRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, str]:
    return await record_web_guide(req, background_tasks)


@app.get("/jobs/{job_id}")
async def job_status(job_id: str) -> Dict[str, Any]:
    job = await _get_job_or_404(job_id)
    payload: Dict[str, Any] = {"job_id": job_id, **job}
    if job.get("kind") == "web_guide":
        payload["guide_url"] = f"/jobs/{job_id}/guide"
        payload["video_url"] = f"/jobs/{job_id}/video"
    return payload


@app.get("/jobs/{job_id}/guide")
async def download_guide(job_id: str) -> FileResponse:
    job = await _get_job_or_404(job_id)
    if job.get("status") != "done":
        raise HTTPException(status_code=409, detail="Job is not completed yet")
    path = _job_result_path(job, "guide_path")
    return FileResponse(
        str(path),
        media_type="text/markdown; charset=utf-8",
        filename=path.name,
    )


@app.get("/jobs/{job_id}/video")
async def download_video(job_id: str) -> FileResponse:
    job = await _get_job_or_404(job_id)
    if job.get("status") != "done":
        raise HTTPException(status_code=409, detail="Job is not completed yet")
    path = _job_result_path(job, "video_path")
    return FileResponse(str(path), media_type="video/mp4", filename=path.name)
