"""Загрузка файлов в S3 (или MinIO) с локальным fallback для разработки."""

from __future__ import annotations

import mimetypes
import uuid
from dataclasses import dataclass
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from fastapi import HTTPException, status

from backend.app.config import Settings, get_settings

ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
        "application/pdf",
    }
)

EXTENSION_BY_TYPE: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "application/pdf": ".pdf",
}


@dataclass(frozen=True)
class StoredFile:
    file_url: str
    file_type: str
    file_name: str
    size_bytes: int


def _guess_content_type(filename: str, content_type: str | None) -> str:
    if content_type and content_type.split(";")[0].strip().lower() in ALLOWED_CONTENT_TYPES:
        return content_type.split(";")[0].strip().lower()
    guessed, _ = mimetypes.guess_type(filename)
    if guessed and guessed in ALLOWED_CONTENT_TYPES:
        return guessed
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unsupported file type. Allowed: JPEG, PNG, WebP, GIF, PDF",
    )


def _extension_for(content_type: str, filename: str) -> str:
    ext = EXTENSION_BY_TYPE.get(content_type)
    if ext:
        return ext
    path_ext = Path(filename).suffix.lower()
    if path_ext in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".pdf"}:
        return path_ext if path_ext != ".jpeg" else ".jpg"
    return ".bin"


def _s3_client(settings: Settings):
    kwargs: dict = {
        "service_name": "s3",
        "aws_access_key_id": settings.S3_ACCESS_KEY_ID,
        "aws_secret_access_key": settings.S3_SECRET_ACCESS_KEY,
        "region_name": settings.S3_REGION,
        "config": Config(signature_version="s3v4"),
    }
    if settings.S3_ENDPOINT_URL:
        kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL
    return boto3.client(**kwargs)


def _build_public_url(settings: Settings, object_key: str) -> str:
    if settings.S3_PUBLIC_URL_PREFIX:
        return f"{settings.S3_PUBLIC_URL_PREFIX.rstrip('/')}/{object_key}"
    if settings.S3_ENDPOINT_URL:
        base = settings.S3_ENDPOINT_URL.rstrip("/")
        return f"{base}/{settings.S3_BUCKET_NAME}/{object_key}"
    return f"https://{settings.S3_BUCKET_NAME}.s3.{settings.S3_REGION}.amazonaws.com/{object_key}"


def _local_public_url(settings: Settings, relative_key: str) -> str:
    base = settings.APP_SERVICE_URL.rstrip("/")
    return f"{base}/files/local/{relative_key}"


def _validate_size(settings: Settings, size: int) -> None:
    if size <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")
    if size > settings.FILE_UPLOAD_MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large (max {settings.FILE_UPLOAD_MAX_BYTES} bytes)",
        )


def assert_file_url_owned_by_client(settings: Settings, client_id: uuid.UUID, file_url: str) -> None:
    """URL должен указывать на объект, загруженный этим клиентом."""
    marker = f"/{client_id}/"
    local_prefix = _local_public_url(settings, "").rstrip("/") + "/"
    if file_url.startswith(local_prefix) and marker in file_url:
        return
    if settings.s3_configured:
        public_base = _build_public_url(settings, "").rstrip("/") + "/"
        custom = (settings.S3_PUBLIC_URL_PREFIX or "").rstrip("/") + "/"
        if (file_url.startswith(public_base) or (custom and file_url.startswith(custom))) and marker in file_url:
            return
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid attachment URL",
    )


def upload_bytes(
    *,
    client_id: uuid.UUID,
    filename: str,
    content: bytes,
    content_type: str | None = None,
    settings: Settings | None = None,
) -> StoredFile:
    settings = settings or get_settings()
    resolved_type = _guess_content_type(filename, content_type)
    _validate_size(settings, len(content))

    safe_name = Path(filename).name or "file"
    ext = _extension_for(resolved_type, safe_name)
    object_id = uuid.uuid4()
    relative_key = f"{settings.S3_PREFIX.strip('/')}/{client_id}/{object_id}{ext}"

    if settings.s3_configured:
        client = _s3_client(settings)
        try:
            client.put_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=relative_key,
                Body=content,
                ContentType=resolved_type,
            )
        except ClientError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="S3 upload failed",
            ) from exc
        file_url = _build_public_url(settings, relative_key)
    else:
        root = Path(settings.LOCAL_UPLOAD_DIR)
        dest = root / relative_key
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        file_url = _local_public_url(settings, relative_key)

    return StoredFile(
        file_url=file_url,
        file_type=resolved_type,
        file_name=safe_name,
        size_bytes=len(content),
    )
