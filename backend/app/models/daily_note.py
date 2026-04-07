from sqlalchemy import Column, Integer, String, Text, Date, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class DailyNote(Base):
    __tablename__ = "daily_notes"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True, nullable=False) # e.g. 2024-04-06
    content = Column(Text, default="")                           # Markdown original content
    category = Column(String(100), default="未分类", index=True) # Note category
    dify_document_id = Column(String(255), nullable=True)        # Sync to Dify knowledge base
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
