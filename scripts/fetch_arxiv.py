import requests
import xml.etree.ElementTree as ET
import json
from datetime import datetime

# API 配置
ARXIV_API_URL = "http://export.arxiv.org/api/query"
INSIGHT_API_URL = "http://localhost:8000/api/feed/incoming"

def fetch_latest_arxiv_papers(category="cs.AI", max_results=10):
    """从 ArXiv API 获取最新论文"""
    print(f"📡 正在从 ArXiv 获取 [{category}] 的最新 {max_results} 篇论文...")
    
    # 不使用 requests 的 params，防止自动 urlencode 冒号
    url = f"{ARXIV_API_URL}?search_query=cat:{category}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"
    
    response = requests.get(url)
    response.raise_for_status()
    
    # 解析 XML
    root = ET.fromstring(response.text)
    namespace = {'atom': 'http://www.w3.org/2005/Atom'}
    
    papers = []
    for entry in root.findall('atom:entry', namespace):
        title = entry.find('atom:title', namespace).text.strip().replace('\n', ' ')
        summary = entry.find('atom:summary', namespace).text.strip().replace('\n', ' ')
        link = entry.find('atom:id', namespace).text.strip()
        published = entry.find('atom:published', namespace).text.strip()
        
        # 提取作者
        authors = [author.find('atom:name', namespace).text for author in entry.findall('atom:author', namespace)]
        
        # 提取分类
        categories = [category.attrib['term'] for category in entry.findall('atom:category', namespace)]
        
        papers.append({
            "title": title,
            "summary": summary,
            "link": link,
            "published": published,
            "authors": authors,
            "categories": categories
        })
        
    print(f"✅ 成功获取 {len(papers)} 篇论文。")
    return papers

def push_to_insight_graph(papers):
    """将论文推送到 FastAPI 后端"""
    print(f"🚀 正在将论文推送至 InsightGraph 后端 ({INSIGHT_API_URL})...")
    
    success_count = 0
    for paper in papers:
        # 构建符合 FeedItemCreate Schema 的数据
        payload = {
            "source": "arxiv",
            "title": f"[ArXiv] {paper['title']}",
            "content": paper['summary'],
            "url": paper['link'],
            "raw_data": {
                "authors": paper['authors'],
                "categories": paper['categories'],
                "published_at": paper['published']
            }
        }
        
        try:
            res = requests.post(INSIGHT_API_URL, json=payload)
            res.raise_for_status()
            success_count += 1
            print(f"  📥 成功写入: {paper['title'][:50]}...")
        except Exception as e:
            print(f"  ❌ 写入失败: {paper['title'][:50]}... 错误: {e}")
            
    print(f"🎉 推送完成！共成功写入 {success_count}/{len(papers)} 篇论文。")

if __name__ == "__main__":
    try:
        # 抓取 cs.AI 领域的最新 5 篇论文
        papers = fetch_latest_arxiv_papers(category="cs.AI", max_results=5)
        push_to_insight_graph(papers)
    except Exception as e:
        print(f"❌ 发生错误: {e}")