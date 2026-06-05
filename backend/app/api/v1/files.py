"""Раздача локально сохранённых файлов (когда S3 не настроен)."""

from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from backend.app.config import get_settings

router = APIRouter(prefix="/files", tags=["files"])


@router.get("/local/{file_path:path}")
async def serve_local_file(file_path: str):
    settings = get_settings()
    if settings.s3_configured:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Local file serving disabled when S3 is configured",
        )
    root = Path(settings.LOCAL_UPLOAD_DIR).resolve()
    target = (root / file_path).resolve()
    if not str(target).startswith(str(root)) or not target.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return FileResponse(target)
