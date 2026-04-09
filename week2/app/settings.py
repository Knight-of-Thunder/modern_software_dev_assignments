from __future__ import annotations

import os
from pathlib import Path


def get_sqlite_path() -> Path:
    """
    SQLite file path for the app.

    Defaults to week2/data/app.db to preserve current behavior.
    """

    base_dir = Path(__file__).resolve().parents[1]
    default_path = base_dir / "data" / "app.db"
    raw = os.getenv("SQLITE_PATH")
    if not raw:
        return default_path
    return Path(raw)


def get_ollama_model() -> str:
    # Kept for centralized config; extract_action_items_llm currently pins llama3.1 per requirements.
    return os.getenv("OLLAMA_MODEL", "llama3.1")

