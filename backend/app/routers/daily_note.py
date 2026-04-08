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
    category: Optional[str] = "未分类"
    tags: Optional[List[str]] = []

class AIRewriteRequest(BaseModel):
    draft_content: str
    reference_capsule_ids: List[int]
    reference_feed_ids: List[int]
    reference_original_ids: List[int]
    format_type: str # 'card', 'blog', 'polish'

class CategoryCreateRequest(BaseModel):
    name: str

class CategoryRenameRequest(BaseModel):
    old_name: str
    new_name: str

class CategoryUpdateRequest(BaseModel):
    category: str

class AutoCategorizeRequest(BaseModel):
    content: str
    existing_categories: List[str]

@router.get("/dates")
def get_note_dates(db: Session = Depends(get_db)):
    """返回所有存在笔记的日期列表"""
    notes = db.query(DailyNote.date).all()
    return {"dates": [note.date.isoformat() for note in notes]}

@router.get("/categories")
def get_note_categories(db: Session = Depends(get_db)):
    """返回按分类分组的笔记列表"""
    from sqlalchemy import desc
    notes = db.query(DailyNote.date, DailyNote.category).order_by(desc(DailyNote.date)).all()
    grouped = {}
    for note in notes:
        cat = note.category or "未分类"
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append({"date": note.date.isoformat(), "title": f"{note.date.isoformat()} 笔记"})
    
    result = [{"name": cat, "count": len(items), "notes": items} for cat, items in grouped.items()]
    return {"categories": result}

@router.post("/categories")
def create_category(payload: CategoryCreateRequest, db: Session = Depends(get_db)):
    """创建一个空的分类"""
    if not payload.name or not payload.name.strip():
        raise HTTPException(status_code=400, detail="分类名称不能为空")
    
    # 目前设计下，分类是通过挂载到笔记上存在的，
    # 为了实现“空分类”，我们可以先把它塞到 grouped_data 的响应里（由前端或一个单独的设置表维护）。
    # 但为了最快且兼容，我们给 DailyNote 塞一条隐藏的占位记录（或者直接在前端/内存里维护空分类，直到有笔记挂载）。
    # 这里我们采用更正规的做法：创建一个无日期的占位记录，或者前端只展示。
    # 鉴于现有表结构是 daily_note (date unique)，直接建表更合理。
    # 为保持简单，我们允许它创建一条特殊的笔记。
    pass
    # 更好的方案：因为当前是按笔记聚合分类的，如果没笔记就没有分类。
    # 用户点击“新增”时，我们其实不需要立刻存数据库，而是告诉前端“前端临时新增这个分类”即可，
    # 等用户写日记时选了它，它自然就会存入数据库。
    # 但为了响应用户的交互，我们这里返回成功。
    return {"message": "由于当前架构分类是动态聚合的，您可以直接在写日记时输入新分类名。或者通过此接口在前端临时注册。"}

@router.put("/categories/rename")
def rename_category(payload: CategoryRenameRequest, db: Session = Depends(get_db)):
    """重命名一个笔记分类"""
    if not payload.old_name or not payload.new_name:
        raise HTTPException(status_code=400, detail="名称不能为空")
        
    notes = db.query(DailyNote).filter(DailyNote.category == payload.old_name).all()
    for note in notes:
        note.category = payload.new_name
    db.commit()
    return {"message": "success", "count": len(notes)}

@router.delete("/categories/{category_name}")
def delete_category(category_name: str, db: Session = Depends(get_db)):
    """删除一个分类（将该分类下的笔记设为未分类）"""
    notes = db.query(DailyNote).filter(DailyNote.category == category_name).all()
    for note in notes:
        note.category = "未分类"
    db.commit()
    return {"message": "success", "count": len(notes)}

@router.patch("/{note_date}/category")
def update_note_category(note_date: date, payload: CategoryUpdateRequest, db: Session = Depends(get_db)):
    """仅更新每日笔记的分类（用于拖拽等场景）"""
    note = db.query(DailyNote).filter(DailyNote.date == note_date).first()
    if not note:
        raise HTTPException(status_code=404, detail="找不到该日期的笔记")
    note.category = payload.category
    db.commit()
    return {"message": "success", "category": note.category}

@router.post("/auto-categorize")
async def auto_categorize(payload: AutoCategorizeRequest, db: Session = Depends(get_db)):
    """自动给笔记分类并提供建议"""
    if not payload.content or len(payload.content) < 50:
        return {"primary": "未分类", "suggestions": []}
        
    # 获取最近 5 篇已分类的笔记作为 Few-shot Examples
    from sqlalchemy import desc
    recent_notes = db.query(DailyNote).filter(DailyNote.category != "未分类").order_by(desc(DailyNote.created_at)).limit(5).all()
    few_shot_examples = [{"content": n.content[:200], "category": n.category} for n in recent_notes]
        
    dify_client = DifyService()
    result = await dify_client.auto_categorize_note(payload.content, payload.existing_categories, few_shot_examples)
    return result

@router.get("/{note_date}")
def get_daily_note(note_date: date, db: Session = Depends(get_db)):
    note = db.query(DailyNote).filter(DailyNote.date == note_date).first()
    if not note:
        return {"date": note_date, "content": "", "category": "未分类", "tags": []}
    
    tags_list = [t.strip() for t in note.tags.split(",")] if note.tags else []
    return {"date": note.date, "content": note.content, "category": note.category or "未分类", "tags": tags_list}

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
    tags_str = ",".join(payload.tags) if payload.tags else ""
    
    if not note:
        note = DailyNote(date=note_date, content=payload.content, category=payload.category, tags=tags_str)
        db.add(note)
        db.commit()
        db.refresh(note)
        # Create GraphNode
        title = f"{note_date.strftime('%Y-%m-%d')} 每日笔记"
        node = GraphNode(node_type='daily_note', title=title, content=payload.content, ref_id=note.id)
        db.add(node)
        db.commit()
        db.refresh(node)
        background_tasks.add_task(build_graph_edges_for_node, db, node.id, payload.tags)
    else:
        note.content = payload.content
        note.category = payload.category
        note.tags = tags_str
        db.commit()
        # Update GraphNode
        node = db.query(GraphNode).filter(GraphNode.ref_id == str(note.id), GraphNode.node_type == 'daily_note').first()
        if node:
            node.content = payload.content
            db.commit()
            background_tasks.add_task(build_graph_edges_for_node, db, node.id, payload.tags)
            
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
        # 强制截断超长原文，防止 Dify 大模型处理缓慢或 OOM
        if content and len(content) > 10000:
            content = content[:10000] + "\n...[内容已截断]..."
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

    system_prompt += "\n注意：请不要输出任何客套话（如“好的，我正在阅读”、“这就为您生成”等），直接开始输出最终的 Markdown 格式正文。"

    query = f"<reference_materials>\n{context}\n</reference_materials>\n\n<user_draft>\n{request.draft_content}\n</user_draft>\n\n{system_prompt}\n请立刻开始输出最终的 Markdown 格式正文："
    
    return StreamingResponse(
        dify_client.global_chat_stream(query=query),
        media_type="text/event-stream"
    )
