"""Tests for the StorageBackend abstraction."""

import os
import tempfile
import pytest
from app.services.storage import LocalStorage


@pytest.fixture()
def storage(tmp_path):
    return LocalStorage(base=str(tmp_path))


def test_user_path_includes_user_id(storage, tmp_path):
    path = storage.user_path("user-123", "knowledge_graphs", "kg-abc")
    assert "user-123" in path
    assert "knowledge_graphs" in path
    assert "kg-abc" in path


def test_save_and_load_roundtrip(storage):
    data = b"hello brief content"
    storage.save_file("user-1", "briefs/brief.txt", data)
    assert storage.load_file("user-1", "briefs/brief.txt") == data


def test_exists_returns_false_before_save(storage):
    assert storage.exists("user-1", "briefs/missing.txt") is False


def test_exists_returns_true_after_save(storage):
    storage.save_file("user-1", "briefs/file.txt", b"x")
    assert storage.exists("user-1", "briefs/file.txt") is True


def test_delete_file(storage):
    storage.save_file("user-1", "briefs/del.txt", b"delete me")
    storage.delete_file("user-1", "briefs/del.txt")
    assert storage.exists("user-1", "briefs/del.txt") is False


def test_save_creates_intermediate_directories(storage):
    storage.save_file("user-1", "deep/nested/dir/file.bin", b"data")
    assert storage.exists("user-1", "deep/nested/dir/file.bin") is True
