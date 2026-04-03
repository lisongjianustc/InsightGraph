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

@router.get("/external")
async def search_external(query: str, max_results: int = 10, db: Session = Depends(get_db)):
    """
    通过 arXiv API 主动按条件检索文献
    """
    if not query:
        return []
        
    try:
        # 简单拼接查询条件
        safe_query = urllib.parse.quote(query)
        url = f"http://export.arxiv.org/api/query?search_query=all:{safe_query}&sortBy=submittedDate&sortOrder=desc&max_results={max_results}"
        
        logger.info(f"Searching arXiv: {url}")
        feed = feedparser.parse(url)
        results = []
        
        # 查询已存在的 URLs 进行去重标识
        existing_urls = {item[0] for item in db.query(FeedItem.url).filter(FeedItem.url.isnot(None)).all()}
        
        for entry in feed.entries:
            is_imported = entry.link in existing_urls
            authors = [a.name for a in entry.authors] if hasattr(entry, "authors") else []
            published = entry.published if hasattr(entry, "published") else ""
            
            results.append({
                "title": entry.title,
                "summary": entry.summary,
                "url": entry.link,
                "authors": authors,
                "published": published,
                "is_imported": is_imported
            })
            
        return results
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@router.post("/import")
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
