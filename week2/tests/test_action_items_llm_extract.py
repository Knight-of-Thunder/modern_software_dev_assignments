import json

import pytest
from fastapi.testclient import TestClient


class _FakeOllamaMessage:
    def __init__(self, content: str):
        self.content = content


class _FakeOllamaResponse:
    def __init__(self, content: str):
        self.message = _FakeOllamaMessage(content)


def _fake_chat_returning(action_items):
    payload = {"action_items": action_items}
    return _FakeOllamaResponse(json.dumps(payload))


def test_action_items_extract_llm_compat_response_and_db_write(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "app.db"))

    # Patch the symbol used by extract_action_items_llm (imported as `chat` in the module).
    from week2.app.services import extract as extract_module

    monkeypatch.setattr(
        extract_module,
        "chat",
        lambda **kwargs: _fake_chat_returning(
            [
                {"task": "Set up database", "assignee": "Alice", "priority": "high"},
                {"task": "Write tests", "assignee": None, "priority": "medium"},
            ]
        ),
    )

    from week2.app.main import app
    from week2.app import db

    with TestClient(app) as client:
        resp = client.post("/action-items/extract", json={"text": "meeting notes", "save_note": True})
        assert resp.status_code == 200
        body = resp.json()

    # API compatibility: keep legacy shape {note_id, items:[{id,text}]}
    assert isinstance(body["note_id"], int)
    assert [i["text"] for i in body["items"]] == ["Set up database", "Write tests"]
    assert all(isinstance(i["id"], int) for i in body["items"])

    # Validate structured fields were stored (assignee/priority columns).
    with db.connection_ctx() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT text, assignee, priority FROM action_items ORDER BY id ASC"
        )
        rows = cur.fetchall()

    assert [(r["text"], r["assignee"], r["priority"]) for r in rows] == [
        ("Set up database", "Alice", "high"),
        ("Write tests", None, "medium"),
    ]


def test_action_items_extract_llm_save_note_false(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "app.db"))

    from week2.app.services import extract as extract_module

    monkeypatch.setattr(
        extract_module,
        "chat",
        lambda **kwargs: _fake_chat_returning(
            [
                {"task": "Schedule QA", "assignee": "Bob", "priority": None},
            ]
        ),
    )

    from week2.app.main import app

    with TestClient(app) as client:
        resp = client.post("/action-items/extract", json={"text": "random", "save_note": False})
        assert resp.status_code == 200
        body = resp.json()

    assert body["note_id"] is None
    assert [i["text"] for i in body["items"]] == ["Schedule QA"]

