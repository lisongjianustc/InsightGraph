import os
import logging
import asyncio
import httpx
from pathlib import Path
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

async def translate_pdf_with_pdf2zh(pdf_url: str, feed_id: int) -> Tuple[Optional[str], Optional[str]]:
    """
    下载 PDF 并使用 pdf2zh 翻译整个文件。
    返回: (双语版路径, 纯中文版路径)
    """
    import sys
    
    data_dir = Path("data/pdfs")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    local_pdf_path = data_dir / f"{feed_id}_original.pdf"
    dual_pdf_path = data_dir / f"{feed_id}_original-dual.pdf"
    mono_pdf_path = data_dir / f"{feed_id}_original-mono.pdf"
    
    # 1. 下载 PDF
    if not local_pdf_path.exists():
        logger.info(f"Downloading PDF from {pdf_url} to {local_pdf_path}")
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(pdf_url, timeout=60.0)
                response.raise_for_status()
                with open(local_pdf_path, 'wb') as f:
                    f.write(response.content)
        except Exception as e:
            logger.error(f"Failed to download PDF for translation: {e}")
            return None, None
            
    # 2. 如果已经翻译过了，直接返回
    if dual_pdf_path.exists() and mono_pdf_path.exists():
        return f"/static/pdfs/{dual_pdf_path.name}", f"/static/pdfs/{mono_pdf_path.name}"
        
    # 3. 调用 pdf2zh 进行翻译
    logger.info(f"Translating PDF: {local_pdf_path} using pdf2zh...")
    try:
        process = await asyncio.create_subprocess_exec(
            "pdf2zh",
            str(local_pdf_path),
            "-o", str(data_dir),
            "-s", "google",
            "-f", ".*Math.*|.*CM.*|.*SY.*", # 匹配常见的数学字体
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"pdf2zh failed with code {process.returncode}: {stderr.decode()}")
            return None, None
            
        logger.info(f"pdf2zh translation completed for {feed_id}")
        
        dual_url = None
        mono_url = None
        
        if dual_pdf_path.exists():
            dual_url = f"/static/pdfs/{dual_pdf_path.name}"
        if mono_pdf_path.exists():
            mono_url = f"/static/pdfs/{mono_pdf_path.name}"
            
        if not dual_url and not mono_url:
            logger.error(f"Translated PDFs not found. stdout: {stdout.decode()} stderr: {stderr.decode()}")
            
        return dual_url, mono_url
            
    except Exception as e:
        logger.error(f"Exception during PDF translation: {e}")
        return None, None
