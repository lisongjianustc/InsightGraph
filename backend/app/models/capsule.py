from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class Capsule(Base):
    __tablename__ = "capsules"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=True)
    content = Column(Text)
    file_url = Column(String(500), nullable=True)
    file_type = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 多租户权限隔离字段
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    visibility = Column(String, default="private", index=True) # 'public' or 'private'
