from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
import feedparser
import urllib.parse
from pydantic import BaseModel
import logging

from app.core.database import get_db, SessionLocal
from app.models.feed import FeedItem
from app.services.dify_service import dify_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/search", tags=["search"])

class ImportRequest(BaseModel):
    title: str
    summary: str
    url: str
    authors: list[str]

import re

def build_arxiv_query(user_query: str) -> str:
    """
    将用户输入的自然语言或简单关键词转化为 arXiv 支持的查询语法。
    支持双引号精确匹配，例如："deep learning" medical
    """
    user_query = user_query.strip()
    if any(prefix in user_query for prefix in ['au:', 'ti:', 'abs:', 'cat:', 'all:']):
        return urllib.parse.quote(user_query)
        
    # 使用正则提取带引号的词组和普通词组
    # r'\"(.*?)\"|(\S+)' 会匹配 "deep learning" 或者 medical
    pattern = re.compile(r'\"(.*?)\"|(\S+)')
    matches = pattern.findall(user_query)
    
    terms = []
    for match in matches:
        if match[0]: # 匹配到双引号包裹的短语
            # arXiv 要求双引号短语需要用 %22 包裹
            terms.append(f"all:%22{urllib.parse.quote(match[0])}%22")
        elif match[1]: # 匹配到普通单词
            terms.append(f"all:{urllib.parse.quote(match[1])}")
            
    if not terms:
        return ""
        
    arxiv_query = "+AND+".join(terms)
    return arxiv_query

