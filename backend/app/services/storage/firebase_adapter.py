"""Firebase & Google Cloud Storage Adapter for YETI Ad Generator."""

import os
import json
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Optional, Any, Dict

from backend.app.services.storage.base import (
    StorageAdapter,
    StorageMetadata,
    StorageStatus,
    StorageError,
    StorageNotFoundError,
    StorageAuthError,
    StorageAlreadyExistsError,
)


class FirebaseStorageAdapter(StorageAdapter):
    """
    Storage adapter connecting to Firebase Storage / Google Cloud Storage buckets.
    Supports upload, download, temporary signed URLs, and health checks.
    """

    def __init__(
        self,
        bucket_name: Optional[str] = None,
        credentials_path: Optional[str] = None,
        credentials_json: Optional[str] = None,
    ):
        self.bucket_name = bucket_name or os.getenv("FIREBASE_STORAGE_BUCKET") or os.getenv("GCS_BUCKET_NAME") or ""
        self.credentials_path = credentials_path or os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv("FIREBASE_CREDENTIALS_PATH")
        self.credentials_json = credentials_json or os.getenv("FIREBASE_CREDENTIALS_JSON")
        
        self._client = None
        self._bucket = None
        self._init_error = None

    def _get_bucket(self):
        if self._bucket is not None:
            return self._bucket
        if self._init_error is not None:
            raise StorageAuthError(f"Firebase Storage initialization failed: {self._init_error}")

        if not self.bucket_name:
            self._init_error = "FIREBASE_STORAGE_BUCKET environment variable is not configured."
            raise StorageAuthError(self._init_error)

        try:
            from google.cloud import storage as gcs_storage
            from google.oauth2 import service_account

            if self.credentials_json:
                cred_info = json.loads(self.credentials_json)
                creds = service_account.Credentials.from_service_account_info(cred_info)
                self._client = gcs_storage.Client(credentials=creds, project=cred_info.get("project_id"))
            elif self.credentials_path and os.path.exists(self.credentials_path):
                creds = service_account.Credentials.from_service_account_file(self.credentials_path)
                self._client = gcs_storage.Client(credentials=creds)
            else:
                # Default application credentials or anonymous fallback
                self._client = gcs_storage.Client()

            self._bucket = self._client.bucket(self.bucket_name)
            return self._bucket
        except ImportError:
            self._init_error = "google-cloud-storage package is not installed."
            raise StorageError(self._init_error)
        except Exception as e:
            self._init_error = str(e)
            raise StorageAuthError(f"Failed to connect to Firebase Storage bucket '{self.bucket_name}': {e}")

    def _clean_path(self, remote_path: str) -> str:
        return remote_path.lstrip("/").replace("\\", "/")

    def exists(self, path: str) -> bool:
        try:
            bucket = self._get_bucket()
            clean = self._clean_path(path)
            blob = bucket.blob(clean)
            return blob.exists()
        except StorageError:
            return False
        except Exception as e:
            raise StorageError(f"Failed to check existence in Firebase Storage: {e}")

    def get_metadata(self, path: str) -> StorageMetadata:
        bucket = self._get_bucket()
        clean = self._clean_path(path)
        blob = bucket.get_blob(clean)
        if blob is None or not blob.exists():
            raise StorageNotFoundError(f"Firebase Storage asset '{path}' not found.")

        mtime = blob.updated.isoformat() if blob.updated else datetime.now(timezone.utc).isoformat()
        return StorageMetadata(
            path=clean,
            size_bytes=blob.size or 0,
            content_hash=blob.md5_hash,
            revision=str(blob.generation),
            modified_at=mtime,
            is_directory=False,
        )

    def list_directory(self, path: str = "", recursive: bool = False) -> List[StorageMetadata]:
        bucket = self._get_bucket()
        clean = self._clean_path(path)
        if clean and not clean.endswith("/"):
            prefix = clean + "/"
        else:
            prefix = clean

        delimiter = None if recursive else "/"
        blobs = bucket.list_blobs(prefix=prefix, delimiter=delimiter)

        results: List[StorageMetadata] = []
        for b in blobs:
            if b.name == prefix:
                continue
            mtime = b.updated.isoformat() if b.updated else datetime.now(timezone.utc).isoformat()
            results.append(
                StorageMetadata(
                    path=b.name,
                    size_bytes=b.size or 0,
                    content_hash=b.md5_hash,
                    revision=str(b.generation),
                    modified_at=mtime,
                    is_directory=b.name.endswith("/"),
                )
            )
        return sorted(results, key=lambda m: m.path)

    def download(self, remote_path: str, local_destination_path: str) -> str:
        bucket = self._get_bucket()
        clean = self._clean_path(remote_path)
        blob = bucket.get_blob(clean)
        if blob is None or not blob.exists():
            raise StorageNotFoundError(f"Firebase Storage asset '{remote_path}' not found.")

        dest = Path(local_destination_path).resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)
        blob.download_to_filename(str(dest))
        return str(dest)

    def upload(
        self,
        local_source_path: str,
        remote_path: str,
        overwrite: bool = False,
    ) -> StorageMetadata:
        src = Path(local_source_path).resolve()
        if not src.exists() or src.is_dir():
            raise StorageNotFoundError(f"Local source file '{local_source_path}' does not exist.")

        bucket = self._get_bucket()
        clean = self._clean_path(remote_path)
        blob = bucket.blob(clean)

        if not overwrite and blob.exists():
            raise StorageAlreadyExistsError(f"Asset '{remote_path}' already exists in Firebase Storage.")

        content_type = "image/png"
        if clean.endswith(".jpg") or clean.endswith(".jpeg"):
            content_type = "image/jpeg"
        elif clean.endswith(".json"):
            content_type = "application/json"
        elif clean.endswith(".zip"):
            content_type = "application/zip"
        elif clean.endswith(".log"):
            content_type = "text/plain"

        blob.upload_from_filename(str(src), content_type=content_type)
        return self.get_metadata(clean)

    def upload_json(
        self,
        data: Any,
        remote_path: str,
        overwrite: bool = False,
    ) -> StorageMetadata:
        bucket = self._get_bucket()
        clean = self._clean_path(remote_path)
        blob = bucket.blob(clean)

        if not overwrite and blob.exists():
            raise StorageAlreadyExistsError(f"JSON asset '{remote_path}' already exists in Firebase Storage.")

        json_bytes = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        blob.upload_from_string(json_bytes, content_type="application/json")
        return self.get_metadata(clean)

    def read_json(self, remote_path: str) -> Any:
        bucket = self._get_bucket()
        clean = self._clean_path(remote_path)
        blob = bucket.get_blob(clean)
        if blob is None or not blob.exists():
            raise StorageNotFoundError(f"JSON asset '{remote_path}' not found in Firebase Storage.")

        content = blob.download_as_text()
        return json.loads(content)

    def get_temporary_link(self, remote_path: str) -> Optional[str]:
        try:
            bucket = self._get_bucket()
            clean = self._clean_path(remote_path)
            blob = bucket.blob(clean)
            if not blob.exists():
                return None
            return blob.generate_signed_url(expiration=timedelta(hours=2), method="GET")
        except Exception:
            clean = self._clean_path(remote_path)
            return f"https://storage.googleapis.com/{self.bucket_name}/{clean}"

    def get_shared_folder_link(self, remote_folder_path: str) -> Optional[str]:
        clean = self._clean_path(remote_folder_path)
        return f"https://console.firebase.google.com/project/_/storage/{self.bucket_name}/files/~2F{clean}"

    def get_status(self) -> StorageStatus:
        is_configured = bool(self.bucket_name)
        if not is_configured:
            return StorageStatus(
                configured=False,
                reachable=False,
                mode="firebase",
                root=self.bucket_name,
                error="FIREBASE_STORAGE_BUCKET is not set.",
            )

        try:
            bucket = self._get_bucket()
            reachable = bucket.exists()
            return StorageStatus(
                configured=True,
                reachable=reachable,
                mode="firebase",
                root=f"gs://{self.bucket_name}",
            )
        except Exception as e:
            return StorageStatus(
                configured=True,
                reachable=False,
                mode="firebase",
                root=f"gs://{self.bucket_name}",
                error=str(e),
            )
