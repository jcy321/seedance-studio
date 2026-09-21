"""Seedream API 封装 - 角色图生成"""
import asyncio
import aiohttp
from typing import Optional

from app.services.config_service import UserConfig


class SeedreamService:
    def __init__(self, user_config: UserConfig):
        self.api_key = user_config.seedream_api_key
        self.endpoint = user_config.seedream_base_url
        self.model = user_config.seedream_model

    async def generate_image(self, description: str) -> Optional[str]:
        """生成一张角色参考图，返回图片URL"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "prompt": description,
            "n": 1,
            "size": "1024x1024",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.endpoint, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    raise Exception(f"Seedream API请求失败: {resp.status}")
                result = await resp.json()
                task_id = result.get("id")

            # 轮询任务状态
            get_url = f"{self.endpoint}/{task_id}"
            while True:
                await asyncio.sleep(5)
                async with session.get(get_url, headers=headers) as resp:
                    result = await resp.json()
                    status = result.get("status")

                    if status == "succeeded":
                        data = result.get("data", [])
                        if data:
                            return data[0].get("image_url")
                        return None
                    elif status == "failed":
                        error = result.get("error", {})
                        raise Exception(f"图片生成失败: {error}")
