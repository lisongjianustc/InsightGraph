import logging
from sqlalchemy.orm import Session
from app.models.graph import GraphNode, GraphEdge
from app.services.dify_service import dify_client

logger = logging.getLogger(__name__)

async def build_graph_edges_for_node(db: Session, node_id: int, manual_tags: list = None):
    """
    异步任务：为一个新生成的实体节点（Feed 或 Capsule）抽取关键词，
    或者直接使用用户手打的 tags（Daily Note），并建立图谱关联
    """
    node = db.query(GraphNode).filter(GraphNode.id == node_id).first()
    if not node:
        return
        
    if manual_tags is not None:
        # 如果提供了手动 tag（如每日笔记），直接使用它们作为关键词，不走大模型抽取
        keywords = manual_tags
        logger.info(f"Using manual tags for node {node_id}: {keywords}")
    else:
        # 如果没有手动 tag（如闪念胶囊或文献），走大模型自动抽取
        keywords = await dify_client.extract_keywords(node.content or "", node.title or "")
        if not keywords:
            logger.info(f"No keywords extracted for node {node_id}")
            return
        logger.info(f"Extracted keywords for node {node_id}: {keywords}")
    
    # 清理该节点旧的连线
    db.query(GraphEdge).filter(GraphEdge.source_node_id == node.id).delete()
    db.commit()
    
    if not keywords:
        return
        
    for kw in keywords:
        kw = kw.strip()
        if not kw: continue
        # 查找是否已经有该 keyword 的 tag 节点
        tag_node = db.query(GraphNode).filter(
            GraphNode.node_type == "tag", 
            GraphNode.title == kw,
            GraphNode.owner_id == node.owner_id
        ).first()
        if not tag_node:
            tag_node = GraphNode(
                node_type="tag",
                title=kw,
                content=f"Tag: {kw}",
                owner_id=node.owner_id,
                visibility=node.visibility
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
                relation_type="has_tag",
                owner_id=node.owner_id,
                visibility=node.visibility
            )
            db.add(edge)
            
    db.commit()
    logger.info(f"Graph edges built successfully for node {node_id}")
