"""Tests for auth utility functions."""

import time
import pytest
from app.utils.auth_utils import (
    encode_access_jwt,
    decode_jwt,
    hash_token,
    hash_password,
    check_password,
)

SECRET = "test-secret"


def test_encode_decode_roundtrip():
    token = encode_access_jwt("user-1", SECRET, ttl_minutes=15)
    payload = decode_jwt(token, SECRET)
    assert payload["sub"] == "user-1"


def test_decode_expired_token_raises():
    token = encode_access_jwt("user-1", SECRET, ttl_minutes=0)
    time.sleep(1)
    with pytest.raises(ValueError, match="expired"):
        decode_jwt(token, SECRET)


def test_decode_wrong_secret_raises():
    token = encode_access_jwt("user-1", SECRET, ttl_minutes=15)
    with pytest.raises(ValueError):
        decode_jwt(token, "wrong-secret")


def test_hash_token_is_deterministic():
    assert hash_token("abc") == hash_token("abc")


def test_hash_token_differs_from_raw():
    raw = "my-refresh-token"
    assert hash_token(raw) != raw


def test_password_roundtrip():
    hashed = hash_password("my-password")
    assert check_password("my-password", hashed) is True
    assert check_password("wrong-password", hashed) is False
