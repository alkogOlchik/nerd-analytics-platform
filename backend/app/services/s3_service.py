"""Async S3/MinIO wrapper using aioboto3."""

import uuid
from pathlib import PurePosixPath

import aioboto3
from botocore.exceptions import ClientError
from fastapi import HTTPException, status

from backend.app.config import get_settings

_session = aioboto3.Session()


def _make_key(client_id: uuid.UUID, filename: str) -> str:
    safe = PurePosixPath(filename).name or "file"
    return f"{client_id}/{uuid.uuid4()}/{safe}"


def _get_client():
    settings = get_settings()
    return _session.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
    )


async def _ensure_bucket(client, bucket: str) -> None:
    try:
        await client.head_bucket(Bucket=bucket)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ("404", "NoSuchBucket"):
            await client.create_bucket(Bucket=bucket)
        else:
            raise


async def upload_file(client_id: uuid.UUID, filename: str, data: bytes, content_type: str) -> str:
    settings = get_settings()
    key = _make_key(client_id, filename)
    async with _get_client() as s3:
        await _ensure_bucket(s3, settings.S3_BUCKET_NAME)
        await s3.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
    return key


async def download_file(key: str) -> bytes:
    settings = get_settings()
    try:
        async with _get_client() as s3:
            response = await s3.get_object(Bucket=settings.S3_BUCKET_NAME, Key=key)
            return await response["Body"].read()
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ("404", "NoSuchKey"):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"File not found in storage: {key}",
            )
        raise


async def delete_file(key: str) -> None:
    settings = get_settings()
    async with _get_client() as s3:
        await s3.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=key)
