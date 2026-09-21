"""Seedance API 封装 - 视频生成 + 提示词构建"""
import asyncio
import aiohttp
from typing import List, Dict, Optional

from app.services.config_service import UserConfig


class PromptBuilder:
    """提示词构建器 - 版权规避：角色名替换为代指别名"""

    @staticmethod
    def build_prompt(scene_data: Dict, characters: Dict) -> str:
        """构建Seedance提示词"""
        parts = []
        content = scene_data.get("镜头内容", "")
        dialogue = scene_data.get("台词", "")

        # 找出当前分镜中出现的角色
        appearing = []
        for char_name, char_info in characters.items():
            if char_name in content or char_name in dialogue:
                appearing.append((char_name, char_info))

        # 声明涉及的角色
        if appearing:
            male_chars = [c[1]["alias"] for c in appearing if c[1].get("gender") == "male"]
            female_chars = [c[1]["alias"] for c in appearing if c[1].get("gender") == "female"]
            declaration = "本分镜涉及角色："
            if male_chars:
                declaration += "、".join(male_chars)
            if female_chars:
                if male_chars:
                    declaration += "、"
                declaration += "、".join(female_chars)
            parts.append(declaration + "。")

        # 按角色名长度降序替换，避免短名误替换
        sorted_chars = sorted(characters.items(), key=lambda x: len(x[0]), reverse=True)
        modified_content = content
        modified_dialogue = dialogue
        for char_name, char_info in sorted_chars:
            modified_content = modified_content.replace(char_name, char_info["alias"])
            modified_dialogue = modified_dialogue.replace(char_name, char_info["alias"])

        type_info = scene_data.get("景别") or scene_data.get("类型") or ""
        if type_info:
            parts.append(type_info)
        parts.append(modified_content)
        if modified_dialogue and modified_dialogue.strip() and modified_dialogue != "无":
            parts.append(f"台词：{modified_dialogue}")

        return "。".join(parts)


class SeedanceService:
    def __init__(self, user_config: UserConfig):
        self.api_key = user_config.seedance_api_key
        self.endpoint = user_config.seedance_base_url
        self.model = user_config.seedance_model

    async def generate_video(
        self,
        prompt: str,
        duration: int = 10,
        reference_images: Optional[List[str]] = None,
        first_frame: Optional[str] = None,
    ) -> str:
        """调用Seedance 2.0 API生成视频，返回视频URL"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        content = [{"type": "text", "text": prompt}]
        if first_frame:
            content.append({
                "type": "image_url",
                "image_url": {"url": first_frame},
                "role": "first_frame",
            })
        if reference_images:
            for img_url in reference_images:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": img_url},
                    "role": "reference_image",
                })

        payload = {
            "model": self.model,
            "content": content,
            "duration": min(max(duration, 4), 15),
            "ratio": "16:9",
            "generate_audio": True,
            "watermark": True,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.endpoint, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(f"Seedance API请求失败 ({resp.status}): {text}")
                result = await resp.json()
                task_id = result.get("id")

            get_url = f"{self.endpoint}/{task_id}"
            while True:
                await asyncio.sleep(10)
                async with session.get(get_url, headers=headers) as resp:
                    result = await resp.json()
                    status = result.get("status")
                    if status == "succeeded":
                        return result.get("content", {}).get("video_url", "")
                    elif status == "failed":
                        error = result.get("error", {})
                        raise Exception(f"视频生成失败: {error}")
