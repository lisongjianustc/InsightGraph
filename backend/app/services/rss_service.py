import logging
import feedparser
from sqlalchemy.orm import Session
from app.models.feed import FeedItem, SourceConfig
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

def fetch_all_active_sources():
    """
    后台定时任务：抓取所有激活的信息源（RSS/Atom）并自动存入 FeedItem。
    """
    logger.info("Starting scheduled task: fetch_all_active_sources")
    db = SessionLocal()
    try:
        sources = db.query(SourceConfig).filter(SourceConfig.is_active == True).all()
        
        # 预设一个默认源，防止初始无数据
        if not sources:
            logger.info("No active sources found. Creating default arxiv source.")
            default_source = SourceConfig(
                name="arxiv",
                type="rss",
                url="http://export.arxiv.org/api/query?search_query=cat:cs.CV+OR+cat:cs.AI+OR+cat:cs.LG&sortBy=submittedDate&sortOrder=desc&max_results=5",
                is_active=True
            )
            db.add(default_source)
            db.commit()
            db.refresh(default_source)
            sources = [default_source]

        total_new = 0
        for source in sources:
            new_count = 0
            logger.info(f"Fetching from source: {source.name} ({source.url})")
            feed = feedparser.parse(source.url)
            
            for entry in feed.entries:
                # 检查是否已存在 (根据链接去重)
                existing = db.query(FeedItem).filter(FeedItem.url == entry.link).first()
                if not existing:
                    # 针对 arXiv 的特殊处理：提取作者
                    raw_data = {}
                    if hasattr(entry, "authors"):
                        raw_data["authors"] = [a.name for a in entry.authors]
                        
                    new_item = FeedItem(
                        source=source.name,
                        title=entry.title,
                        content=entry.summary,
                        url=entry.link,
                        raw_data=raw_data
                    )
                    db.add(new_item)
                    new_count += 1
            total_new += new_count
            logger.info(f"Finished fetching {source.name}. Added {new_count} new items.")
            
        db.commit()
        logger.info(f"Finished fetch_all_active_sources. Total {total_new} new items added.")
    except Exception as e:
        logger.error(f"Error fetching active sources: {str(e)}")
    finally:
        db.close()
