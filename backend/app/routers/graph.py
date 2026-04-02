from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.graph import GraphNode, GraphEdge
from app.services.graph_builder import build_graph_edges_for_node

router = APIRouter(prefix="/api/graph", tags=["graph"])

@router.get("/data")
async def get_graph_data(db: Session = Depends(get_db)):
    """获取图谱数据用于可视化"""
    nodes = db.query(GraphNode).all()
    edges = db.query(GraphEdge).all()
    
    return {
        "nodes": [
            {
                "id": str(n.id),
                "name": n.title,
                "type": n.node_type,
                "content": n.content,
                "ref_id": n.ref_id
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

@router.post("/build")
async def build_all_graph_edges(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """为没有边的实体节点建立关键词关联 (仅为已有数据补全)"""
    nodes = db.query(GraphNode).filter(GraphNode.node_type.in_(["capsule", "deep", "original", "skim"])).all()
    for node in nodes:
        # 检查是否已经有连出去的边
        edge_count = db.query(GraphEdge).filter(GraphEdge.source_node_id == node.id).count()
        if edge_count == 0:
            background_tasks.add_task(build_graph_edges_for_node, db, node.id)
            
    return {"status": "success", "message": "Graph building tasks started in background"}
