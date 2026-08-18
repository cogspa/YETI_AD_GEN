"""Storage Adapter Module for YETI Ad Generator."""

import os
from typing import Optional

from backend.app.services.storage.base import (
    StorageAdapter,
    StorageMetadata,
    StorageStatus,
    StorageError,
    StorageNotFoundError,
    StorageAuthError,
    StorageAlreadyExistsError,
)
from backend.app.services.storage.local import LocalStorageAdapter
from backend.app.services.storage.dropbox_adapter import DropboxStorageAdapter


def get_storage_adapter(force_local: bool = False) -> StorageAdapter:
    """
    Storage factory returning DropboxStorageAdapter when DROPBOX_ACCESS_TOKEN or
    DROPBOX_REFRESH_TOKEN credentials are configured, or LocalStorageAdapter as default.
    """
    token = os.getenv("DROPBOX_ACCESS_TOKEN")
    refresh_token = os.getenv("DROPBOX_REFRESH_TOKEN")
    app_key = os.getenv("DROPBOX_APP_KEY")
    app_secret = os.getenv("DROPBOX_APP_SECRET")

    is_dbx = bool(token or (refresh_token and app_key and app_secret))
    if is_dbx and not force_local:
        return DropboxStorageAdapter(
            access_token=token,
            refresh_token=refresh_token,
            app_key=app_key,
            app_secret=app_secret,
        )

    storage_root = os.getenv("STORAGE_ROOT", "./outputs")
    return LocalStorageAdapter(root_dir=storage_root)


__all__ = [
    "StorageAdapter",
    "StorageMetadata",
    "StorageStatus",
    "StorageError",
    "StorageNotFoundError",
    "StorageAuthError",
    "StorageAlreadyExistsError",
    "LocalStorageAdapter",
    "DropboxStorageAdapter",
    "get_storage_adapter",
]
