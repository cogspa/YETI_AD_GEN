"""Local Filesystem Storage Adapter."""

import os
import json
import shutil
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Any

from backend.app.services.storage.base import (
    StorageAdapter,
    StorageMetadata,
    StorageStatus,
    StorageNotFoundError,
    StorageAlreadyExistsError,
    StorageError,
)


class LocalStorageAdapter(StorageAdapter):
    """Concrete storage adapter using local filesystem."""

    def __init__(self, root_dir: str = "./outputs"):
        self.root_dir = Path(root_dir).resolve()
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, rel_path: str) -> Path:
        clean = rel_path.lstrip("/").replace("\\", "/")
        target = (self.root_dir / clean).resolve()
        try:
            target.relative_to(self.root_dir)
        except ValueError:
            raise StorageError(f"Security: Path '{rel_path}' traverses outside local storage root.")
        return target

    def _compute_sha256(self, path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    def exists(self, path: str) -> bool:
        target = self._resolve_path(path)
        return target.exists()

    def get_metadata(self, path: str) -> StorageMetadata:
        target = self._resolve_path(path)
        if not target.exists():
            raise StorageNotFoundError(f"Local file '{path}' does not exist.")

        stat = target.stat()
        is_dir = target.is_dir()
        content_hash = self._compute_sha256(target) if not is_dir else None
        mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()

        return StorageMetadata(
            path=str(target.relative_to(self.root_dir)).replace("\\", "/"),
            size_bytes=stat.st_size if not is_dir else 0,
            content_hash=content_hash,
            revision=f"local-{stat.st_mtime_ns}",
            modified_at=mtime,
            is_directory=is_dir,
        )

    def list_directory(self, path: str = "", recursive: bool = False) -> List[StorageMetadata]:
        target = self._resolve_path(path)
        if not target.exists():
            return []

        results: List[StorageMetadata] = []
        if recursive:
            for root, _, files in os.walk(target):
                for f in files:
                    fp = Path(root) / f
                    results.append(self.get_metadata(str(fp.relative_to(self.root_dir))))
        else:
            for item in target.iterdir():
                results.append(self.get_metadata(str(item.relative_to(self.root_dir))))

        return sorted(results, key=lambda m: m.path)

    def download(self, remote_path: str, local_destination_path: str) -> str:
        src = self._resolve_path(remote_path)
        if not src.exists() or src.is_dir():
            raise StorageNotFoundError(f"Local storage source '{remote_path}' not found.")

        dest = Path(local_destination_path).resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        return str(dest)

    def upload(
        self,
        local_source_path: str,
        remote_path: str,
        overwrite: bool = False,
    ) -> StorageMetadata:
        src = Path(local_source_path).resolve()
        if not src.exists() or src.is_dir():
            raise StorageNotFoundError(f"Source file '{local_source_path}' does not exist.")

        dest = self._resolve_path(remote_path)
        if dest.exists() and not overwrite:
            raise StorageAlreadyExistsError(
                f"Destination '{remote_path}' already exists and overwrite is False."
            )

        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        return self.get_metadata(remote_path)

    def upload_json(
        self,
        data: Any,
        remote_path: str,
        overwrite: bool = False,
    ) -> StorageMetadata:
        dest = self._resolve_path(remote_path)
        if dest.exists() and not overwrite:
            raise StorageAlreadyExistsError(
                f"Destination '{remote_path}' already exists and overwrite is False."
            )

        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return self.get_metadata(remote_path)

    def read_json(self, remote_path: str) -> Any:
        src = self._resolve_path(remote_path)
        if not src.exists():
            raise StorageNotFoundError(f"JSON file '{remote_path}' not found.")

        with open(src, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_temporary_link(self, remote_path: str) -> Optional[str]:
        target = self._resolve_path(remote_path)
        if not target.exists():
            return None
        return f"file://{target}"

    def get_status(self) -> StorageStatus:
        return StorageStatus(
            configured=True,
            reachable=self.root_dir.exists(),
            mode="local",
            root=str(self.root_dir).replace("\\", "/"),
            error=None,
        )
