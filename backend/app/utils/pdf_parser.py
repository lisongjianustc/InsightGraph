import httpx
import logging
import fitz  # PyMuPDF
import io

logger = logging.getLogger(__name__)

async def fetch_arxiv_pdf_text(url: str) -> str:
    """
    将 arxiv 的抽象页链接转为 pdf 链接并提取文本
    例如: http://arxiv.org/abs/2103.00020 -> http://arxiv.org/pdf/2103.00020.pdf
    """
    if "arxiv.org/abs/" in url:
        pdf_url = url.replace("arxiv.org/abs/", "arxiv.org/pdf/") + ".pdf"
    elif "arxiv.org/pdf/" in url:
        pdf_url = url if url.endswith(".pdf") else url + ".pdf"
    else:
        # 如果不是 arxiv，目前暂时返回空或者原样处理
        return ""
        
    logger.info(f"Fetching PDF from {pdf_url}")
        
    try:
        # arXiv 的 API 有时会自动跳到 https，然后返回无后缀的内容
        # 我们用 requests 或者 httpx.AsyncClient 来跟随重定向
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(pdf_url, timeout=60.0)
            response.raise_for_status()
            
            # 检查返回的内容是否真的是 PDF（防止下载到 HTML 错误页）
            content_type = response.headers.get("Content-Type", "")
            if "application/pdf" not in content_type:
                logger.error(f"Expected PDF but got {content_type} from {pdf_url}")
                return ""
            
            # 使用 PyMuPDF 从内存中读取 PDF
            pdf_bytes = response.content
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            text_blocks = []
            for page in doc:
                text_blocks.append(page.get_text())
                
            full_text = "\n".join(text_blocks)
            return full_text
            
    except Exception as e:
        logger.error(f"Failed to fetch or parse PDF from {pdf_url}: {e}")
        return ""
