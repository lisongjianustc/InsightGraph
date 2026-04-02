import os
import httpx
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class DifyService:
    def __init__(self):
        # 从环境变量获取 Dify API 基础地址
        self.api_url = os.getenv("DIFY_API_URL", "http://localhost:5001/v1")
        
        # 知识库统一 API Key
        self.api_key = os.getenv("DIFY_API_KEY", "")
        
        # 获取泛读大模型应用 API Key (带有总结模板)
        self.reader_api_key = os.getenv("DIFY_READER_API_KEY", "")
        
        # 获取精读大模型应用 API Key (无预设模板的自由对话应用)
        self.deep_reader_api_key = os.getenv("DIFY_DEEP_READER_API_KEY", self.reader_api_key)
        
        # 获取用于文件解析和 OCR 提取的工作流 API Key
        self.ocr_workflow_api_key = os.getenv("DIFY_OCR_WORKFLOW_API_KEY", "")
        
    async def save_text_to_dataset(self, text_content: str, title: Optional[str] = None, kb_type: str = "default") -> Dict[str, Any]:
        """
        将文本内容保存到 Dify 的知识库中
        所有的知识库共享同一个 API Key，但通过 dataset_id 区分存入哪个库
        """
        if not self.api_key:
            logger.error("DIFY_API_KEY is not set.")
            return {"error": "API key missing"}

        dataset_id = self._get_dataset_id(kb_type)
        if not dataset_id:
            logger.error(f"Missing Dataset ID for kb_type: {kb_type}")
            return {"error": f"Dataset ID missing for {kb_type}"}

        endpoint = f"{self.api_url}/datasets/{dataset_id}/document/create_by_text"
        
        doc_title = title if title else text_content[:20].replace('\n', ' ') + "..."
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "name": doc_title,
            "text": text_content,
            "indexing_technique": "high_quality", # 默认使用高质量索引
            "process_rule": {
                "mode": "automatic" # 使用自动分段和清洗规则
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=180.0
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"Successfully saved text to dataset {dataset_id}")
                return result
        except httpx.ReadTimeout:
            logger.error(f"Dify save_text_to_dataset API ReadTimeout for {dataset_id}")
            return {"error": "Timeout", "details": "The request timed out. Indexing might still be processing in the background."}
        except httpx.HTTPStatusError as e:
            logger.error(f"Dify API Error: {e.response.text}")
            return {"error": f"API Error: {e.response.status_code}", "details": e.response.text}
        except Exception as e:
            import traceback
            logger.error(f"Failed to connect to Dify: {str(e)}\n{traceback.format_exc()}")
            return {"error": "Connection failed", "details": str(e)}

    async def get_skim_reading_summary(self, content: str, title: str) -> str:
        """
        调用 Dify 的 Chat/Workflow API 进行泛读总结
        """
        if not self.reader_api_key:
            logger.warning("DIFY_READER_API_KEY is not set. Using fallback placeholder summary.")
            return f"**【系统提示】**\n未配置 `DIFY_READER_API_KEY`，目前无法调用大模型。\n\n**原文标题**：{title}\n**原文内容片段**：{content[:200]}..."

        endpoint = f"{self.api_url}/chat-messages"
        headers = {
            "Authorization": f"Bearer {self.reader_api_key}",
            "Content-Type": "application/json"
        }
        
        # 构建给大模型的 Prompt
        query = f"请作为一位资深研究员，对以下文章内容进行泛读总结。请提取出文章的【主旨要义】、【核心结论】和【创新点】。要求语言精炼，使用中文输出。\n\n标题：{title}\n内容：{content}"
        
        payload = {
            "inputs": {},
            "query": query,
            "response_mode": "blocking",
            "user": "insight-graph-user"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=60.0
                )
                response.raise_for_status()
                result = response.json()
                return result.get("answer", "大模型未能返回有效总结。")
        except httpx.HTTPStatusError as e:
            logger.error(f"Dify Reader API Error: {e.response.text}")
            return f"请求大模型接口失败：HTTP {e.response.status_code}"
        except Exception as e:
            logger.error(f"Failed to connect to Dify Reader API: {str(e)}")
            return f"连接大模型服务失败：{str(e)}"

    async def chat_with_document(self, query: str, content: str, title: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        精读模式：针对文档上下文与大模型进行对话
        """
        if not self.deep_reader_api_key:
            return {"answer": "未配置 DIFY_DEEP_READER_API_KEY，无法调用大模型对话。"}

        endpoint = f"{self.api_url}/chat-messages"
        headers = {
            "Authorization": f"Bearer {self.deep_reader_api_key}",
            "Content-Type": "application/json"
        }
        
        # 首轮对话时，把文档内容作为上下文塞给大模型
        if not conversation_id:
            truncated_content = content[:30000] + "..." if len(content) > 30000 else content
            
            # 使用更温和且更聚焦的引导语，将其作为一个自由的精读助手
            full_query = (
                f"下面是用户正在阅读的参考文档内容：\n\n"
                f"<document>\n"
                f"标题：{title}\n"
                f"内容：\n{truncated_content}\n"
                f"</document>\n\n"
                f"请你作为一位专业的科研阅读助手，灵活、准确地回答用户提出的问题：\n"
                f"用户的问题：{query}"
            )
        else:
            full_query = query
            
        payload = {
            "inputs": {},
            "query": full_query,
            "response_mode": "blocking",
            "user": "insight-graph-user"
        }
        
        if conversation_id:
            payload["conversation_id"] = conversation_id
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=180.0  # 增加超时时间到 3 分钟，防止长上下文大模型处理超时
                )
                response.raise_for_status()
                return response.json()
        except httpx.ReadTimeout:
            logger.error("Dify Chat API ReadTimeout")
            return {"answer": "请求大模型对话超时：大模型思考时间过长，请稍后再试。"}
        except httpx.HTTPStatusError as e:
            logger.error(f"Dify Chat API Error: {e.response.text}")
            return {"answer": f"请求大模型对话失败：HTTP {e.response.status_code}\n{e.response.text}"}
        except Exception as e:
            logger.error(f"Failed to connect to Dify Chat API: {str(e)}")
            return {"answer": f"连接大模型对话服务失败：{str(e)}"}

    async def translate_text(self, content: str) -> str:
        """
        调用 Dify 大模型进行全文翻译
        """
        if not self.reader_api_key:
            return "未配置 DIFY_READER_API_KEY，无法调用大模型翻译。"

        endpoint = f"{self.api_url}/chat-messages"
        headers = {
            "Authorization": f"Bearer {self.reader_api_key}",
            "Content-Type": "application/json"
        }
        
        # 截取前一部分，防止超长报错（对于 PDF 翻译，截取前 20000 字符，大概够涵盖核心篇幅）
        truncated_content = content[:20000] + "..." if len(content) > 20000 else content
        query = f"请将以下外文内容翻译成流畅、专业的中文。如果原文已经是中文，请对其进行润色和排版优化。请直接输出翻译结果，不要任何多余的解释：\n\n{truncated_content}"
        
        payload = {
            "inputs": {},
            "query": query,
            "response_mode": "blocking",
            "user": "insight-graph-user"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=120.0 # 翻译可能需要较长时间
                )
                response.raise_for_status()
                result = response.json()
                return result.get("answer", "翻译失败：模型未返回结果。")
        except httpx.HTTPStatusError as e:
            logger.error(f"Dify Translate API Error: {e.response.text}")
            return f"请求大模型翻译失败：HTTP {e.response.status_code}"
        except Exception as e:
            logger.error(f"Failed to connect to Dify Translate API: {str(e)}")
            return f"连接大模型翻译服务失败：{str(e)}"

    def _get_dataset_id(self, kb_type: str = "default") -> str:
        """
        根据不同的分类获取对应的 Dataset ID。
        支持的 kb_type: 'original', 'skim', 'deep', 'capsule', 'default'
        """
        env_key = f"DIFY_DATASET_{kb_type.upper()}_ID"
        specific_id = os.getenv(env_key)
        if specific_id:
            return specific_id
        return os.getenv("DIFY_DATASET_ID", "your_dataset_id_here")

# 实例化单例供其他模块使用
dify_client = DifyService()
