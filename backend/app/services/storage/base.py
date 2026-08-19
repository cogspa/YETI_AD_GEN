"""Abstract Base Class and Models for Storage Adapters."""

import abc
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class StorageMetadata(BaseModel):
    """File or directory metadata within a storage provider."""
    path: str
    size_bytes: int = 0
    content_hash: Optional[str] = None
    revision: Optional[str] = None
    modified_at: Optional[str] = None
    is_directory: bool = False


class StorageStatus(BaseModel):
    """Health and configuration status of the storage provider."""
    configured: bool
    reachable: bool
    mode: str = Field(description="'local' or 'dropbox'")
    root: str
    error: Optional[str] = None


class StorageError(Exception):
    """Base exception for storage adapter operations."""
    pass


class StorageNotFoundError(StorageError):
    """Raised when a requested remote or local path does not exist."""
    pass


class StorageAuthError(StorageError):
    """Raised on authentication or credential failures."""
    pass


class StorageAlreadyExistsError(StorageError):
    """Raised when upload attempts to overwrite an existing asset without overwrite=True."""
    pass


class StorageAdapter(abc.ABC):
    """Abstract interface for file and artifact storage providers."""

    @abc.abstractmethod
    def exists(self, path: str) -> bool:
        """Return True if path exists in storage."""
        pass

    @abc.abstractmethod
    def get_metadata(self, path: str) -> StorageMetadata:
        """Retrieve metadata for a specific path."""
        pass

    @abc.abstractmethod
    def list_directory(self, path: str, recursive: bool = False) -> List[StorageMetadata]:
        """List files and folders under path."""
        pass

    @abc.abstractmethod
    def download(self, remote_path: str, local_destination_path: str) -> str:
        """Download remote asset to local destination, returning destination path."""
        pass

    @abc.abstractmethod
    def upload(
        self,
        local_source_path: str,
        remote_path: str,
        overwrite: bool = False,
    ) -> StorageMetadata:
        """Upload local file to remote storage."""
        pass

    @abc.abstractmethod
    def upload_json(
        self,
        data: Any,
        remote_path: str,
        overwrite: bool = False,
    ) -> StorageMetadata:
        """Serialize data to JSON and upload to remote storage."""
        pass

    @abc.abstractmethod
    def read_json(self, remote_path: str) -> Any:
        """Read and deserialize JSON file from remote storage."""
        pass

    @abc.abstractmethod
    def get_temporary_link(self, remote_path: str) -> Optional[str]:
        """Generate temporary direct download link if supported."""
        pass

    @abc.abstractmethod
    def get_shared_folder_link(self, remote_folder_path: str) -> Optional[str]:
        """Generate web browser link to view the storage folder."""
        pass

    @abc.abstractmethod
    def get_status(self) -> StorageStatus:
        """Return provider readiness and reachability status without exposing secrets."""
        pass

