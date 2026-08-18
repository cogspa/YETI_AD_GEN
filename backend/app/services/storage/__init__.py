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
    Storage factory returning DropboxStorageAdapter when DROPBOX_ACCESS_TOKEN is configured,
    or LocalStorageAdapter as the robust offline / default local store.
    """
    token = os.getenv("DROPBOX_ACCESS_TOKEN")
    if token and not force_local:
        return DropboxStorageAdapter(access_token=token)

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
