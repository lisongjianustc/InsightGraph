from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from pydantic import BaseModel
import json

from app.core.database import get_db
from app.models.chat import GlobalConversation

router = APIRouter(prefix="/api/global-chat", tags=["global_chat"])

class ConversationCreate(BaseModel):
    title: Optional[str] = None
    dify_conversation_id: Optional[str] = None

class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    is_favorite: Optional[bool] = None
    dify_conversation_id: Optional[str] = None
    history: Optional[List[Any]] = None

@router.get("/conversations")
async def list_conversations(db: Session = Depends(get_db)):
    conversations = db.query(GlobalConversation).order_by(GlobalConversation.updated_at.desc()).all()
    # Don't return huge history in list view, just basic info
    results = []
    for c in conversations:
        results.append({
            "id": c.id,
            "title": c.title,
            "is_favorite": c.is_favorite,
            "dify_conversation_id": c.dify_conversation_id,
            "updated_at": c.updated_at
        })
    return results

@router.get("/conversations/{conv_id}")
async def get_conversation(conv_id: int, db: Session = Depends(get_db)):
    conv = db.query(GlobalConversation).filter(GlobalConversation.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    history = []
    if conv.history:
        try:
            history = json.loads(conv.history)
        except:
            pass
            
    return {
        "id": conv.id,
        "title": conv.title,
        "is_favorite": conv.is_favorite,
        "dify_conversation_id": conv.dify_conversation_id,
        "history": history
    }

@router.post("/conversations")
async def create_conversation(payload: ConversationCreate, db: Session = Depends(get_db)):
    conv = GlobalConversation(
        title=payload.title or "新对话",
        dify_conversation_id=payload.dify_conversation_id
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return {"id": conv.id, "title": conv.title}

@router.put("/conversations/{conv_id}")
async def update_conversation(conv_id: int, payload: ConversationUpdate, db: Session = Depends(get_db)):
    conv = db.query(GlobalConversation).filter(GlobalConversation.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if payload.title is not None:
        conv.title = payload.title
    if payload.is_favorite is not None:
        conv.is_favorite = payload.is_favorite
    if payload.dify_conversation_id is not None:
        conv.dify_conversation_id = payload.dify_conversation_id
    if payload.history is not None:
        conv.history = json.dumps(payload.history, ensure_ascii=False)
        
    db.commit()
    return {"status": "success"}

@router.delete("/conversations/{conv_id}")
async def delete_conversation(conv_id: int, db: Session = Depends(get_db)):
    conv = db.query(GlobalConversation).filter(GlobalConversation.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(conv)
    db.commit()
    return {"status": "success"}