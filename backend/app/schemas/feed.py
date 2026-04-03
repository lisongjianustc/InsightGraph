from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class FeedItemCreate(BaseModel):
    source: str
    title: str
    content: str
    url: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None

class FeedItemResponse(FeedItemCreate):
    id: int
    is_saved_to_kb: bool
    skim_summary: Optional[str] = None
    full_text: Optional[str] = None
    translated_pdf_url: Optional[str] = None # 双语版
    translated_pdf_url_mono: Optional[str] = None # 纯译文版
    created_at: datetime

    class Config:
        from_attributes = True

class ChatHistorySync(BaseModel):
    conversation_id: Optional[str] = None
    history: list

class ChatFile(BaseModel):
    type: str
    transfer_method: str = "local_file"
    upload_file_id: str

class GlobalChatRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = ""
    files: Optional[list[ChatFile]] = []

class SourceConfigCreate(BaseModel):
    name: str
    type: str = "rss"
    url: str
    is_active: bool = True

class SourceConfigResponse(SourceConfigCreate):
    id: int
    
    class Config:
        orm_mode = True

class ChatRequest(BaseModel):
    feed_id: int
    query: str
    conversation_id: Optional[str] = None

class KnowledgeSaveRequest(BaseModel):
    title: str
    content: str
    kb_type: str = "default"  # 'original', 'skim', 'deep', 'capsule'
    ref_id: Optional[int] = None

