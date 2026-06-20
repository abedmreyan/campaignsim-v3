"""Storage abstraction for user-scoped file I/O.

LocalStorage stores files at {base}/{user_id}/{key}.
An S3Storage class can implement the same interface later without
touching any service code — just swap the registered backend.
"""

import os
import shutil


class StorageBackend:
    """Interface definition. Subclasses must implement all methods."""

    def save_file(self, user_id: str, key: str, data: bytes) -> str:
        """Write bytes to storage. Returns the resolved path/URL."""
        raise NotImplementedError

    def load_file(self, user_id: str, key: str) -> bytes:
        """Read bytes from storage."""
        raise NotImplementedError

    def delete_file(self, user_id: str, key: str) -> None:
        """Delete a file. No-op if the file does not exist."""
        raise NotImplementedError

    def exists(self, user_id: str, key: str) -> bool:
        """Return True if the file exists."""
        raise NotImplementedError

    def user_path(self, user_id: str, *parts: str) -> str:
        """Return the full local path for a user-scoped resource."""
        raise NotImplementedError


class LocalStorage(StorageBackend):
    """Stores files at {base}/{user_id}/{key} on the local filesystem."""

    def __init__(self, base: str):
        self.base = os.path.abspath(base)

    def user_path(self, user_id: str, *parts: str) -> str:
        return os.path.join(self.base, user_id, *parts)

    def _full_path(self, user_id: str, key: str) -> str:
        return os.path.join(self.base, user_id, key)

    def save_file(self, user_id: str, key: str, data: bytes) -> str:
        path = self._full_path(user_id, key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
        return path

    def load_file(self, user_id: str, key: str) -> bytes:
        with open(self._full_path(user_id, key), "rb") as f:
            return f.read()

    def delete_file(self, user_id: str, key: str) -> None:
        path = self._full_path(user_id, key)
        if os.path.exists(path):
            os.remove(path)

    def exists(self, user_id: str, key: str) -> bool:
        return os.path.exists(self._full_path(user_id, key))
