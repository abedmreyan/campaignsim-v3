"""Integration tests for brand brief API."""

import pytest


def _signup_and_get_client(client):
    client.post(
        "/api/auth/signup",
        json={"email": "user@example.com", "password": "Password1!", "display_name": "U"},
    )
    return client


def test_list_briefs_empty_for_new_user(client):
    _signup_and_get_client(client)
    resp = client.get("/api/briefs")
    assert resp.status_code == 200
    assert resp.get_json()["items"] == []


def test_create_brief(client):
    _signup_and_get_client(client)
    resp = client.post("/api/briefs", json={"name": "My Brand", "content": "We sell coffee."})
    assert resp.status_code == 201
    data = resp.get_json()["brief"]
    assert data["name"] == "My Brand"
    assert data["content"] == "We sell coffee."
    assert data["graph_status"] == "pending"


def test_get_brief_by_id(client):
    _signup_and_get_client(client)
    created = client.post("/api/briefs", json={"name": "Brand X", "content": "X content"})
    brief_id = created.get_json()["brief"]["id"]

    resp = client.get(f"/api/briefs/{brief_id}")
    assert resp.status_code == 200
    assert resp.get_json()["brief"]["id"] == brief_id


def test_update_brief_name_and_content(client):
    _signup_and_get_client(client)
    created = client.post("/api/briefs", json={"name": "Old Name", "content": "old"})
    brief_id = created.get_json()["brief"]["id"]

    resp = client.put(f"/api/briefs/{brief_id}", json={"name": "New Name", "content": "new"})
    assert resp.status_code == 200
    assert resp.get_json()["brief"]["name"] == "New Name"


def test_delete_brief(client):
    _signup_and_get_client(client)
    created = client.post("/api/briefs", json={"name": "To Delete", "content": "bye"})
    brief_id = created.get_json()["brief"]["id"]

    resp = client.delete(f"/api/briefs/{brief_id}")
    assert resp.status_code == 200

    resp2 = client.get(f"/api/briefs/{brief_id}")
    assert resp2.status_code == 404


def test_cannot_access_another_users_brief(client):
    client.post(
        "/api/auth/signup",
        json={"email": "user1@example.com", "password": "Password1!", "display_name": "U1"},
    )
    created = client.post("/api/briefs", json={"name": "User1 Brief", "content": "private"})
    brief_id = created.get_json()["brief"]["id"]

    # Log in as user2
    client.post("/api/auth/logout")
    client.post(
        "/api/auth/signup",
        json={"email": "user2@example.com", "password": "Password1!", "display_name": "U2"},
    )
    resp = client.get(f"/api/briefs/{brief_id}")
    assert resp.status_code == 404
