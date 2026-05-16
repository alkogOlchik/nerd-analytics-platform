"""FastAPI wrapper.

Recording can take many minutes, so /record returns a job_id immediately
and the work runs as a BackgroundTask. Poll /jobs/{job_id} for status.

In-memory job registry — fine for a single process; swap for Redis/DB
if multi-worker deployment is needed.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any, Dict

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel

import config
from agent.recorder import GuideRecorder
from guide.exporter import export_html, export_markdown

logger = logging.getLogger(__name__)

app = FastAPI(title="Web Guide Recorder API")

_JOBS: Dict[str, Dict[str, Any]] = {}
_JOBS_LOCK = asyncio.Lock()


class RecordRequest(BaseModel):
    url: str
    goal: str
    fmt: str = "both"
    headless: bool = True
    max_steps: int = config.MAX_STEPS


async def _set_job(job_id: str, **fields: Any) -> None:
    async with _JOBS_LOCK:
        _JOBS.setdefault(job_id, {}).update(fields)


async def _run_job(job_id: str, req: RecordRequest) -> None:
    await _set_job(job_id, status="running")
    try:
        recorder = GuideRecorder(headless=req.headless, max_steps=req.max_steps)
        guide = await recorder.record(start_url=req.url, goal=req.goal)

        outputs: Dict[str, str] = {}
        if req.fmt in ("md", "both"):
            outputs["markdown"] = await export_markdown(guide, str(config.GUIDES_PATH))
        if req.fmt in ("html", "both"):
            outputs["html"] = await export_html(guide, str(config.GUIDES_PATH))

        await _set_job(
            job_id,
            status="done",
            outputs=outputs,
            steps=len(guide.steps),
        )
    except Exception as exc:  # noqa: BLE001 — surface any failure as job state
        logger.exception("Job %s failed", job_id)
        await _set_job(job_id, status="failed", error=f"{type(exc).__name__}: {exc}")


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/record")
async def record(req: RecordRequest, background_tasks: BackgroundTasks) -> Dict[str, str]:
    job_id = str(uuid.uuid4())
    await _set_job(job_id, status="queued")
    background_tasks.add_task(_run_job, job_id, req)
    return {"job_id": job_id, "status": "queued"}


@app.get("/jobs/{job_id}")
async def job_status(job_id: str) -> Dict[str, Any]:
    async with _JOBS_LOCK:
        job = _JOBS.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return {"job_id": job_id, **job}
