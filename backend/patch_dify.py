import sys

with open("backend/app/services/dify_service.py", "r") as f:
    content = f.read()

# Add create_empty_dataset method
new_method = """    async def create_empty_dataset(self, username: str) -> str:
        \"\"\"
        在 Dify 平台动态创建一个专属的私有大模型知识库（Dataset）。
        \"\"\"
        if not self.api_key:
            logger.error("DIFY_API_KEY is not set.")
            raise Exception("DIFY_API_KEY is not set.")

        endpoint = f"{self.api_url}/datasets"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "name": f"InsightGraph_{username}_KnowledgeBase",
            "description": f"Personal knowledge base for {username}",
            "indexing_technique": "high_quality",
            "permission": "only_me",
            "provider": "vendor"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"Successfully created Dify dataset for user {username}: {result.get('id')}")
                return result.get("id")
        except httpx.HTTPStatusError as e:
            logger.error(f"Dify create dataset API Error: {e.response.text}")
            raise Exception(f"API Error: {e.response.status_code} {e.response.text}")
        except Exception as e:
            logger.error(f"Failed to connect to Dify to create dataset: {str(e)}")
            raise e

    async def save_text_to_dataset(self, text_content: str, dataset_id: str, title: Optional[str] = None) -> Dict[str, Any]:
        \"\"\"
        将文本内容保存到用户的 Dify 私有知识库中
        \"\"\"
        if not self.api_key:
            logger.error("DIFY_API_KEY is not set.")
            return {"error": "API key missing"}

        if not dataset_id:
            logger.error(f"Missing Dataset ID")
            return {"error": f"Dataset ID missing"}

        endpoint = f"{self.api_url}/datasets/{dataset_id}/document/create_by_text"
"""

# Replace save_text_to_dataset signature
old_save_text = """    async def save_text_to_dataset(self, text_content: str, title: Optional[str] = None, kb_type: str = "default") -> Dict[str, Any]:
        \"\"\"
        将文本内容保存到 Dify 的知识库中
        所有的知识库共享同一个 API Key，但通过 dataset_id 区分存入哪个库
        \"\"\"
        if not self.api_key:
            logger.error("DIFY_API_KEY is not set.")
            return {"error": "API key missing"}

        dataset_id = self._get_dataset_id(kb_type)
        if not dataset_id:
            logger.error(f"Missing Dataset ID for kb_type: {kb_type}")
            return {"error": f"Dataset ID missing for {kb_type}"}

        endpoint = f"{self.api_url}/datasets/{dataset_id}/document/create_by_text\""""

if old_save_text in content:
    content = content.replace(old_save_text, new_method)
    with open("backend/app/services/dify_service.py", "w") as f:
        f.write(content)
    print("Patched successfully")
else:
    print("Could not find the target string to replace")
