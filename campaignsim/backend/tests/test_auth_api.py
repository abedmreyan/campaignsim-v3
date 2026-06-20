"""Integration tests for auth API endpoints."""

import json
import pytest


def _signup(client, email="test@example.com", password="Password1!", name="Test User"):
    return client.post(
        "/api/auth/signup",
        json={"email": email, "password": password, "display_name": name},
    )


def test_signup_creates_user_and_sets_cookies(client):
    resp = _signup(client)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["user"]["email"] == "test@example.com"
    assert "cs_access" in resp.headers.get("Set-Cookie", "")


def test_signup_duplicate_email_returns_409(client):
    _signup(client)
    resp = _signup(client)
    assert resp.status_code == 409


def test_login_with_correct_credentials(client):
    _signup(client)
    resp = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "Password1!"},
    )
    assert resp.status_code == 200
    assert "cs_access" in resp.headers.get("Set-Cookie", "")


def test_login_with_wrong_password_returns_401(client):
    _signup(client)
    resp = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "WrongPass1!"},
    )
    assert resp.status_code == 401


def test_me_returns_user_when_authenticated(client):
    _signup(client)
    # The test client holds cookies from signup automatically
    resp = client.get("/api/auth/me")
    assert resp.status_code == 200
    assert resp.get_json()["email"] == "test@example.com"


def test_me_returns_401_when_not_authenticated(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_logout_clears_cookies(client):
    _signup(client)
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 200
    # Cookies should be cleared (max-age=0)
    cookie_header = resp.headers.get("Set-Cookie", "")
    assert "cs_access" in cookie_header
