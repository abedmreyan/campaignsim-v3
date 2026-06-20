"""Tests for persona persistence endpoints."""

import pytest
from app.db import db as _db
from app.db.models import BrandBrief, Persona


def _auth(client):
    client.post(
        "/api/auth/signup",
        json={"email": "p@example.com", "password": "Password1!", "display_name": "P"},
    )


def _make_brief(client):
    resp = client.post("/api/briefs", json={"name": "B", "content": "c"})
    return resp.get_json()["brief"]["id"]


def _seed_personas(app, user_id, brief_id, count=3):
    """Directly insert test personas into the DB."""
    with app.app_context():
        for i in range(count):
            p = Persona(
                user_id=user_id,
                brand_brief_id=brief_id,
                external_id=f"user_{i:03}",
                segment="Segment A",
                data={"name": f"Person {i}", "user_id": f"user_{i:03}"},
            )
            _db.session.add(p)
        _db.session.commit()


def test_list_personas_empty(client):
    _auth(client)
    brief_id = _make_brief(client)
    resp = client.get(f"/api/simulation/personas?brief_id={brief_id}")
    assert resp.status_code == 200
    assert resp.get_json()["items"] == []


def test_list_personas_returns_saved_rows(client, app):
    _auth(client)
    brief_id = _make_brief(client)
    # Get user_id from the me endpoint
    me = client.get("/api/auth/me").get_json()
    _seed_personas(app, me["id"], brief_id, count=3)
    resp = client.get(f"/api/simulation/personas?brief_id={brief_id}")
    assert len(resp.get_json()["items"]) == 3


def test_delete_persona(client, app):
    _auth(client)
    brief_id = _make_brief(client)
    me = client.get("/api/auth/me").get_json()
    _seed_personas(app, me["id"], brief_id, count=2)

    items = client.get(f"/api/simulation/personas?brief_id={brief_id}").get_json()["items"]
    persona_id = items[0]["id"]

    resp = client.delete(f"/api/simulation/persona/{persona_id}")
    assert resp.status_code == 200

    items_after = client.get(f"/api/simulation/personas?brief_id={brief_id}").get_json()["items"]
    assert len(items_after) == 1


def test_clear_personas(client, app):
    _auth(client)
    brief_id = _make_brief(client)
    me = client.get("/api/auth/me").get_json()
    _seed_personas(app, me["id"], brief_id, count=5)

    resp = client.post(f"/api/simulation/personas/clear?brief_id={brief_id}")
    assert resp.status_code == 200

    items = client.get(f"/api/simulation/personas?brief_id={brief_id}").get_json()["items"]
    assert items == []
