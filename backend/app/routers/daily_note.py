from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
import json
import logging

from app.core.database import get_db
from app.models.daily_note import DailyNote
from app.models.capsule import Capsule
from app.models.graph import GraphNode, GraphEdge
from app.services.graph_builder import build_graph_edges_for_node
from app.services.dify_service import DifyService
import os

router = APIRouter(prefix="/api/daily-notes", tags=["daily-notes"])
logger = logging.getLogger(__name__)

class DailyNoteUpdate(BaseModel):
    content: str

class AIRewriteRequest(BaseModel):
    draft_content: str
    reference_capsule_ids: List[int]
    reference_feed_ids: List[int]
    reference_original_ids: List[int]
    format_type: str # 'card', 'blog', 'polish'

@router.get("/dates")
def get_note_dates(db: Session = Depends(get_db)):
    """返回所有存在笔记的日期列表"""
    notes = db.query(DailyNote.date).all()
    return {"dates": [note.date.isoformat() for note in notes]}

@router.get("/{note_date}")
def get_daily_note(note_date: date, db: Session = Depends(get_db)):
    note = db.query(DailyNote).filter(DailyNote.date == note_date).first()
    if not note:
        return {"date": note_date, "content": ""}
    return {"date": note.date, "content": note.content}

async def _update_dify_doc(note_id: int, content: str, dataset_id: str):
    try:
        from app.core.database import get_db
        dify_client = DifyService()
        new_doc_id = await dify_client.save_text_to_dataset(content, dataset_id)
        if new_doc_id:
            db_gen = get_db()
            db_session = next(db_gen)
            try:
                n = db_session.query(DailyNote).filter(DailyNote.id == note_id).first()
                if n:
                    n.dify_document_id = new_doc_id
                    db_session.commit()
            finally:
                next(db_gen, None)
    except Exception as e:
        logger.error(f"Failed to update Dify doc for daily note: {e}")

@router.put("/{note_date}")
def update_daily_note(note_date: date, payload: DailyNoteUpdate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    note = db.query(DailyNote).filter(DailyNote.date == note_date).first()
    
    if not note:
        note = DailyNote(date=note_date, content=payload.content)
        db.add(note)
        db.commit()
        db.refresh(note)
        # Create GraphNode
        title = f"{note_date.strftime('%Y-%m-%d')} 每日笔记"
        node = GraphNode(node_type='daily_note', title=title, content=payload.content, ref_id=note.id)
        db.add(node)
        db.commit()
        db.refresh(node)
        background_tasks.add_task(build_graph_edges_for_node, db, node.id)
    else:
        note.content = payload.content
        db.commit()
        # Update GraphNode
        node = db.query(GraphNode).filter(GraphNode.ref_id == str(note.id), GraphNode.node_type == 'daily_note').first()
        if node:
            node.content = payload.content
            db.commit()
            background_tasks.add_task(build_graph_edges_for_node, db, node.id)
            
    # Update Dify
    dify_client = DifyService()
    dataset_id = os.getenv("DIFY_DATASET_CAPSULE_ID") # Reuse capsule dataset for simple integration, or define a new one. Let's reuse capsule dataset for now.
    if dataset_id:
        if getattr(note, 'dify_document_id', None):
            background_tasks.add_task(dify_client.delete_document, dataset_id, note.dify_document_id)
        background_tasks.add_task(_update_dify_doc, note.id, note.content, dataset_id)

    return {"status": "success", "date": note_date}

@router.post("/ai-rewrite")
async def ai_rewrite(request: AIRewriteRequest, db: Session = Depends(get_db)):
    dify_client = DifyService()
    
    # 查出引用的胶囊内容
    capsules = []
    if request.reference_capsule_ids:
        capsules = db.query(Capsule).filter(Capsule.id.in_(request.reference_capsule_ids)).all()
        
    # [新增] 查出引用的精读文献内容
    import re
    from app.models.feed import FeedItem
    
    # 获取显式通过 API 传过来的 feed_ids 和 original_ids
    feed_ids = set(request.reference_feed_ids)
    original_ids = set(request.reference_original_ids)
    
    # 获取通过草稿内正文引用的 feed_ids 和 original_ids
    feed_id_regex = re.compile(r'\[\[feed:(\d+)\]\]')
    original_id_regex = re.compile(r'\[\[original:(\d+)\]\]')
    
    for x in feed_id_regex.findall(request.draft_content):
        feed_ids.add(int(x))
    for x in original_id_regex.findall(request.draft_content):
        original_ids.add(int(x))
        
    feeds = []
    originals = []
    
    if feed_ids:
        feeds = db.query(FeedItem).filter(FeedItem.id.in_(list(feed_ids))).all()
    if original_ids:
        originals = db.query(FeedItem).filter(FeedItem.id.in_(list(original_ids))).all()
        
    reference_texts = []
    for c in capsules:
        reference_texts.append(f"<reference type='capsule' title='{c.title}'>\n{c.content}\n</reference>")
        
    for f in feeds:
        content = f.skim_summary if f.skim_summary else "无摘要"
        reference_texts.append(f"<reference type='feed_summary' title='{f.title}'>\n{content}\n</reference>")
        
    for o in originals:
        content = o.full_text if o.full_text else o.skim_summary
        reference_texts.append(f"<reference type='feed_original_text' title='{o.title}'>\n{content}\n</reference>")
        
    context = "\n".join(reference_texts) if reference_texts else "无额外参考资料"
    
    # Prompt 设计
    system_prompt = "你是一个专业的知识管理与写作助手。用户正在撰写每日笔记，请根据用户提供的【参考素材】和【原始草稿】，将其重构为高质量的指定格式内容。\n"
    if request.format_type == 'blog':
        system_prompt += "要求：生成带有引言、多级标题和总结的流畅博客文章。自然融合参考素材的内容。"
    elif request.format_type == 'card':
        system_prompt += "要求：提炼核心观点，输出为精炼的无序列表知识卡片，带上适当的 Emoji。"
    elif request.format_type == 'polish':
        system_prompt += "要求：修饰语法，统一行文风格，使其更加流畅和专业，保持原意不变。"
    else:
        system_prompt += "要求：按照用户的要求对文本进行优化。"

    query = f"<reference_materials>\n{context}\n</reference_materials>\n\n<user_draft>\n{request.draft_content}\n</user_draft>\n\n{system_prompt}\n请开始处理："
    
    return StreamingResponse(
        dify_client.global_chat_stream(query=query),
        media_type="text/event-stream"
    )
