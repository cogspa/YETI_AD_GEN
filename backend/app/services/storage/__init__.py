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
from backend.app.services.storage.firebase_adapter import FirebaseStorageAdapter


def get_storage_adapter(force_local: bool = False) -> StorageAdapter:
    """
    Storage factory returning:
    - LocalStorageAdapter if force_local is True or as default fallback.
    - FirebaseStorageAdapter if STORAGE_MODE='firebase' or FIREBASE_STORAGE_BUCKET is configured.
    - DropboxStorageAdapter if DROPBOX_ACCESS_TOKEN or DROPBOX_REFRESH_TOKEN credentials are configured.
    """
    if force_local:
        storage_root = os.getenv("STORAGE_ROOT", "./outputs")
        return LocalStorageAdapter(root_dir=storage_root)

    storage_mode = os.getenv("STORAGE_MODE", "").lower()

    # 1. Firebase / GCS Storage Mode
    firebase_bucket = os.getenv("FIREBASE_STORAGE_BUCKET") or os.getenv("GCS_BUCKET_NAME")
    if storage_mode in ("firebase", "gcs") or (firebase_bucket and storage_mode != "dropbox"):
        return FirebaseStorageAdapter(bucket_name=firebase_bucket)

    # 2. Dropbox Storage Mode
    token = os.getenv("DROPBOX_ACCESS_TOKEN")
    refresh_token = os.getenv("DROPBOX_REFRESH_TOKEN")
    app_key = os.getenv("DROPBOX_APP_KEY")
    app_secret = os.getenv("DROPBOX_APP_SECRET")

    is_dbx = bool(token or (refresh_token and app_key and app_secret))
    if is_dbx:
        return DropboxStorageAdapter(
            access_token=token,
            refresh_token=refresh_token,
            app_key=app_key,
            app_secret=app_secret,
        )

    # 3. Default Local Storage
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
    "FirebaseStorageAdapter",
    "get_storage_adapter",
]