@router.get("/external")
async def search_external(
    query: str, 
    max_results: int = 10, 
    sort_by: str = "submittedDate", 
    sort_order: str = "descending", 
    db: Session = Depends(get_db)
):
    """
    通过 arXiv API 主动按条件检索文献
    支持自定义排序依据和排序顺序
    """
    if not query:
        return []
        
    try:
        safe_query = build_arxiv_query(query)
        if not safe_query:
            return []
            
        url = f"http://export.arxiv.org/api/query?search_query={safe_query}&sortBy={sort_by}&sortOrder={sort_order}&max_results={max_results}"
        
        logger.info(f"Searching arXiv: {url}")
        feed = feedparser.parse(url)
        results = []
        
        # 处理 feedparser 可能返回的错误 (比如 arXiv API 报错)
        if feed.bozo and hasattr(feed, 'bozo_exception'):
            logger.error(f"Feedparser bozo error: {feed.bozo_exception}")
            return []
            
        # 查询已存在的项目进行去重和状态绑定
        existing_items = {item.url: item for item in db.query(FeedItem).filter(FeedItem.url.isnot(None)).all()}
        
        for entry in feed.entries:
            # 如果标题是 Error，说明 API 返回了错误信息而不是论文列表
            if getattr(entry, 'title', '').strip().lower() == 'error':
                logger.warning(f"arXiv API returned an error entry: {getattr(entry, 'summary', '')}")
                continue
                
            # 某些论文可能没有 link，我们跳过
            if not hasattr(entry, 'link'):
                continue
                
            existing = existing_items.get(entry.link)
            is_imported = existing is not None
            authors = [a.name for a in entry.authors] if hasattr(entry, "authors") else []
            published = entry.published if hasattr(entry, "published") else ""
            
            results.append({
                "title": entry.title,
                "summary": entry.summary,
                "url": entry.link,
                "authors": authors,
                "published": published,
                "is_imported": is_imported,
                "local_id": existing.id if existing else None,
                "status": existing.status if existing else None,
                "skim_summary": existing.skim_summary if existing else None,
                "is_saved_to_kb": existing.is_saved_to_kb if existing else False
            })
            
        return results
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@router.post("/import")
async def import_search_result(req: ImportRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    将单条外部文献入库并触发处理
    """
    existing = db.query(FeedItem).filter(FeedItem.url == req.url).first()
    if existing:
        return {"status": "success", "message": "Already imported", "id": existing.id}
        
    new_item = FeedItem(
        source="arxiv",
        title=req.title,
        content=req.summary,
        url=req.url,
        raw_data={"authors": req.authors}
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    
    # 异步生成摘要的闭包
    async def generate_skim(item_id: int):
        local_db = SessionLocal()
        try:
            item = local_db.query(FeedItem).filter(FeedItem.id == item_id).first()
            if item:
                safe_content = item.content.replace('\x00', '')
                summary = await dify_client.get_skim_reading_summary(content=safe_content, title=item.title)
                item.skim_summary = summary
                local_db.commit()
        except Exception as e:
            logger.error(f"Failed to generate skim for imported item: {e}")
        finally:
            local_db.close()
            
    background_tasks.add_task(generate_skim, new_item.id)
    
    return {"status": "success", "message": "Imported successfully", "id": new_item.id}

class ImportBatchRequest(BaseModel):
    items: list[ImportRequest]

@router.post("/import_batch")
async def import_batch_results(req: ImportBatchRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    批量将选中的外部文献入库并触发处理
    """
    if not req.items:
        return {"status": "success", "imported_count": 0, "items": []}
        
    urls = [item.url for item in req.items]
    existing_items = {item.url: item for item in db.query(FeedItem).filter(FeedItem.url.in_(urls)).all()}
    
    new_items = []
    for item_req in req.items:
        if item_req.url not in existing_items:
            new_item = FeedItem(
                source="arxiv",
                title=item_req.title,
                content=item_req.summary,
                url=item_req.url,
                raw_data={"authors": item_req.authors}
            )
            db.add(new_item)
            new_items.append(new_item)
            
    if new_items:
        db.commit()
        for item in new_items:
            db.refresh(item)
            
    # 异步生成摘要的闭包
    async def generate_skim_batch(item_ids: list[int]):
        local_db = SessionLocal()
        try:
            items = local_db.query(FeedItem).filter(FeedItem.id.in_(item_ids)).all()
            for item in items:
                try:
                    safe_content = item.content.replace('\x00', '')
                    summary = await dify_client.get_skim_reading_summary(content=safe_content, title=item.title)
                    item.skim_summary = summary
                    local_db.commit()
                except Exception as e:
                    logger.error(f"Failed to generate skim for imported item {item.id}: {e}")
        finally:
            local_db.close()
            
    new_item_ids = [item.id for item in new_items]
    if new_item_ids:
        background_tasks.add_task(generate_skim_batch, new_item_ids)
        
    # 构建返回结果，供前端更新状态
    response_items = []
    for item_req in req.items:
        existing = existing_items.get(item_req.url)
        if existing:
            response_items.append({"url": item_req.url, "local_id": existing.id})
        else:
            # 找到刚刚新插入的
            new_inserted = next((n for n in new_items if n.url == item_req.url), None)
            if new_inserted:
                response_items.append({"url": item_req.url, "local_id": new_inserted.id})
                
    return {
        "status": "success", 
        "imported_count": len(new_items), 
        "items": response_items
    }
async def import_search_result(req: ImportRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    将选中的外部文献入库并触发处理
    """
    existing = db.query(FeedItem).filter(FeedItem.url == req.url).first()
    if existing:
        return {"status": "success", "message": "Already imported", "id": existing.id}
        
    new_item = FeedItem(
        source="arxiv",
        title=req.title,
        content=req.summary,
        url=req.url,
        raw_data={"authors": req.authors}
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    
    # 异步生成摘要的闭包
    async def generate_skim(item_id: int):
        local_db = SessionLocal()
        try:
            item = local_db.query(FeedItem).filter(FeedItem.id == item_id).first()
            if item:
                summary = await dify_client.get_skim_reading_summary(content=item.content, title=item.title)
                item.skim_summary = summary
                local_db.commit()
        except Exception as e:
            logger.error(f"Failed to generate skim for imported item: {e}")
        finally:
            local_db.close()
            
    background_tasks.add_task(generate_skim, new_item.id)
    
    return {"status": "success", "message": "Imported successfully", "id": new_item.id}
