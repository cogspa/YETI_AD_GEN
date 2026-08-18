"""Dropbox Storage Adapter implementation using official Dropbox Python SDK."""

import os
import json
from pathlib import Path
from typing import List, Optional, Any, Dict

import dropbox
from dropbox.exceptions import ApiError, AuthError
from dropbox.files import (
    WriteMode,
    FileMetadata,
    FolderMetadata,
    LookupError,
    GetMetadataError,
)

from backend.app.services.storage.base import (
    StorageAdapter,
    StorageMetadata,
    StorageStatus,
    StorageNotFoundError,
    StorageAuthError,
    StorageAlreadyExistsError,
    StorageError,
)


class DropboxStorageAdapter(StorageAdapter):
    """
    Storage adapter communicating with Dropbox API behind the unified StorageAdapter contract.
    Features revision-based asset caching, overwrite protection, and non-leaking status checks.
    """

    def __init__(
        self,
        access_token: Optional[str] = None,
        campaign_root: Optional[str] = None,
        cache_dir: Optional[str] = None,
    ):
        self.access_token = access_token or os.getenv("DROPBOX_ACCESS_TOKEN")
        self.campaign_root = (campaign_root or os.getenv("DROPBOX_CAMPAIGN_ROOT", "/yeti-ad-generator")).rstrip("/")
        self.cache_dir = Path(cache_dir or os.getenv("LOCAL_ASSET_CACHE_DIR", "./.cache/dropbox-assets")).resolve()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._client: Optional[dropbox.Dropbox] = None
        if self.access_token:
            self._client = dropbox.Dropbox(self.access_token)

    def _get_client(self) -> dropbox.Dropbox:
        if not self._client:
            raise StorageAuthError("DROPBOX_ACCESS_TOKEN is not configured in server environment.")
        return self._client

    def normalize_path(self, rel_path: str) -> str:
        """
        Normalize path to be strictly within the DROPBOX_CAMPAIGN_ROOT.
        Returns a clean leading-slash path like '/yeti-ad-generator/campaigns/...'.
        """
        cleaned = rel_path.strip().replace("\\", "/").strip("/")
        if not cleaned:
            return self.campaign_root

        root_clean = self.campaign_root.strip("/")
        if cleaned.startswith(root_clean):
            return f"/{cleaned}"

        return f"{self.campaign_root}/{cleaned}"

    def exists(self, path: str) -> bool:
        client = self._get_client()
        norm_path = self.normalize_path(path)
        try:
            client.files_get_metadata(norm_path)
            return True
        except ApiError as e:
            if isinstance(e.error, GetMetadataError) and e.error.is_path() and e.error.get_path().is_not_found():
                return False
            raise StorageError(f"Dropbox exists check failed for '{path}': {e}")
        except AuthError as ae:
            raise StorageAuthError(f"Dropbox authentication error: {ae}")

    def get_metadata(self, path: str) -> StorageMetadata:
        client = self._get_client()
        norm_path = self.normalize_path(path)
        try:
            meta = client.files_get_metadata(norm_path)
            return self._convert_metadata(meta)
        except ApiError as e:
            if isinstance(e.error, GetMetadataError) and e.error.is_path() and e.error.get_path().is_not_found():
                raise StorageNotFoundError(f"Dropbox asset '{path}' not found at '{norm_path}'.")
            raise StorageError(f"Dropbox get_metadata failed for '{path}': {e}")
        except AuthError as ae:
            raise StorageAuthError(f"Dropbox authentication error: {ae}")

    def _convert_metadata(self, meta: Any) -> StorageMetadata:
        is_dir = isinstance(meta, FolderMetadata)
        is_file = isinstance(meta, FileMetadata)

        rel_path = meta.path_display or meta.path_lower or ""
        if rel_path.startswith(self.campaign_root):
            rel_path = rel_path[len(self.campaign_root):].lstrip("/")

        size = meta.size if is_file else 0
        content_hash = meta.content_hash if is_file else None
        rev = meta.rev if is_file else None
        mtime = meta.server_modified.isoformat() if is_file and hasattr(meta, "server_modified") else None

        return StorageMetadata(
            path=rel_path,
            size_bytes=size,
            content_hash=content_hash,
            revision=rev,
            modified_at=mtime,
            is_directory=is_dir,
        )

    def list_directory(self, path: str = "", recursive: bool = False) -> List[StorageMetadata]:
        client = self._get_client()
        norm_path = self.normalize_path(path)
        results: List[StorageMetadata] = []

        try:
            res = client.files_list_folder(norm_path, recursive=recursive)
            for entry in res.entries:
                results.append(self._convert_metadata(entry))

            while res.has_more:
                res = client.files_list_folder_continue(res.cursor)
                for entry in res.entries:
                    results.append(self._convert_metadata(entry))

            return sorted(results, key=lambda m: m.path)
        except ApiError as e:
            raise StorageError(f"Dropbox list_directory failed for '{path}': {e}")
        except AuthError as ae:
            raise StorageAuthError(f"Dropbox authentication error: {ae}")

    def download(self, remote_path: str, local_destination_path: str) -> str:
        """
        Download with cache verification: if local file exists and matches remote rev/hash, skips download.
        """
        client = self._get_client()
        norm_path = self.normalize_path(remote_path)
        dest = Path(local_destination_path).resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)

        meta = self.get_metadata(remote_path)
        if meta.is_directory:
            raise StorageError(f"Cannot download directory '{remote_path}' as a file.")

        # Cache check: if local cache file exists, record rev metadata sidecar
        sidecar_path = dest.with_suffix(dest.suffix + ".dbx_meta")
        if dest.exists() and sidecar_path.exists():
            try:
                with open(sidecar_path, "r", encoding="utf-8") as f:
                    cached_meta = json.load(f)
                if cached_meta.get("revision") == meta.revision and cached_meta.get("content_hash") == meta.content_hash:
                    # Unchanged, return cached copy
                    return str(dest)
            except Exception:
                pass

        # Download from Dropbox
        try:
            client.files_download_to_file(str(dest), norm_path)
            # Write sidecar cache verification
            with open(sidecar_path, "w", encoding="utf-8") as f:
                json.dump(
                    {"revision": meta.revision, "content_hash": meta.content_hash, "size": meta.size_bytes},
                    f,
                )
            return str(dest)
        except ApiError as e:
            raise StorageError(f"Dropbox download failed for '{remote_path}': {e}")
        except AuthError as ae:
            raise StorageAuthError(f"Dropbox authentication error: {ae}")

    def upload(
        self,
        local_source_path: str,
        remote_path: str,
        overwrite: bool = False,
    ) -> StorageMetadata:
        client = self._get_client()
        src = Path(local_source_path).resolve()
        if not src.exists() or src.is_dir():
            raise StorageNotFoundError(f"Local source file '{local_source_path}' does not exist.")

        norm_path = self.normalize_path(remote_path)

        if not overwrite and self.exists(remote_path):
            raise StorageAlreadyExistsError(
                f"Dropbox destination '{remote_path}' already exists and overwrite is False."
            )

        mode = WriteMode.overwrite if overwrite else WriteMode.add

        try:
            with open(src, "rb") as f:
                file_bytes = f.read()

            meta = client.files_upload(file_bytes, norm_path, mode=mode)
            return self._convert_metadata(meta)
        except ApiError as e:
            raise StorageError(f"Dropbox upload failed for '{remote_path}': {e}")
        except AuthError as ae:
            raise StorageAuthError(f"Dropbox authentication error: {ae}")

    def upload_json(
        self,
        data: Any,
        remote_path: str,
        overwrite: bool = False,
    ) -> StorageMetadata:
        client = self._get_client()
        norm_path = self.normalize_path(remote_path)

        if not overwrite and self.exists(remote_path):
            raise StorageAlreadyExistsError(
                f"Dropbox destination '{remote_path}' already exists and overwrite is False."
            )

        mode = WriteMode.overwrite if overwrite else WriteMode.add

        try:
            json_bytes = json.dumps(data, indent=2).encode("utf-8")
            meta = client.files_upload(json_bytes, norm_path, mode=mode)
            return self._convert_metadata(meta)
        except ApiError as e:
            raise StorageError(f"Dropbox upload_json failed for '{remote_path}': {e}")
        except AuthError as ae:
            raise StorageAuthError(f"Dropbox authentication error: {ae}")

    def read_json(self, remote_path: str) -> Any:
        client = self._get_client()
        norm_path = self.normalize_path(remote_path)

        try:
            _, response = client.files_download(norm_path)
            content_str = response.content.decode("utf-8")
            return json.loads(content_str)
        except ApiError as e:
            if isinstance(e.error, GetMetadataError) and e.error.is_path() and e.error.get_path().is_not_found():
                raise StorageNotFoundError(f"Dropbox JSON file '{remote_path}' not found at '{norm_path}'.")
            raise StorageError(f"Dropbox read_json failed for '{remote_path}': {e}")
        except AuthError as ae:
            raise StorageAuthError(f"Dropbox authentication error: {ae}")

    def get_temporary_link(self, remote_path: str) -> Optional[str]:
        client = self._get_client()
        norm_path = self.normalize_path(remote_path)
        try:
            link_res = client.files_get_temporary_link(norm_path)
            return link_res.link
        except Exception:
            return None

    def get_status(self) -> StorageStatus:
        if not self.access_token:
            return StorageStatus(
                configured=False,
                reachable=False,
                mode="dropbox",
                root=self.campaign_root,
                error="DROPBOX_ACCESS_TOKEN is not configured.",
            )

        try:
            client = self._get_client()
            client.users_get_current_account()
            return StorageStatus(
                configured=True,
                reachable=True,
                mode="dropbox",
                root=self.campaign_root,
                error=None,
            )
        except Exception as e:
            return StorageStatus(
                configured=True,
                reachable=False,
                mode="dropbox",
                root=self.campaign_root,
                error=f"Dropbox unreachable: {str(e)}",
            )
