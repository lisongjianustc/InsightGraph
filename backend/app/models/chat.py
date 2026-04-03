from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class GlobalConversation(Base):
    __tablename__ = "global_conversations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=True)
    is_favorite = Column(Boolean, default=False)
    dify_conversation_id = Column(String(100), nullable=True) # To continue stream in dify
    history = Column(Text, nullable=True) # JSON array of messages
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())