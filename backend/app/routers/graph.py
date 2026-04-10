from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.database import get_db
from app.models.graph import GraphNode, GraphEdge
from app.models.user import User
from app.api.deps import get_current_active_user
from app.services.graph_builder import build_graph_edges_for_node
from app.models.feed import FeedItem
from app.models.capsule import Capsule

router = APIRouter(prefix="/api/graph", tags=["graph"])

@router.get("/data")
async def get_graph_data(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """获取图谱数据用于可视化（仅包含用户的私有数据及所有公开数据）"""
    nodes = db.query(GraphNode).filter(
        or_(GraphNode.visibility == 'public', GraphNode.owner_id == current_user.id)
    ).all()
    
    node_ids = [n.id for n in nodes]
    
    edges = db.query(GraphEdge).filter(
        GraphEdge.source_node_id.in_(node_ids),
        GraphEdge.target_node_id.in_(node_ids)
    ).all()
    
    # 提取 original 类型的关联文献 URL 和 capsule 类型的 file_url
    feeds = db.query(FeedItem.id, FeedItem.url).all()
    feed_url_map = {f.id: f.url for f in feeds}
    
    capsules = db.query(Capsule.id, Capsule.file_url).all()
    capsule_file_map = {c.id: c.file_url for c in capsules}
    
    def get_pdf_url(url: str):
        if not url: return None
        if "arxiv.org/abs/" in url:
            return url.replace("arxiv.org/abs/", "arxiv.org/pdf/") + ".pdf"
        elif "arxiv.org/pdf/" in url or url.endswith(".pdf"):
            return url
        return None
    
    return {
        "nodes": [
            {
                "id": str(n.id),
                "name": n.title,
                "type": n.node_type,
                "content": n.content,
                "ref_id": n.ref_id,
                "url": feed_url_map.get(n.ref_id) if n.node_type == 'original' else None,
                "pdf_url": get_pdf_url(feed_url_map.get(n.ref_id)) if n.node_type == 'original' else None,
                "file_url": capsule_file_map.get(n.ref_id) if n.node_type == 'capsule' else None
            } for n in nodes
        ],
        "edges": [
            {
                "source": str(e.source_node_id),
                "target": str(e.target_node_id),
                "relation": e.relation_type
            } for e in edges
        ]
    }

@router.get("/tag/{tag_id}/definition")
async def get_tag_definition(tag_id: int, force: bool = False, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """获取或动态生成标签的专业定义"""
    node = db.query(GraphNode).filter(
        GraphNode.id == tag_id, 
        GraphNode.node_type == 'tag',
        or_(GraphNode.visibility == 'public', GraphNode.owner_id == current_user.id)
    ).first()
    if not node:
        raise HTTPException(status_code=404, detail="Tag not found")
        
    if force or not node.content or node.content.startswith("Tag:") or "获取定义失败" in node.content:
        # Call Dify to generate definition dynamically
        from app.services.dify_service import dify_client
        definition = await dify_client.generate_tag_definition(node.title)
        node.content = definition
        db.commit()
        
    return {"definition": node.content}
        
@router.post("/build")
async def build_all_graph_edges(background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """为没有边的实体节点建立关键词关联 (仅为已有数据补全)"""
    nodes = db.query(GraphNode).filter(
        GraphNode.node_type.in_(["capsule", "deep", "original", "skim"]),
        GraphNode.owner_id == current_user.id
    ).all()
    for node in nodes:
        # 检查是否已经有连出去的边
        edge_count = db.query(GraphEdge).filter(GraphEdge.source_node_id == node.id).count()
        if edge_count == 0:
            background_tasks.add_task(build_graph_edges_for_node, db, node.id)
            
    return {"status": "success", "message": "Graph building tasks started in background"}
