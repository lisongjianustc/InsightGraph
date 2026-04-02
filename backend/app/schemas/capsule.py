from pydantic import BaseModel
from typing import Optional

class CapsuleCreate(BaseModel):
    content: str
    title: Optional[str] = None
