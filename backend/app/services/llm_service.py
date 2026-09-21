"""LLM服务 - 封装LLM调用，支持多种API协议"""
import base64
from typing import Optional
from pathlib import Path

from anthropic import Anthropic
import httpx

from app.services.config_service import UserConfig


class LLMService:
    def __init__(self, user_config: UserConfig):
        self.api_type = user_config.llm_api_type
        self.base_url = user_config.llm_base_url
        self.api_key = user_config.llm_api_key
        self.model_main = user_config.llm_model_main
        self.model_fast = user_config.llm_model_fast

        # 根据API类型初始化客户端
        if self.api_type == "claude":
            self.client = Anthropic(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        else:
            # OpenAI兼容格式和火山方舟使用httpx
            self.client = None

    async def generate_text(self, prompt: str, use_reasoning: bool = False) -> str:
        model_name = self.model_main if use_reasoning else self.model_fast

        if self.api_type == "claude":
            return await self._generate_claude(prompt, model_name)
        elif self.api_type in ["openai", "ark"]:
            return await self._generate_openai_compatible(prompt, model_name)
        else:
            raise ValueError(f"不支持的API类型: {self.api_type}")

    async def _generate_claude(self, prompt: str, model: str) -> str:
        """使用Claude API"""
        response = self.client.messages.create(
            model=model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )

        for block in response.content:
            if hasattr(block, "text"):
                return block.text
        return ""

    async def _generate_openai_compatible(self, prompt: str, model: str) -> str:
        """使用OpenAI兼容API（包括火山方舟）"""
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2000,
        }
        if self.api_type == "ark":
            payload["thinking"] = {"type": "disabled"}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def describe_image(self, image_path: Path) -> str:
        """描述图片内容（使用快速模型）"""
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        if self.api_type == "claude":
            return await self._describe_image_claude(image_data)
        elif self.api_type in ["openai", "ark"]:
            return await self._describe_image_openai_compatible(image_data)
        else:
            raise ValueError(f"不支持的API类型: {self.api_type}")

    async def _describe_image_claude(self, image_data: str) -> str:
        """使用Claude API描述图片"""
        response = self.client.messages.create(
            model=self.model_fast,
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": "用一句话简洁描述这张图片的内容，包括人物、场景、动作等关键信息。",
                    },
                ],
            }],
        )

        for block in response.content:
            if hasattr(block, "text"):
                return block.text
        return ""

    async def _describe_image_openai_compatible(self, image_data: str) -> str:
        """使用OpenAI兼容API描述图片"""
        payload = {
            "model": self.model_fast,
            "messages": [{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}"
                        }
                    },
                    {
                        "type": "text",
                        "text": "用一句话简洁描述这张图片的内容，包括人物、场景、动作等关键信息。"
                    }
                ]
            }],
            "max_tokens": 200,
        }
        if self.api_type == "ark":
            payload["thinking"] = {"type": "disabled"}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def should_use_first_frame(
        self, prev_shot_desc: str, curr_shot_desc: str
    ) -> bool:
        """判断是否需要首帧（使用主模型）"""
        prompt = f"""分析两个连续分镜的内容，判断是否需要将上一个分镜的尾帧作为首帧参考图。

上一個分镜：{prev_shot_desc}
当前分镜：{curr_shot_desc}

判断标准：
1. 推镜/摇镜/移镜等连续性镜头 → 需要首帧
2. 明确提到"接上一镜"、"延续"、"紧接着" → 需要首帧
3. 场景未变，只是角度或距离变化 → 需要首帧
4. 全新场景、角色或完全不同的事件 → 不需要首帧

只返回 "yes" 或 "no"。"""
        result = await self.generate_text(prompt, use_reasoning=True)
        return result.strip().lower().startswith("yes")
