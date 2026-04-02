from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from app.core.database import Base

class FeedItem(Base):
    __tablename__ = "feed_items"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), index=True) # 来源，比如 "github", "arxiv"
    title = Column(String(255), index=True)
    content = Column(Text) # 具体的 Markdown 或纯文本内容
    url = Column(String(512), nullable=True) # 原文链接
    authors = Column(JSON, nullable=True)
    keywords = Column(JSON, nullable=True)
    raw_data = Column(JSON, nullable=True) # 保存 n8n 传过来的原始 JSON 数据，备用
    full_text = Column(Text, nullable=True) # 保存完整的原文内容（如 PDF 解析后全文）
    skim_summary = Column(Text, nullable=True)
    deep_conversation_id = Column(String(255), nullable=True)
    deep_chat_history = Column(JSON, nullable=True)
    translated_content = Column(Text, nullable=True)
    translated_pdf_url = Column(String(512), nullable=True) # 双语版
    translated_pdf_url_mono = Column(String(512), nullable=True) # 纯译文版
    
    status = Column(String(50), default="unread")
    is_saved_to_kb = Column(Boolean, default=False) # 是否已整合进知识库
    created_at = Column(DateTime(timezone=True), server_default=func.now())
