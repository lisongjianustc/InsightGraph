from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from app.core.database import Base

class GraphNode(Base):
    __tablename__ = "graph_nodes"

    id = Column(Integer, primary_key=True, index=True)
    node_type = Column(String(50), index=True)  # 'original', 'skim', 'deep', 'capsule'
    title = Column(String(512), index=True)
    content = Column(Text)
    ref_id = Column(Integer, nullable=True)     # 关联的 FeedItem ID 或 Capsule ID
    dify_doc_id = Column(String(255), nullable=True) # Dify 返回的 Document ID
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 多租户权限隔离字段
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    visibility = Column(String, default="private", index=True) # 'public' or 'private'

class GraphEdge(Base):
    __tablename__ = "graph_edges"

    id = Column(Integer, primary_key=True, index=True)
    source_node_id = Column(Integer, ForeignKey('graph_nodes.id'), index=True)
    target_node_id = Column(Integer, ForeignKey('graph_nodes.id'), index=True)
    relation_type = Column(String(50), index=True) # 'extracted_from', 'relates_to'
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 多租户权限隔离字段
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    visibility = Column(String, default="private", index=True) # 'public' or 'private'
