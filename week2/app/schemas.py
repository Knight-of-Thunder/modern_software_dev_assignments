from __future__ import annotations

from pydantic import BaseModel


class NoteOut(BaseModel):
    id: int
    content: str
    created_at: str


class ExtractItemOut(BaseModel):
    id: int
    text: str


class ExtractResponse(BaseModel):
    note_id: int | None
    items: list[ExtractItemOut]


class ActionItemOut(BaseModel):
    id: int
    note_id: int | None
    text: str
    done: bool
    created_at: str


class MarkDoneResponse(BaseModel):
    id: int
    done: bool

