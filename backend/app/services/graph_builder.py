import logging
from sqlalchemy.orm import Session
from app.models.graph import GraphNode, GraphEdge
from app.services.dify_service import dify_client

logger = logging.getLogger(__name__)

async def build_graph_edges_for_node(db: Session, node_id: int):
    """
    异步任务：为一个新生成的实体节点（Feed 或 Capsule）抽取关键词，
    并建立图谱关联
    """
    node = db.query(GraphNode).filter(GraphNode.id == node_id).first()
    if not node:
        return
        
    keywords = await dify_client.extract_keywords(node.content or "", node.title or "")
    if not keywords:
        logger.info(f"No keywords extracted for node {node_id}")
        return
        
    logger.info(f"Extracted keywords for node {node_id}: {keywords}")
    
    for kw in keywords:
        # 查找是否已经有该 keyword 的 tag 节点
        tag_node = db.query(GraphNode).filter(GraphNode.node_type == "tag", GraphNode.title == kw).first()
        if not tag_node:
            tag_node = GraphNode(
                node_type="tag",
                title=kw,
                content=f"Tag: {kw}"
            )
            db.add(tag_node)
            db.commit()
            db.refresh(tag_node)
            
        # 建立关联 (node -> tag_node)
        edge_exists = db.query(GraphEdge).filter(
            GraphEdge.source_node_id == node.id,
            GraphEdge.target_node_id == tag_node.id
        ).first()
        
        if not edge_exists:
            edge = GraphEdge(
                source_node_id=node.id,
                target_node_id=tag_node.id,
                relation_type="has_tag"
            )
            db.add(edge)
            
    db.commit()
    logger.info(f"Graph edges built successfully for node {node_id}")
