# Week 2 - Action Item Extractor

A minimal FastAPI + SQLite application that turns free-form notes into actionable tasks using an LLM (Ollama), with a lightweight HTML frontend for quick interaction.

## Project Overview

This project provides:

- A backend API built with FastAPI
- SQLite persistence for notes and action items
- LLM-based extraction (`extract_action_items_llm`) with structured JSON output
- A simple frontend to:
  - submit notes for extraction
  - mark action items as done
  - list all saved notes

Core flow:

1. User submits notes text to `POST /action-items/extract`
2. Backend calls Ollama with a strict JSON schema
3. Extracted tasks are saved in SQLite
4. Frontend renders checkboxes for action items and supports listing notes

## Tech Stack

- Python
- FastAPI
- SQLite (`sqlite3`)
- Ollama Python SDK (`ollama`)
- Pydantic
- Pytest

## Setup and Run

## 1) Environment

If you are using conda (as in the course setup):

```bash
conda activate cs146s
```

## 2) Install dependencies

Install the required Python packages in your active environment:

```bash
pip install fastapi uvicorn pydantic python-dotenv ollama pytest
```

## 3) Run Ollama model

Pull and run a llama3.1 model locally (example):

```bash
ollama run llama3.1:8b
```

You can override the model via environment variable:

```bash
export OLLAMA_MODEL=llama3.1:8b
```

## 4) Start the API server

From repository root:

```bash
uvicorn week2.app.main:app --reload
```

Open:

- App UI: <http://127.0.0.1:8000/>
- API docs: <http://127.0.0.1:8000/docs>

## Configuration

- `SQLITE_PATH` (optional): custom SQLite file path
  - default: `week2/data/app.db`
- `OLLAMA_MODEL` (optional): model name used by extraction
  - default fallback in code: `llama3.1:8b`

## API Endpoints

Base URL: `http://127.0.0.1:8000`

### Health/UI

- `GET /`
  - Serves the frontend page (`week2/frontend/index.html`)

### Notes

- `GET /notes`
  - Returns all notes
  - Response: `[{ id, content, created_at }, ...]`

- `POST /notes`
  - Creates one note
  - Request body:
    ```json
    { "content": "Meeting notes..." }
    ```
  - Response:
    ```json
    { "id": 1, "content": "Meeting notes...", "created_at": "..." }
    ```

- `GET /notes/{note_id}`
  - Returns one note by ID
  - `404` if note not found

### Action Items

- `POST /action-items/extract`
  - Extracts tasks from text using Ollama and optionally saves the note
  - Request body:
    ```json
    { "text": "TODO: update docs", "save_note": true }
    ```
  - Response (legacy-compatible shape):
    ```json
    {
      "note_id": 12,
      "items": [
        { "id": 101, "text": "Update docs" },
        { "id": 102, "text": "Notify team" }
      ]
    }
    ```

- `GET /action-items`
  - Returns all action items
  - Optional query param: `note_id`
  - Response: `[{ id, note_id, text, done, created_at }, ...]`

- `POST /action-items/{action_item_id}/done`
  - Marks an action item as done/undone
  - Request body:
    ```json
    { "done": true }
    ```
  - Response:
    ```json
    { "id": 101, "done": true }
    ```

## Running Tests

From repository root:

```bash
pytest week2/tests -q
```

### Test groups

- `week2/tests/test_extract.py`
  - Heuristic extraction tests
  - LLM-backed tests are gated by `RUN_OLLAMA_TESTS=1`
- `week2/tests/test_action_items_llm_extract.py`
  - Mocked Ollama tests for endpoint + DB behavior (CI-friendly)

To run LLM integration tests in `test_extract.py`:

```bash
RUN_OLLAMA_TESTS=1 pytest week2/tests/test_extract.py -s -q
```

## Project Structure

```text
week2/
  app/
    main.py                  # FastAPI app, lifespan, middleware, router mount
    db.py                    # SQLite init, migrations, CRUD helpers, transactions
    settings.py              # env-based config helpers
    schemas.py               # API response schemas
    routers/
      notes.py               # /notes endpoints
      action_items.py        # /action-items endpoints
    services/
      extract.py             # heuristic + LLM extraction logic
  frontend/
    index.html               # simple UI (Extract + List Notes)
  tests/
    test_extract.py
    test_action_items_llm_extract.py
```

