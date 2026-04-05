from fastapi import FastAPI, Request, BackgroundTasks, Depends, HTTPException, File, UploadFile, Form
from fastapi.responses import StreamingResponse
import logging
from sqlalchemy.orm import Session
from typing import List

from app.services.dify_service import dify_client
from app.core.database import engine, Base, get_db
from app.models.feed import FeedItem, SourceConfig
from app.models.graph import GraphNode, GraphEdge
from app.models.capsule import Capsule
from app.models.chat import GlobalConversation
from app.schemas.feed import FeedItemCreate, FeedItemResponse, ChatRequest, KnowledgeSaveRequest, GlobalChatRequest, SourceConfigCreate, SourceConfigResponse, ChatHistorySync
from app.schemas.capsule import CapsuleCreate
from app.utils.pdf_parser import fetch_arxiv_pdf_text
from app.utils.pdf_translator import translate_pdf_with_pdf2zh
from app.utils.file_parser import parse_file_to_text
from app.routers import graph, search, chat
from app.services.graph_builder import build_graph_edges_for_node

# 自动创建数据库表（生产环境建议使用 Alembic 迁移）
Base.metadata.create_all(bind=engine)

# 配置基础日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from fastapi.middleware.cors import CORSMiddleware

from fastapi.staticfiles import StaticFiles
import os

from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from app.services.rss_service import fetch_all_active_sources

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the background scheduler
    logger.info("Starting APScheduler for background tasks...")
    scheduler = BackgroundScheduler()
    # 每小时自动抓取一次活跃的信息源
    scheduler.add_job(fetch_all_active_sources, 'interval', minutes=60)
    scheduler.start()
    
    # 启动时先执行一次抓取
    scheduler.add_job(fetch_all_active_sources, 'date')
    
    yield
    
    # Shutdown: Shutdown the scheduler
    logger.info("Shutting down APScheduler...")
    scheduler.shutdown()

app = FastAPI(
    title="InsightGraph API",
    description="Knowledge Base System Core Backend for local Web Admin, n8n, and Dify integrations.",
    version="0.1.0",
    lifespan=lifespan
)

# 允许前端跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 生产环境请指定前端 URL，如 http://localhost:5173
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(graph.router)
app.include_router(search.router)
app.include_router(chat.router)

# 确保存放 PDF 的目录存在
os.makedirs("data/pdfs", exist_ok=True)
app.mount("/static/pdfs", StaticFiles(directory="data/pdfs"), name="pdfs")
os.makedirs("uploads/capsules", exist_ok=True)
app.mount("/uploads/capsules", StaticFiles(directory="uploads/capsules"), name="uploads_capsules")

