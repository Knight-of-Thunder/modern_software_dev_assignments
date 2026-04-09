from __future__ import annotations

from contextlib import contextmanager
import sqlite3
from pathlib import Path
from typing import Any, Iterator, Optional

from .settings import get_sqlite_path

BASE_DIR = Path(__file__).resolve().parents[1]


def ensure_data_directory_exists() -> None:
    get_sqlite_path().parent.mkdir(parents=True, exist_ok=True)


def _connect() -> sqlite3.Connection:
    ensure_data_directory_exists()
    connection = sqlite3.connect(get_sqlite_path())
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def connection_ctx() -> Iterator[sqlite3.Connection]:
    conn = _connect()
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def transaction_ctx() -> Iterator[sqlite3.Connection]:
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    ensure_data_directory_exists()
    with transaction_ctx() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS action_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                note_id INTEGER,
                text TEXT NOT NULL,
                assignee TEXT,
                priority TEXT,
                done INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (note_id) REFERENCES notes(id)
            );
            """
        )

        # Lightweight migration for older DBs created before assignee/priority existed.
        cursor.execute("PRAGMA table_info(action_items)")
        existing_cols = {str(row[1]) for row in cursor.fetchall()}
        if "assignee" not in existing_cols:
            cursor.execute("ALTER TABLE action_items ADD COLUMN assignee TEXT")
        if "priority" not in existing_cols:
            cursor.execute("ALTER TABLE action_items ADD COLUMN priority TEXT")


def insert_note(content: str, *, conn: sqlite3.Connection | None = None) -> int:
    if conn is None:
        with transaction_ctx() as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO notes (content) VALUES (?)", (content,))
            return int(cursor.lastrowid)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO notes (content) VALUES (?)", (content,))
    return int(cursor.lastrowid)


def list_notes() -> list[sqlite3.Row]:
    with connection_ctx() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id, content, created_at FROM notes ORDER BY id DESC")
        return list(cursor.fetchall())


def get_note(note_id: int) -> Optional[sqlite3.Row]:
    with connection_ctx() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id, content, created_at FROM notes WHERE id = ?",
            (note_id,),
        )
        row = cursor.fetchone()
        return row


def insert_action_items(
    items: list[str],
    note_id: Optional[int] = None,
    *,
    conn: sqlite3.Connection | None = None,
) -> list[int]:
    if conn is None:
        with transaction_ctx() as connection:
            cursor = connection.cursor()
            ids: list[int] = []
            for item in items:
                cursor.execute(
                    "INSERT INTO action_items (note_id, text) VALUES (?, ?)",
                    (note_id, item),
                )
                ids.append(int(cursor.lastrowid))
            return ids
    cursor = conn.cursor()
    ids: list[int] = []
    for item in items:
        cursor.execute(
            "INSERT INTO action_items (note_id, text) VALUES (?, ?)",
            (note_id, item),
        )
        ids.append(int(cursor.lastrowid))
    return ids


def insert_action_items_structured(
    action_items: list[Any],
    note_id: Optional[int] = None,
    *,
    conn: sqlite3.Connection | None = None,
) -> list[int]:
    """
    Stores structured fields when columns exist, while keeping API compatibility.
    Expects each item to have: task (str), assignee (str|None), priority (str|None).
    """

    def _as_row(item: Any) -> tuple[str, str | None, str | None]:
        task = str(getattr(item, "task", "")).strip()
        assignee = getattr(item, "assignee", None)
        priority = getattr(item, "priority", None)
        return task, (str(assignee).strip() if assignee is not None else None), (
            str(priority).strip() if priority is not None else None
        )

    rows = [_as_row(i) for i in action_items]
    rows = [(t, a, p) for (t, a, p) in rows if t]
    if not rows:
        return []

    if conn is None:
        with transaction_ctx() as connection:
            cursor = connection.cursor()
            ids: list[int] = []
            for task, assignee, priority in rows:
                cursor.execute(
                    "INSERT INTO action_items (note_id, text, assignee, priority) VALUES (?, ?, ?, ?)",
                    (note_id, task, assignee, priority),
                )
                ids.append(int(cursor.lastrowid))
            return ids

    cursor = conn.cursor()
    ids: list[int] = []
    for task, assignee, priority in rows:
        cursor.execute(
            "INSERT INTO action_items (note_id, text, assignee, priority) VALUES (?, ?, ?, ?)",
            (note_id, task, assignee, priority),
        )
        ids.append(int(cursor.lastrowid))
    return ids


def list_action_items(note_id: Optional[int] = None) -> list[sqlite3.Row]:
    with connection_ctx() as connection:
        cursor = connection.cursor()
        if note_id is None:
            cursor.execute(
                "SELECT id, note_id, text, done, created_at FROM action_items ORDER BY id DESC"
            )
        else:
            cursor.execute(
                "SELECT id, note_id, text, done, created_at FROM action_items WHERE note_id = ? ORDER BY id DESC",
                (note_id,),
            )
        return list(cursor.fetchall())


def mark_action_item_done(
    action_item_id: int, done: bool, *, conn: sqlite3.Connection | None = None
) -> None:
    if conn is None:
        with transaction_ctx() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE action_items SET done = ? WHERE id = ?",
                (1 if done else 0, action_item_id),
            )
            return
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE action_items SET done = ? WHERE id = ?",
        (1 if done else 0, action_item_id),
    )


