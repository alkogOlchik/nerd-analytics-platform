"""FastAPI service wrapper for the LangGraph agent.

Supports both synchronous query execution and background jobs for long tasks.
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from agent.graph import graph
from agent.tools.rag_index import DEFAULT_SOURCE, SUPPORTED_EXTS, index_directory
from agent.tools.rag_tool import (
    rag_search as rag_search_impl,
    rag_status,
    reset_collection,
)
from agent.tools.web_guide_tool import (
    DEFAULT_TIMEOUT_SECONDS,
    RECORDER_DIR,
    record_web_guide as record_web_guide_tool,
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Project LLM Agent API")

VIDEOS_DIR = RECORDER_DIR / "output" / "videos"

# ML service base URL — used to build video_url returned to clients.
# Override via ML_SERVICE_BASE_URL env var if not running on localhost:8091.
import os as _os
_ML_BASE_URL = _os.environ.get("ML_SERVICE_BASE_URL", "http://localhost:8091")

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
    response: Dict[str, Any] = {
        "answer": answer,
        "model": model.value,
        "iterations": iterations,
        "observations_count": observations,
    }
    if result.get("escalate_to_operator"):
        response["escalate_to_operator"] = True
    if result.get("pending_review"):
        response["pending_review"] = result["pending_review"]
    if result.get("video_path"):
        video_filename = Path(str(result["video_path"])).name
        response["video_url"] = f"{_ML_BASE_URL}/videos/{video_filename}"
        logger.info("query | video_url=%s", response["video_url"])
    return response


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


@app.get("/videos/{filename}")
async def serve_video(filename: str) -> FileResponse:
    """Serve a recorded guide video by filename."""
    # Prevent path traversal: only allow the bare filename, no slashes.
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    path = VIDEOS_DIR / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail=f"Video not found: {filename}")
    return FileResponse(
        str(path),
        media_type="video/mp4",
        filename=filename,
        headers={"Accept-Ranges": "bytes"},
    )


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


# ---------------------------------------------------------------------------
# RAG knowledge base management
# ---------------------------------------------------------------------------

_SAFE_NAME_RE = re.compile(r"[^A-Za-zА-Яа-я0-9._\- ]+")


def _safe_filename(raw: str, default_ext: str = ".md") -> str:
    """Sanitize an arbitrary user-supplied filename. Never returns empty,
    never lets the caller escape the docs directory."""
    name = Path(raw).name.strip()
    name = _SAFE_NAME_RE.sub("_", name)
    if not name:
        name = f"doc_{int(time.time())}{default_ext}"
    suffix = Path(name).suffix.lower()
    if suffix not in SUPPORTED_EXTS:
        name = f"{Path(name).stem or 'doc'}{default_ext}"
    return name


def _unique_path(base_dir: Path, filename: str) -> Path:
    candidate = base_dir / filename
    if not candidate.exists():
        return candidate
    stem = candidate.stem
    suffix = candidate.suffix
    ts = int(time.time())
    return base_dir / f"{stem}_{ts}{suffix}"


class IngestTextRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="File name to save under docs/")
    content: str = Field(..., min_length=1, description="Document body (plain text or markdown)")


class RagSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(4, ge=1, le=50)


async def _index_path(path: Path, *, reset: bool = False) -> Dict[str, Any]:
    """Run index_directory in a worker thread — embedding calls are blocking."""
    return await asyncio.to_thread(index_directory, path, reset=reset)


@app.get("/rag/status")
async def get_rag_status() -> Dict[str, Any]:
    return rag_status()


@app.post("/rag/search")
async def search_rag(req: RagSearchRequest) -> Dict[str, Any]:
    return await asyncio.to_thread(rag_search_impl, req.query, req.top_k)


@app.post("/rag/documents", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    reset: bool = Form(False),
) -> Dict[str, Any]:
    """Upload a single file (md/txt/rst) and index it.

    `reset=true` drops the existing collection before indexing.
    """
    docs_dir: Path = DEFAULT_SOURCE
    docs_dir.mkdir(parents=True, exist_ok=True)

    raw_name = file.filename or f"upload_{int(time.time())}.md"
    raw_suffix = Path(raw_name).suffix.lower()
    if raw_suffix not in SUPPORTED_EXTS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported extension {raw_suffix!r}. Allowed: {sorted(SUPPORTED_EXTS)}",
        )
    safe_name = _safe_filename(raw_name, default_ext=raw_suffix)

    target = _unique_path(docs_dir, safe_name)
    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    await asyncio.to_thread(target.write_bytes, payload)

    result = await _index_path(target, reset=reset)
    if not result.get("ok"):
        raise HTTPException(status_code=500, detail=result)
    return {
        "saved_to": str(target),
        "size_bytes": len(payload),
        "index": result,
    }


@app.post("/rag/documents/text", status_code=201)
async def upload_text_document(req: IngestTextRequest) -> Dict[str, Any]:
    """Save an inline document as a file and index it. Convenient for JSON clients
    that don't want to deal with multipart uploads."""
    docs_dir: Path = DEFAULT_SOURCE
    docs_dir.mkdir(parents=True, exist_ok=True)

    safe_name = _safe_filename(req.name)
    target = _unique_path(docs_dir, safe_name)
    await asyncio.to_thread(target.write_text, req.content, "utf-8")

    result = await _index_path(target)
    if not result.get("ok"):
        raise HTTPException(status_code=500, detail=result)
    return {
        "saved_to": str(target),
        "size_bytes": len(req.content.encode("utf-8")),
        "index": result,
    }


@app.post("/rag/reindex")
async def reindex_rag(
    reset: bool = False,
    source: Optional[str] = None,
) -> Dict[str, Any]:
    """Reindex an entire directory. Defaults to ml/docs/.

    Use `?reset=true` to drop the collection first (full rebuild)."""
    src_path = Path(source).expanduser() if source else DEFAULT_SOURCE
    if not src_path.exists():
        raise HTTPException(status_code=404, detail=f"Source path not found: {src_path}")
    result = await _index_path(src_path, reset=reset)
    if not result.get("ok"):
        raise HTTPException(status_code=500, detail=result)
    return result


@app.delete("/rag/collection")
async def delete_rag_collection() -> Dict[str, Any]:
    result = await asyncio.to_thread(reset_collection)
    if not result.get("ok"):
        raise HTTPException(status_code=500, detail=result)
    return result
