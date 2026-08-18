"""Unit and Integration Tests for Storage Adapters (LocalStorageAdapter and DropboxStorageAdapter)."""

import os
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from dropbox.files import FileMetadata, FolderMetadata, WriteMode
from dropbox.exceptions import ApiError, AuthError

from backend.app.services.storage.base import (
    StorageAdapter,
    StorageMetadata,
    StorageStatus,
    StorageNotFoundError,
    StorageAlreadyExistsError,
    StorageAuthError,
    StorageError,
)
from backend.app.services.storage.local import LocalStorageAdapter
from backend.app.services.storage.dropbox_adapter import DropboxStorageAdapter
from backend.app.services.storage import get_storage_adapter


@pytest.fixture
def local_storage(tmp_path) -> LocalStorageAdapter:
    return LocalStorageAdapter(root_dir=str(tmp_path / "storage_root"))


def test_local_storage_lifecycle(local_storage, tmp_path):
    """Test full upload, metadata, list, read_json, download, and overwrite protection."""
    # 1. Create a dummy local source file
    src_file = tmp_path / "sample_ad.png"
    src_file.write_bytes(b"\x89PNG\r\n\x1a\nFakePngData")

    # 2. Upload with overwrite=False
    meta = local_storage.upload(str(src_file), "campaigns/test/sample_ad.png")
    assert meta.path == "campaigns/test/sample_ad.png"
    assert meta.size_bytes == len(b"\x89PNG\r\n\x1a\nFakePngData")
    assert meta.content_hash is not None
    assert meta.is_directory is False

    # 3. Verify exists()
    assert local_storage.exists("campaigns/test/sample_ad.png") is True
    assert local_storage.exists("campaigns/test/non_existent.png") is False

    # 4. Overwrite protection
    with pytest.raises(StorageAlreadyExistsError):
        local_storage.upload(str(src_file), "campaigns/test/sample_ad.png", overwrite=False)

    # 5. Overwrite allowed
    meta_updated = local_storage.upload(str(src_file), "campaigns/test/sample_ad.png", overwrite=True)
    assert meta_updated.path == "campaigns/test/sample_ad.png"

    # 6. JSON Upload & Read
    manifest_data = {
        "campaignId": "yeti-la-go-anywhere-2026",
        "runId": "run-20260818-001",
        "totalAds": 18,
    }
    json_meta = local_storage.upload_json(manifest_data, "campaigns/test/generation-manifest.json")
    assert json_meta.path == "campaigns/test/generation-manifest.json"

    read_back = local_storage.read_json("campaigns/test/generation-manifest.json")
    assert read_back == manifest_data

    # 7. List Directory
    entries = local_storage.list_directory("campaigns/test")
    paths = [e.path for e in entries]
    assert "campaigns/test/generation-manifest.json" in paths
    assert "campaigns/test/sample_ad.png" in paths

    # 8. Download
    dest_download = tmp_path / "downloaded_sample.png"
    downloaded_path = local_storage.download("campaigns/test/sample_ad.png", str(dest_download))
    assert Path(downloaded_path).exists()
    assert Path(downloaded_path).read_bytes() == b"\x89PNG\r\n\x1a\nFakePngData"

    # 9. Status
    status = local_storage.get_status()
    assert status.configured is True
    assert status.reachable is True
    assert status.mode == "local"
    assert status.error is None


def test_dropbox_adapter_path_normalization():
    """Verify Dropbox path normalization enforces single campaign root."""
    adapter = DropboxStorageAdapter(
        access_token="test_token_123",
        campaign_root="/yeti-ad-generator",
    )

    assert adapter.normalize_path("") == "/yeti-ad-generator"
    assert adapter.normalize_path("briefs/test.json") == "/yeti-ad-generator/briefs/test.json"
    assert adapter.normalize_path("/yeti-ad-generator/campaigns/c1/run1") == "/yeti-ad-generator/campaigns/c1/run1"
    assert adapter.normalize_path("yeti-ad-generator/assets/logo.png") == "/yeti-ad-generator/assets/logo.png"


