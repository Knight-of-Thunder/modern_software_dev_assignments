from __future__ import annotations

from contextlib import asynccontextmanager
import logging
from pathlib import Path
import time
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.responses import Response

from .routers import action_items, notes

from .db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Action Item Extractor", lifespan=lifespan)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("week2.app")


@app.middleware("http")
async def request_id_and_logging(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id") or uuid4().hex
    start = time.perf_counter()
    try:
        response: Response = await call_next(request)
    except Exception:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        logger.exception(
            "request_failed method=%s path=%s elapsed_ms=%.2f request_id=%s",
            request.method,
            request.url.path,
            elapsed_ms,
            request_id,
        )
        raise
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    response.headers["X-Request-Id"] = request_id
    logger.info(
        "request_completed method=%s path=%s status=%s elapsed_ms=%.2f request_id=%s",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
        request_id,
    )
    return response


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    html_path = Path(__file__).resolve().parents[1] / "frontend" / "index.html"
    return html_path.read_text(encoding="utf-8")


app.include_router(notes.router)
app.include_router(action_items.router)


static_dir = Path(__file__).resolve().parents[1] / "frontend"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")