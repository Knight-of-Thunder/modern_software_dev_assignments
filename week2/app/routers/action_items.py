from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from .. import db
from ..schemas import ActionItemOut, ExtractResponse, MarkDoneResponse
from ..services.extract import extract_action_items_llm


router = APIRouter(prefix="/action-items", tags=["action-items"])


@router.post("/extract", response_model=ExtractResponse)
def extract(payload: Dict[str, Any]) -> ExtractResponse:
    text = str(payload.get("text", "")).strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    note_id: Optional[int] = None
    llm_items = extract_action_items_llm(text)
    items = [ai.task for ai in llm_items.action_items if ai.task.strip()]
    if payload.get("save_note"):
        with db.transaction_ctx() as conn:
            note_id = db.insert_note(text, conn=conn)
            ids = db.insert_action_items_structured(llm_items.action_items, note_id=note_id, conn=conn)
    else:
        ids = db.insert_action_items_structured(llm_items.action_items, note_id=None)
    return {"note_id": note_id, "items": [{"id": i, "text": t} for i, t in zip(ids, items)]}


@router.get("", response_model=list[ActionItemOut])
def list_all(note_id: Optional[int] = None) -> List[ActionItemOut]:
    rows = db.list_action_items(note_id=note_id)
    return [
        {
            "id": r["id"],
            "note_id": r["note_id"],
            "text": r["text"],
            "done": bool(r["done"]),
            "created_at": r["created_at"],
        }
        for r in rows
    ]


@router.post("/{action_item_id}/done", response_model=MarkDoneResponse)
def mark_done(action_item_id: int, payload: Dict[str, Any]) -> MarkDoneResponse:
    done = bool(payload.get("done", True))
    db.mark_action_item_done(action_item_id, done)
    return {"id": action_item_id, "done": done}