@app.get("/")
async def root():
    return {"message": "Welcome to InsightGraph Backend API!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# ----------------- Feed / 资讯流管理接口 -----------------

@app.post("/api/feed/incoming", response_model=FeedItemResponse)
async def receive_incoming_feed(item: FeedItemCreate, db: Session = Depends(get_db)):
    """
    接收来自 n8n 的自动化抓取数据，暂存到本地数据库。
    """
    logger.info(f"Received new feed from n8n: {item.source} - {item.title}")
    db_item = FeedItem(
        source=item.source,
        title=item.title,
        content=item.content,
        url=item.url,
        raw_data=item.raw_data
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/api/feed/list", response_model=List[FeedItemResponse])
async def list_feeds(skip: int = 0, limit: int = 50, is_saved_to_kb: bool = None, db: Session = Depends(get_db)):
    """
    获取资讯列表（供前端展示）
    """
    query = db.query(FeedItem)
    if is_saved_to_kb is not None:
        query = query.filter(FeedItem.is_saved_to_kb == is_saved_to_kb)
    
    feeds = query.order_by(FeedItem.created_at.desc()).offset(skip).limit(limit).all()
    return feeds

@app.post("/api/chat/upload")
async def upload_global_chat_file(file: UploadFile = File(...)):
    """
    接收前端全局问答的多模态文件，上传到 Dify 并返回 file_id
    """
    content = await file.read()
    try:
        res = await dify_client.upload_file_to_global_chat(content, file.filename, file.content_type)
        # 根据 mime_type 简单判断是图片还是文档
        file_type = "image" if file.content_type and file.content_type.startswith("image/") else "document"
        return {
            "status": "success",
            "file_id": res.get("id"),
            "type": file_type,
            "name": file.filename
        }
    except Exception as e:
        logger.error(f"Failed to upload global chat file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/global")
async def global_chat(req: GlobalChatRequest):
    """
    提供给前端跨文档全局聊天的流式接口
    """
    return StreamingResponse(
        dify_client.global_chat_stream(
            req.query, 
            req.conversation_id, 
            [f.dict() for f in req.files] if req.files else []
        ),
        media_type="text/event-stream"
    )

@app.get("/api/feed/{feed_id}")
async def get_feed_item(feed_id: int, db: Session = Depends(get_db)):
    item = db.query(FeedItem).filter(FeedItem.id == feed_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Feed not found")
    return item

@app.post("/api/feed/{feed_id}/retry")
async def retry_feed_processing(feed_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    单卡片刷新重试机制：重新抓取 PDF 全文（如果缺失）并强制重新生成泛读摘要
    """
    feed_item = db.query(FeedItem).filter(FeedItem.id == feed_id).first()
    if not feed_item:
        raise HTTPException(status_code=404, detail="Feed not found")
        
    # 1. 尝试重新拉取全文 (针对 arXiv)
    if feed_item.source == 'arxiv' and feed_item.url:
        try:
            from app.utils.pdf_parser import fetch_arxiv_pdf_text
            full_text = await fetch_arxiv_pdf_text(feed_item.url)
            if full_text:
                feed_item.full_text = full_text.replace('\x00', '')
                db.commit()
        except Exception as e:
            logger.error(f"Failed to retry fetching arxiv pdf: {e}")
            
    # 2. 清理之前的摘要失败状态或旧缓存
    feed_item.skim_summary = None
    db.commit()
    
    # 3. 重新调用泛读生成
    safe_content = (feed_item.full_text or feed_item.content).replace('\x00', '')
    summary = await dify_client.get_skim_reading_summary(
        content=safe_content,
        title=feed_item.title
    )
    
    feed_item.skim_summary = summary
    db.commit()
    
    return {
        "status": "success",
        "message": "Retry completed",
        "feed": {
            "id": feed_item.id,
            "full_text": feed_item.full_text,
            "skim_summary": feed_item.skim_summary
        }
    }

@app.post("/api/feed/{feed_id}/save_to_kb")
async def save_feed_to_kb(feed_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    前端点击“整合进知识库”按钮时调用此接口。
    将资讯内容发送给 Dify 进行向量化，并更新数据库状态。
    """
    feed_item = db.query(FeedItem).filter(FeedItem.id == feed_id).first()
    if not feed_item:
        raise HTTPException(status_code=404, detail="Feed not found")
        
    if feed_item.is_saved_to_kb:
        return {"status": "already_saved", "message": "This feed is already in the Knowledge Base."}

    # 如果是 arxiv 源且 full_text 为空，主动抓取完整的英文原文 PDF 内容
    if feed_item.source == 'arxiv' and not feed_item.full_text and feed_item.url:
        try:
            from app.utils.pdf_parser import fetch_arxiv_pdf_text
            full_text = await fetch_arxiv_pdf_text(feed_item.url)
            if full_text:
                feed_item.full_text = full_text.replace('\x00', '')
                db.commit()
        except Exception as e:
            logger.error(f"Failed to fetch arxiv pdf text before saving to KB: {e}")

    # 构建发送给 Dify 的内容
    safe_text = (feed_item.full_text or feed_item.content).replace('\x00', '')
    content_to_save = f"# {feed_item.title}\n\n{safe_text}\n\nSource URL: {feed_item.url}"
    
    # 异步调用 Dify
    logger.info(f"Triggering background task to save feed {feed_id} to Dify.")
    background_tasks.add_task(
        dify_client.save_text_to_dataset, 
        text_content=content_to_save, 
        title=f"[{feed_item.source}] {feed_item.title}",
        kb_type="original"
    )
    
    # 本地也保存一份 GraphNode 节点数据
    node = GraphNode(
        node_type="original",
        title=f"[{feed_item.source}] {feed_item.title}",
        content=content_to_save,
        ref_id=feed_id
    )
    db.add(node)
    
    # 更新数据库状态
    feed_item.is_saved_to_kb = True
    db.commit()
    db.refresh(node)
    
    background_tasks.add_task(build_graph_edges_for_node, db, node.id)
    
    return {"status": "processing", "message": "Sent to Dify for embedding."}

@app.post("/api/knowledge/save")
async def save_knowledge_node(req: KnowledgeSaveRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    通用知识库保存接口，用于保存泛读笔记、精读笔记、闪念胶囊等，并支持分类
    """
    # 异步调用 Dify
    logger.info(f"Triggering background task to save knowledge node '{req.title}' to Dify. type: {req.kb_type}")
    background_tasks.add_task(
        dify_client.save_text_to_dataset, 
        text_content=req.content, 
        title=req.title,
        kb_type=req.kb_type
    )
    
    # 本地落库
    node = GraphNode(
        node_type=req.kb_type,
        title=req.title,
        content=req.content,
        ref_id=req.ref_id
    )
    db.add(node)
    
    # 建立简单的边关系 (如果关联了某篇 Feed 原文)
    if req.ref_id:
        original_node = db.query(GraphNode).filter(
            GraphNode.ref_id == req.ref_id, 
            GraphNode.node_type == "original"
        ).first()
        if original_node:
            db.flush() # 获取 node.id
            edge = GraphEdge(
                source_node_id=node.id,
                target_node_id=original_node.id,
                relation_type="extracted_from"
            )
            db.add(edge)
            
    db.commit()
    db.refresh(node)
    
    background_tasks.add_task(build_graph_edges_for_node, db, node.id)
    
    return {"status": "success", "message": f"Saved {req.kb_type} note successfully."}

@app.post("/api/reader/skim")
async def get_feed_skim_summary(feed_id: int, force_regenerate: bool = False, db: Session = Depends(get_db)):
    """
    泛读模式：请求后端根据资讯内容生成泛读总结。
    如果已经生成过且不强制重新生成，则返回缓存结果。
    """
    feed_item = db.query(FeedItem).filter(FeedItem.id == feed_id).first()
    if not feed_item:
        raise HTTPException(status_code=404, detail="Feed not found")
        
    if not force_regenerate and feed_item.skim_summary:
        return {
            "status": "success",
            "feed_id": feed_id,
            "summary": feed_item.skim_summary,
            "cached": True
        }
        
    # 调用 Dify 接口生成总结
    summary = await dify_client.get_skim_reading_summary(
        content=feed_item.content,
        title=feed_item.title
    )
    
    # 固化保存结果
    feed_item.skim_summary = summary
    db.commit()
    
    return {
        "status": "success",
        "feed_id": feed_id,
        "summary": summary,
        "cached": False
    }

@app.post("/api/reader/chat")
async def chat_with_feed(req: ChatRequest, db: Session = Depends(get_db)):
    """
    精读模式：与大模型进行针对性的对话
    """
    feed_item = db.query(FeedItem).filter(FeedItem.id == req.feed_id).first()
    if not feed_item:
        raise HTTPException(status_code=404, detail="Feed not found")
        
    try:
        result = await dify_client.chat_with_document(
            query=req.query,
            content=feed_item.full_text or feed_item.content or "",
            title=feed_item.title or "Unknown Title",
            conversation_id=req.conversation_id
        )
    except Exception as e:
        logger.error(f"Chat exception: {e}")
        return {
            "status": "error",
            "answer": f"内部错误: {e}",
            "conversation_id": ""
        }
    
    return {
        "status": "success",
        "answer": result.get("answer", f"大模型未返回内容或发生错误: {result}"),
        "conversation_id": result.get("conversation_id", "")
    }

@app.get("/api/reader/feed/{feed_id}/deep_read")
async def get_deep_read_info(feed_id: int, db: Session = Depends(get_db)):
    """
    获取单篇 feed 的精读信息（包含聊天记录、翻译缓存，并拉取全文PDF）
    """
    feed_item = db.query(FeedItem).filter(FeedItem.id == feed_id).first()
    if not feed_item:
        raise HTTPException(status_code=404, detail="Feed not found")
        
    # 如果是 arXiv 来源且还没有 full_text，尝试动态抓取
    if feed_item.source and feed_item.source.lower() == "arxiv" and not feed_item.full_text and feed_item.url:
        try:
            full_text = await fetch_arxiv_pdf_text(feed_item.url)
            if full_text:
                feed_item.full_text = full_text
                db.commit()
        except Exception as e:
            logger.error(f"Failed to fetch arxiv pdf: {e}")
            
    return {
        "status": "success",
        "full_text": feed_item.full_text,
        "translated_content": feed_item.translated_content,
        "translated_pdf_url": feed_item.translated_pdf_url,
        "translated_pdf_url_mono": feed_item.translated_pdf_url_mono,
        "deep_conversation_id": feed_item.deep_conversation_id,
        "deep_chat_history": feed_item.deep_chat_history or []
    }

@app.post("/api/reader/feed/{feed_id}/chat_history")
async def save_chat_history(feed_id: int, payload: ChatHistorySync, db: Session = Depends(get_db)):
    """
    同步前端聊天记录到数据库
    """
    feed_item = db.query(FeedItem).filter(FeedItem.id == feed_id).first()
    if not feed_item:
        raise HTTPException(status_code=404, detail="Feed not found")
        
    feed_item.deep_conversation_id = payload.conversation_id
    feed_item.deep_chat_history = payload.history
    db.commit()
    return {"status": "success"}

@app.post("/api/reader/feed/{feed_id}/translate")
async def translate_feed(feed_id: int, force_refresh: bool = False, db: Session = Depends(get_db)):
    """
    全文翻译功能
    如果该源是 arXiv 并且有原文 URL，我们将调用 pdf2zh 提供排版一致的中文 PDF
    如果 force_refresh 为 True，则强制忽略缓存，重新进行翻译
    """
    feed_item = db.query(FeedItem).filter(FeedItem.id == feed_id).first()
    if not feed_item:
        raise HTTPException(status_code=404, detail="Feed not found")
        
    # 如果强制刷新，清理旧缓存文件和数据库记录
    if force_refresh:
        import os
        from pathlib import Path
        data_dir = Path("data/pdfs")
        for suffix in ['-dual.pdf', '-mono.pdf', '-zh.pdf', '_zh.pdf']:
            old_file = data_dir / f"{feed_id}_original{suffix}"
            if old_file.exists():
                try:
                    os.remove(old_file)
                except Exception:
                    pass
        feed_item.translated_pdf_url = None
        feed_item.translated_pdf_url_mono = None
        feed_item.translated_content = None
        db.commit()
        
    # 如果不强制刷新且已经缓存过翻译，直接返回
    elif feed_item.translated_pdf_url or feed_item.translated_pdf_url_mono or feed_item.translated_content:
        return {
            "status": "success",
            "translated_content": feed_item.translated_content,
            "translated_pdf_url": feed_item.translated_pdf_url,
            "translated_pdf_url_mono": feed_item.translated_pdf_url_mono,
            "cached": True
        }
        
    # 如果是 arXiv 论文，我们尝试翻译整个 PDF
    if feed_item.source == "arxiv" and feed_item.url:
        # 获取真实的 pdf URL
        pdf_url = feed_item.url.replace("abs", "pdf") + ".pdf"
        dual_url, mono_url = await translate_pdf_with_pdf2zh(pdf_url, feed_id)
        
        if dual_url or mono_url:
            feed_item.translated_pdf_url = dual_url
            feed_item.translated_pdf_url_mono = mono_url
            db.commit()
            return {
                "status": "success",
                "translated_pdf_url": dual_url,
                "translated_pdf_url_mono": mono_url,
                "translated_content": None,
                "cached": False
            }
            
    # 回退到纯文本翻译
    content_to_translate = feed_item.full_text or feed_item.content
    translated = await dify_client.translate_text(content_to_translate)
    feed_item.translated_content = translated
    db.commit()
    
    return {
        "status": "success",
        "translated_content": translated,
        "translated_pdf_url": None,
        "translated_pdf_url_mono": None,
        "cached": False
    }

@app.post("/api/capsules")
async def create_capsule(capsule: CapsuleCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    创建一条新的闪念胶囊，并自动发送给 Dify 知识库进行向量化。
    """
    # 1. 本地落库保存胶囊记录
    new_capsule = Capsule(
        title=capsule.title,
        content=capsule.content
    )
    db.add(new_capsule)
    db.commit()
    db.refresh(new_capsule)
    
    # 2. 生成 GraphNode 数据用于关联
    capsule_node = GraphNode(
        node_type="capsule",
        title=capsule.title or f"闪念胶囊 #{new_capsule.id}",
        content=capsule.content,
        ref_id=new_capsule.id
    )
    db.add(capsule_node)
    db.commit()

    # 3. 异步发送给 Dify 向量化和图谱关联
    background_tasks.add_task(
        dify_client.save_text_to_dataset,
        text_content=capsule.content,
        title=capsule.title or f"[闪念胶囊] #{new_capsule.id}",
        kb_type="capsule"
    )
    background_tasks.add_task(build_graph_edges_for_node, db, capsule_node.id)

    return {"status": "success", "id": new_capsule.id, "message": "Capsule created and sent to Dify."}

@app.post("/api/capsules/upload")
async def upload_capsule_file(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    接收上传的文件，解析为纯文本，并保存为闪念胶囊（暂不涉及 OCR 图片解析）
    """
    content = await file.read()
    filename = file.filename
    
    try:
        # 如果是图片格式，则调用 Dify 多模态模型进行 OCR 解析
        if file.content_type and file.content_type.startswith('image/'):
            extracted_text = await dify_client.extract_text_from_image(content, filename, file.content_type)
        else:
            # 解析文件内容为文本
            extracted_text = parse_file_to_text(content, filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to parse file {filename}: {e}")
        raise HTTPException(status_code=500, detail="文件解析失败")
        
    if not extracted_text or not extracted_text.strip():
        raise HTTPException(status_code=400, detail="未能从文件中提取到有效内容")

    # 构建胶囊内容，包含文件名以示区分
    capsule_content = f"【文件解析: {filename}】\n\n{extracted_text}"
    title = f"文件: {filename}"
    
    # 将文件保存到本地 uploads 目录以便后续回溯
    file_url = None
    file_type = None
    if file.content_type and (file.content_type.startswith('application/pdf') or 'word' in file.content_type or 'powerpoint' in file.content_type or 'excel' in file.content_type or 'spreadsheet' in file.content_type or file.content_type.startswith('image/')):
        os.makedirs("uploads/capsules", exist_ok=True)
        import uuid
        safe_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join("uploads/capsules", safe_filename)
        with open(file_path, "wb") as f:
            f.write(content)
        file_url = f"/uploads/capsules/{safe_filename}"
        file_type = file.content_type

    # 1. 本地落库
    new_capsule = Capsule(
        title=title,
        content=capsule_content,
        file_url=file_url,
        file_type=file_type
    )
    db.add(new_capsule)
    db.commit()
    db.refresh(new_capsule)
    
    # 2. 生成 GraphNode
    capsule_node = GraphNode(
        node_type="capsule",
        title=title,
        content=capsule_content,
        ref_id=new_capsule.id
    )
    db.add(capsule_node)
    db.commit()

    # 3. 发送给 Dify
    background_tasks.add_task(
        dify_client.save_text_to_dataset,
        text_content=capsule_content,
        title=title,
        kb_type="capsule"
    )
    background_tasks.add_task(build_graph_edges_for_node, db, capsule_node.id)

    return {"status": "success", "id": new_capsule.id, "message": f"文件 {filename} 已成功解析并入库。"}

@app.get("/api/capsules")
async def list_capsules(skip: int = 0, limit: int = 50, keyword: str = None, db: Session = Depends(get_db)):
    """
    获取所有的闪念胶囊列表（支持搜索和分页）
    """
    query = db.query(Capsule)
    if keyword:
        query = query.filter(Capsule.content.ilike(f"%{keyword}%") | Capsule.title.ilike(f"%{keyword}%"))
    
    total = query.count()
    capsules = query.order_by(Capsule.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "items": capsules
    }

@app.put("/api/capsules/{capsule_id}")
async def update_capsule(capsule_id: int, payload: CapsuleCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    更新闪念胶囊的内容，并同步更新知识图谱节点及 Dify 知识库
    """
    capsule = db.query(Capsule).filter(Capsule.id == capsule_id).first()
    if not capsule:
        raise HTTPException(status_code=404, detail="Capsule not found")
        
    capsule.content = payload.content
    # Allow title to be cleared if payload.title is explicitly empty string, but keep if None
    if payload.title is not None:
        capsule.title = payload.title
    db.commit()
    
    # Update GraphNode
    node = db.query(GraphNode).filter(GraphNode.ref_id == str(capsule_id), GraphNode.node_type == 'capsule').first()
    if node:
        node.content = payload.content
        if payload.title is not None:
            node.title = payload.title
        db.commit()
        
    # Update Dify Knowledge Base
    if getattr(capsule, 'dify_document_id', None):
        from app.services.dify_service import DifyService
        import os
        dify_client = DifyService()
        dataset_id = os.getenv("DIFY_DATASET_CAPSULE_ID")
        if dataset_id:
            # First delete the old document
            background_tasks.add_task(
                dify_client.delete_document,
                dataset_id,
                capsule.dify_document_id
            )
            # Then add the new content as a new document and update the dify_document_id
            def update_dify_doc(capsule_id, content, dataset_id):
                try:
                    from app.core.database import get_db
                    new_doc_id = dify_client.save_text_to_dataset(content, dataset_id)
                    if new_doc_id:
                        db_gen = get_db()
                        db_session = next(db_gen)
                        try:
                            c = db_session.query(Capsule).filter(Capsule.id == capsule_id).first()
                            if c:
                                c.dify_document_id = new_doc_id
                                db_session.commit()
                        finally:
                            next(db_gen, None)
                except Exception as e:
                    print(f"Failed to update Dify doc: {e}")
            
            background_tasks.add_task(update_dify_doc, capsule.id, capsule.content, dataset_id)

    return {"status": "success", "message": "Capsule updated successfully"}

@app.delete("/api/capsules/{capsule_id}")
async def delete_capsule(capsule_id: int, db: Session = Depends(get_db)):
    """
    删除闪念胶囊，并级联删除相关的知识图谱节点与关联边
    """
    capsule = db.query(Capsule).filter(Capsule.id == capsule_id).first()
    if not capsule:
        raise HTTPException(status_code=404, detail="Capsule not found")
        
    # Delete GraphNode and Edges
    node = db.query(GraphNode).filter(GraphNode.ref_id == str(capsule_id), GraphNode.node_type == 'capsule').first()
    if node:
        db.query(GraphEdge).filter((GraphEdge.source_node_id == node.id) | (GraphEdge.target_node_id == node.id)).delete()
        db.delete(node)
        
    db.delete(capsule)
    db.commit()
    return {"status": "success", "message": "Capsule deleted successfully"}

# 预留给飞书的 Webhook 回调路由 (处理日常聊天消息存入知识库)
@app.post("/webhook/feishu")
async def feishu_webhook(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    logger.info(f"Received Feishu Event: {body}")
    
    # 飞书要求的 URL Challenge 验证
    if "challenge" in body:
        return {"challenge": body["challenge"]}
    
    # 这里后续可以解析用户的纯文本消息，并异步存入 Dify
    # 假设解析出的用户文本为 user_text
    # background_tasks.add_task(dify_client.save_text_to_dataset, text_content=user_text, title="飞书碎片知识")
    
    return {"status": "received"}

# 预留给 n8n 报告反馈的回调路由 (处理卡片按钮点击)
@app.post("/webhook/n8n/report")
async def n8n_report_webhook(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    logger.info(f"Received n8n Action: {body}")
    
    try:
        # 解析飞书互动卡片按钮传回的 action 和 content
        # 参照之前 n8n 节点配置的 value 结构
        action_value = body.get("action", {}).get("value", {})
        action_type = action_value.get("action")
        content_to_save = action_value.get("content")
        
        if action_type == "save_to_knowledge_base" and content_to_save:
            logger.info("Triggering background task to save report to Dify Knowledge Base.")
            # 使用后台任务异步保存，避免飞书 Webhook 等待超时
            background_tasks.add_task(
                dify_client.save_text_to_dataset, 
                text_content=content_to_save, 
                title="InsightGraph 每日追踪早报入库"
            )
            return {"status": "processing", "message": "Save to knowledge base initiated"}
        else:
            return {"status": "ignored", "message": "No valid action found"}
            
    except Exception as e:
        logger.error(f"Error processing n8n webhook: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/settings/sources", response_model=list[SourceConfigResponse])
async def list_sources(db: Session = Depends(get_db)):
    """获取所有信息源配置"""
    return db.query(SourceConfig).all()

@app.post("/api/settings/sources", response_model=SourceConfigResponse)
async def create_source(payload: SourceConfigCreate, db: Session = Depends(get_db)):
    """新增信息源"""
    new_source = SourceConfig(**payload.dict())
    db.add(new_source)
    db.commit()
    db.refresh(new_source)
    return new_source

@app.put("/api/settings/sources/{source_id}", response_model=SourceConfigResponse)
async def update_source(source_id: int, payload: SourceConfigCreate, db: Session = Depends(get_db)):
    """更新信息源配置"""
    source = db.query(SourceConfig).filter(SourceConfig.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    for key, value in payload.dict().items():
        setattr(source, key, value)
        
    db.commit()
    db.refresh(source)
    return source

@app.delete("/api/settings/sources/{source_id}")
async def delete_source(source_id: int, db: Session = Depends(get_db)):
    """删除信息源"""
    source = db.query(SourceConfig).filter(SourceConfig.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
        
    db.delete(source)
    db.commit()
    return {"status": "success"}

@app.post("/api/settings/sync")
async def trigger_manual_sync(background_tasks: BackgroundTasks):
    """
    手动触发自动源抓取
    """
    from app.services.rss_service import fetch_all_active_sources
    background_tasks.add_task(fetch_all_active_sources)
    return {"status": "success", "message": "Sync task started in background"}

@app.delete("/api/settings/tags/{tag_id}")
async def delete_tag_node(tag_id: int, db: Session = Depends(get_db)):
    """
    删除标签节点以及与其相连的边
    """
    tag_node = db.query(GraphNode).filter(GraphNode.id == tag_id, GraphNode.node_type == 'tag').first()
    if not tag_node:
        raise HTTPException(status_code=404, detail="Tag not found")
        
    # 删除关联边
    db.query(GraphEdge).filter(
        (GraphEdge.source_node_id == tag_id) | (GraphEdge.target_node_id == tag_id)
    ).delete()
    
    # 删除标签节点
    db.delete(tag_node)
    db.commit()
    
    return {"status": "success", "message": "Tag and its relations deleted"}

from sqlalchemy.sql.expression import func

@app.get("/api/review/daily")
async def get_daily_review(db: Session = Depends(get_db)):
    """获取每日温故卡片（随机从胶囊或精读文献中抽取一条）"""
    import random
    
    review_type = random.choice(["capsule", "feed"])
    
    if review_type == "capsule":
        item = db.query(Capsule).order_by(func.random()).first()
        if item:
            return {"type": "capsule", "data": {"id": item.id, "title": item.title, "content": item.content, "date": item.created_at, "file_url": item.file_url, "file_type": item.file_type}}
            
    # 如果没抽到胶囊，或者抽到了 feed，则去查 feed
    item = db.query(FeedItem).filter(FeedItem.status == 'deep_read').order_by(func.random()).first()
    if item:
        return {"type": "feed", "data": {"id": item.id, "title": item.title, "content": item.skim_summary or item.content, "source": item.source, "date": item.created_at}}
        
    # 如果 feed 也没有，再去查一次胶囊兜底
    item = db.query(Capsule).order_by(func.random()).first()
    if item:
        return {"type": "capsule", "data": {"id": item.id, "title": item.title, "content": item.content, "date": item.created_at, "file_url": item.file_url, "file_type": item.file_type}}
        
    return {"type": "none", "data": None}

# -------------------- 其他接口 --------------------
