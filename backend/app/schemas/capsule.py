from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CapsuleCreate(BaseModel):
    content: str
    title: Optional[str] = None
    visibility: Optional[str] = "private"

class CapsuleResponse(BaseModel):
    id: int
    title: Optional[str] = None
    content: str
    file_url: Optional[str] = None
    file_type: Optional[str] = None
    visibility: str
    created_at: datetime

    class Config:
        from_attributes = True
