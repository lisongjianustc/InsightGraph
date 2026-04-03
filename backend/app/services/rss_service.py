import logging
import feedparser
from sqlalchemy.orm import Session
from app.models.feed import FeedItem
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

ARXIV_URLS = [
    "http://export.arxiv.org/api/query?search_query=cat:cs.CV+OR+cat:cs.AI+OR+cat:cs.LG&sortBy=submittedDate&sortOrder=desc&max_results=5"
]

def fetch_arxiv_rss():
    """
    后台定时任务：抓取最新的 Arxiv 论文并自动存入 FeedItem。
    """
    logger.info("Starting scheduled task: fetch_arxiv_rss")
    db = SessionLocal()
    try:
        new_count = 0
        for url in ARXIV_URLS:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                # 检查是否已存在
                existing = db.query(FeedItem).filter(FeedItem.url == entry.link).first()
                if not existing:
                    new_item = FeedItem(
                        source="arxiv",
                        title=entry.title,
                        content=entry.summary,
                        url=entry.link,
                        raw_data={"authors": [a.name for a in entry.authors]} if hasattr(entry, "authors") else {}
                    )
                    db.add(new_item)
                    new_count += 1
        db.commit()
        logger.info(f"Finished fetch_arxiv_rss. Added {new_count} new items.")
    except Exception as e:
        logger.error(f"Error fetching arxiv RSS: {str(e)}")
    finally:
        db.close()
