"""Storage abstraction (spec §5).

All user files (uploaded briefs, knowledge graph DBs, simulation output)
live under a per-user root: {base}/{user_id}/{key...}. LocalStorage is the
only implementation for now; S3Storage can implement the same interface
later without touching service code.
"""

import os
import shutil

from ..config import Config


class StorageBackend:
    """Interface for user-scoped file storage."""

    def save_file(self, user_id: str, key: str, data: bytes) -> str:
        raise NotImplementedError

    def load_file(self, user_id: str, key: str) -> bytes:
        raise NotImplementedError

    def delete_file(self, user_id: str, key: str):
        raise NotImplementedError

    def exists(self, user_id: str, key: str) -> bool:
        raise NotImplementedError

    def user_path(self, user_id: str, *parts) -> str:
        raise NotImplementedError


class LocalStorage(StorageBackend):
    """Stores files at {base}/{user_id}/{key}."""

    def __init__(self, base: str):
        self.base = os.path.abspath(base)

    def user_path(self, user_id: str, *parts) -> str:
        path = os.path.abspath(os.path.join(self.base, str(user_id), *parts))
        # Guard against path traversal via crafted keys.
        if not path.startswith(self.base + os.sep):
            raise ValueError(f"Path escapes storage root: {path}")
        return path

    def save_file(self, user_id: str, key: str, data: bytes) -> str:
        path = self.user_path(user_id, key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
        return path

    def load_file(self, user_id: str, key: str) -> bytes:
        with open(self.user_path(user_id, key), "rb") as f:
            return f.read()

    def delete_file(self, user_id: str, key: str):
        path = self.user_path(user_id, key)
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
        elif os.path.exists(path):
            os.remove(path)

    def exists(self, user_id: str, key: str) -> bool:
        return os.path.exists(self.user_path(user_id, key))


# App-level singleton
storage = LocalStorage(Config.UPLOAD_FOLDER)
