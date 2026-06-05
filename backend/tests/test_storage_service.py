import uuid

import pytest
from fastapi import HTTPException

from backend.app.config import Settings
from backend.app.services import storage_service


@pytest.fixture
def local_settings(tmp_path):
    client_id = uuid.uuid4()
    return Settings(
        S3_BUCKET_NAME="",
        APP_SERVICE_URL="http://testserver",
        LOCAL_UPLOAD_DIR=str(tmp_path / "uploads"),
        S3_PREFIX="uploads",
        FILE_UPLOAD_MAX_BYTES=1024 * 1024,
    ), client_id


def test_upload_bytes_local(local_settings):
    settings, client_id = local_settings
    stored = storage_service.upload_bytes(
        client_id=client_id,
        filename="scan.pdf",
        content=b"%PDF-1.4 test",
        content_type="application/pdf",
        settings=settings,
    )
    assert stored.file_type == "application/pdf"
    assert str(client_id) in stored.file_url
    storage_service.assert_file_url_owned_by_client(settings, client_id, stored.file_url)


def test_reject_foreign_url(local_settings):
    settings, client_id = local_settings
    with pytest.raises(HTTPException) as exc:
        storage_service.assert_file_url_owned_by_client(
            settings, client_id, "https://evil.example/uploads/other/file.pdf"
        )
    assert exc.value.status_code == 400


def test_reject_unsupported_type(local_settings):
    settings, client_id = local_settings
    with pytest.raises(HTTPException) as exc:
        storage_service.upload_bytes(
            client_id=client_id,
            filename="virus.exe",
            content=b"MZ",
            content_type="application/octet-stream",
            settings=settings,
        )
    assert exc.value.status_code == 400
