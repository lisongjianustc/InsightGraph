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

def build_arxiv_query(user_query: str) -> str:
    """
    将用户输入的自然语言或简单关键词转化为 arXiv 支持的查询语法。
    如果用户已经输入了高级语法（如 au:, cat:），则尽量保留；
    否则，将以空格分隔的词汇转化为 AND 关系的全字段检索。
    """
    user_query = user_query.strip()
    # 如果已经包含 arXiv 关键字前缀，则假定用户知道自己在干什么，直接 urlencode
    if any(prefix in user_query for prefix in ['au:', 'ti:', 'abs:', 'cat:', 'all:']):
        return urllib.parse.quote(user_query)
        
    # 否则，将普通关键词按空格分割，并用 AND 连接
    # 例如 "deep learning" -> "all:deep AND all:learning"
    # 或者如果包含引号，可以做更复杂的处理，这里做简单处理
    terms = [term for term in user_query.split() if term]
    if not terms:
        return ""
        
    formatted_terms = [f"all:{term}" for term in terms]
    arxiv_query = "+AND+".join(formatted_terms)
    
    return arxiv_query

@router.get("/external")
async def search_external(query: str, max_results: int = 10, db: Session = Depends(get_db)):
    """
    通过 arXiv API 主动按条件检索文献
    """
    if not query:
        return []
        
    try:
        # 智能构建查询参数
        safe_query = build_arxiv_query(query)
        if not safe_query:
            return []
            
        # 修复 sortOrder=desc 为 descending
        url = f"http://export.arxiv.org/api/query?search_query={safe_query}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"
        
        logger.info(f"Searching arXiv: {url}")
        feed = feedparser.parse(url)
        results = []
        
        # 处理 feedparser 可能返回的错误 (比如 arXiv API 报错)
        if feed.bozo and hasattr(feed, 'bozo_exception'):
            logger.error(f"Feedparser bozo error: {feed.bozo_exception}")
            return []
            
        # 查询已存在的 URLs 进行去重标识
        existing_urls = {item[0] for item in db.query(FeedItem.url).filter(FeedItem.url.isnot(None)).all()}
        
        for entry in feed.entries:
            # 如果标题是 Error，说明 API 返回了错误信息而不是论文列表
            if getattr(entry, 'title', '').strip().lower() == 'error':
                logger.warning(f"arXiv API returned an error entry: {getattr(entry, 'summary', '')}")
                continue
                
            # 某些论文可能没有 link，我们跳过
            if not hasattr(entry, 'link'):
                continue
                
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
