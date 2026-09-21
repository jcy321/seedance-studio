"""火山方舟图像生成服务"""
import asyncio
import aiohttp
import os
from typing import Optional, List
import json
from pathlib import Path

from app.services.config_service import UserConfig


class VolcanoArkImageService:
    """火山方舟图像生成服务 - Seedream 5.0"""

    def __init__(self, user_config: UserConfig):
        self.api_key = user_config.ark_api_key if hasattr(user_config, 'ark_api_key') else user_config.seedream_api_key
        self.endpoint = user_config.ark_image_endpoint if hasattr(user_config, 'ark_image_endpoint') else user_config.seedream_base_url
        self.model = user_config.ark_image_model if hasattr(user_config, 'ark_image_model') else "doubao-seedream-5-0-260128"

    async def generate_images(
        self,
        prompt: str,
        size: str = "2K",  # 支持: 1K, 2K, 4K
        output_format: str = "png",  # png 或 jpeg
        watermark: bool = False,
        num_images: int = 4
    ) -> List[str]:
        """生成图像，返回图片URL列表（7天有效期）

        Args:
            prompt: 图像描述提示词
            size: 图像尺寸 (1K=1024x1024, 2K=2048x2048, 4K=4096x4096)
            output_format: 输出格式 (png/jpeg)
            watermark: 是否添加水印
            num_images: 生成图片数量

        Returns:
            图片URL列表，每个URL有效期7天
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        images = []

        # 火山方舟图片生成API是同步的，直接返回结果
        async with aiohttp.ClientSession() as session:
            for i in range(num_images):
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "size": size,
                    "output_format": output_format,
                    "watermark": watermark
                }

                async with session.post(self.endpoint, headers=headers, json=payload) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        print(f"图片生成失败 ({i+1}/{num_images}): {resp.status}, {error_text}")
                        continue

                    result = await resp.json()
                    # 根据官方文档，返回格式为 {"data": [{"url": "..."}]}
                    data = result.get("data", [])
                    if data and len(data) > 0:
                        url = data[0].get("url")
                        if url:
                            images.append(url)

                # 避免请求过快
                if i < num_images - 1:
                    await asyncio.sleep(1)

        if not images:
            raise Exception("所有图片生成请求均失败")

        return images

    async def download_image(self, url: str, save_path: str) -> str:
        """下载图片到本地作为备份

        Args:
            url: 图片URL
            save_path: 保存路径

        Returns:
            本地文件路径
        """
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    raise Exception(f"下载图片失败: {resp.status}")

                content = await resp.read()
                with open(save_path, 'wb') as f:
                    f.write(content)

        return save_path


class VolcanoArkVideoService:
    """火山方舟视频生成服务 - Seedance 2.0"""

    def __init__(self, user_config: UserConfig):
        self.api_key = user_config.ark_api_key if hasattr(user_config, 'ark_api_key') else user_config.seedance_api_key
        self.endpoint = user_config.ark_video_endpoint if hasattr(user_config, 'ark_video_endpoint') else user_config.seedance_base_url
        self.model = user_config.ark_video_model if hasattr(user_config, 'ark_video_model') else "doubao-seedance-2-0-260128"

    async def generate_video(
        self,
        prompt: str,
        duration: int = 5,
        ratio: str = "16:9",  # 支持: 16:9, 9:16, 1:1
        reference_images: Optional[List[str]] = None,  # 参考图片URL列表（需要是信任的模型产物）
        reference_videos: Optional[List[str]] = None,  # 参考视频URL列表
        reference_audios: Optional[List[str]] = None,  # 参考音频URL列表
        generate_audio: bool = True,
        watermark: bool = True
    ) -> str:
        """生成视频，返回视频URL

        Args:
            prompt: 视频描述提示词
            duration: 视频时长（秒），支持5-15秒
            ratio: 视频比例 (16:9, 9:16, 1:1)
            reference_images: 参考图片URL列表（必须是同账号Seedream 5.0生成的，30天内有效）
            reference_videos: 参考视频URL列表
            reference_audios: 参考音频URL列表
            generate_audio: 是否生成音频
            watermark: 是否添加水印

        Returns:
            视频URL
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # 构建content数组
        content = [
            {
                "type": "text",
                "text": prompt
            }
        ]

        # 添加参考图片
        if reference_images:
            for img_url in reference_images:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": img_url},
                    "role": "reference_image"
                })

        # 添加参考视频
        if reference_videos:
            for video_url in reference_videos:
                content.append({
                    "type": "video_url",
                    "video_url": {"url": video_url},
                    "role": "reference_video"
                })

        # 添加参考音频
        if reference_audios:
            for audio_url in reference_audios:
                content.append({
                    "type": "audio_url",
                    "audio_url": {"url": audio_url},
                    "role": "reference_audio"
                })

        payload = {
            "model": self.model,
            "content": content,
            "duration": duration,
            "ratio": ratio,
            "generate_audio": generate_audio,
            "watermark": watermark
        }

        async with aiohttp.ClientSession() as session:
            # 创建生成任务
            async with session.post(self.endpoint, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(f"火山方舟视频API请求失败: {resp.status}, {error_text}")
                result = await resp.json()
                task_id = result.get("id")

            # 轮询任务状态
            get_url = f"{self.endpoint}/{task_id}"
            max_retries = 120  # 最多等待60分钟（每30秒查询一次）
            retry_count = 0

            while retry_count < max_retries:
                await asyncio.sleep(30)  # 每30秒查询一次
                retry_count += 1

                async with session.get(get_url, headers=headers) as resp:
                    if resp.status != 200:
                        continue

                    result = await resp.json()
                    status = result.get("status")

                    if status == "succeeded":
                        # 提取视频URL
                        data = result.get("data", {})
                        if isinstance(data, dict):
                            video_url = data.get("video_url") or data.get("url")
                            if video_url:
                                return video_url
                        elif isinstance(data, list) and len(data) > 0:
                            video_url = data[0].get("video_url") or data[0].get("url")
                            if video_url:
                                return video_url
                        raise Exception("未找到视频URL")

                    elif status == "failed":
                        error = result.get("error", {})
                        raise Exception(f"视频生成失败: {error}")

            raise Exception("视频生成超时")

    async def download_video(self, url: str, save_path: str) -> str:
        """下载视频到本地

        Args:
            url: 视频URL
            save_path: 保存路径

        Returns:
            本地文件路径
        """
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    raise Exception(f"下载视频失败: {resp.status}")

                content = await resp.read()
                with open(save_path, 'wb') as f:
                    f.write(content)

        return save_path