def test_dropbox_adapter_status_unconfigured():
    """Verify unconfigured Dropbox status returns clean non-leaking status."""
    adapter = DropboxStorageAdapter(access_token=None)
    status = adapter.get_status()
    assert status.configured is False
    assert status.reachable is False
    assert status.mode == "dropbox"
    assert "not configured" in status.error.lower()


@patch("dropbox.Dropbox")
def test_dropbox_adapter_mocked_operations(mock_dbx_class, tmp_path):
    """Test DropboxStorageAdapter operations with mocked official Dropbox client."""
    mock_dbx = MagicMock()
    mock_dbx_class.return_value = mock_dbx

    # Mock user account check for status
    mock_dbx.users_get_current_account.return_value = MagicMock(account_id="acc_123")

    adapter = DropboxStorageAdapter(
        access_token="dbx_mock_token_secret",
        campaign_root="/yeti-ad-generator",
        cache_dir=str(tmp_path / "dbx_cache"),
    )

    # 1. Test status
    status = adapter.get_status()
    assert status.configured is True
    assert status.reachable is True
    assert status.mode == "dropbox"
    assert "token" not in json.dumps(status.model_dump())

    # 2. Mock files_get_metadata
    mock_file_meta = MagicMock(spec=FileMetadata)
    mock_file_meta.path_display = "/yeti-ad-generator/campaigns/c1/test-manifest.json"
    mock_file_meta.size = 1024
    mock_file_meta.content_hash = "sha_content_hash_abc123"
    mock_file_meta.rev = "rev_98765"
    mock_file_meta.server_modified = datetime(2026, 8, 18, 12, 0, 0, tzinfo=timezone.utc)
    mock_dbx.files_get_metadata.return_value = mock_file_meta

    meta = adapter.get_metadata("campaigns/c1/test-manifest.json")
    assert meta.path == "campaigns/c1/test-manifest.json"
    assert meta.size_bytes == 1024
    assert meta.revision == "rev_98765"
    assert meta.content_hash == "sha_content_hash_abc123"

    # 3. Test upload_json
    mock_dbx.files_upload.return_value = mock_file_meta
    test_manifest = {"campaign": "YETI LA", "status": "approved"}
    uploaded_meta = adapter.upload_json(
        test_manifest,
        "campaigns/c1/test-manifest.json",
        overwrite=True,
    )
    assert uploaded_meta.path == "campaigns/c1/test-manifest.json"
    mock_dbx.files_upload.assert_called()

    # 4. Test download caching
    dest_path = tmp_path / "cached_manifest.json"
    def fake_download(dest_file, path):
        Path(dest_file).write_text(json.dumps({"mock": True}), encoding="utf-8")

    mock_dbx.files_download_to_file.side_effect = fake_download

    # First download: mock download to file
    adapter.download("campaigns/c1/test-manifest.json", str(dest_path))
    mock_dbx.files_download_to_file.assert_called_once()
    assert dest_path.exists()

    # Reset mock and download again: should hit local revision cache without calling files_download_to_file
    mock_dbx.files_download_to_file.reset_mock()
    adapter.download("campaigns/c1/test-manifest.json", str(dest_path))
    mock_dbx.files_download_to_file.assert_not_called()


def test_storage_factory():
    """Verify get_storage_adapter factory honors environment and force_local flag."""
    with patch.dict(os.environ, {"DROPBOX_ACCESS_TOKEN": ""}):
        local_adapter = get_storage_adapter()
        assert isinstance(local_adapter, LocalStorageAdapter)

    with patch.dict(os.environ, {"DROPBOX_ACCESS_TOKEN": "valid_token"}):
        dbx_adapter = get_storage_adapter()
        assert isinstance(dbx_adapter, DropboxStorageAdapter)

        forced_local = get_storage_adapter(force_local=True)
        assert isinstance(forced_local, LocalStorageAdapter)
