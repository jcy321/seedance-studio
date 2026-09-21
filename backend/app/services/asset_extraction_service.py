"""资产提取服务 - 从分镜表格中提取角色、场景、道具、服装等资产信息"""
import json
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.llm_service import LLMService
from app.services.docx_parser import DocxParserService
from app.models import Script, Character, Scene, Item, Costume


class AssetExtractionService:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.docx_parser = DocxParserService()

    async def extract_assets_from_script(
        self,
        db: AsyncSession,
        script: Script
    ) -> Dict[str, List[Dict]]:
        """从剧本中提取所有资产"""
        # 1. 解析docx文件获取分镜数据
        scenes_data = self.docx_parser.parse_docx(script.docx_path)

        # 2. 将所有分镜内容合并为一个文本
        all_content = "\n".join([
            f"镜号{s.get('镜号', '')}: {s.get('镜头内容', '')}"
            for s in scenes_data
        ])

        # 3. 使用LLM提取资产信息
        extraction_result = await self._extract_assets_with_llm(all_content)

        return extraction_result

    async def _extract_assets_with_llm(self, content: str) -> Dict[str, List[Dict]]:
        """使用LLM从内容中提取资产"""
        prompt = f"""请分析以下分镜脚本，提取出所有的角色、场景、道具和服装信息。

分镜脚本：
{content}

请以JSON格式返回，包含以下字段：
{{
  "characters": [
    {{
      "name": "角色名称",
      "gender": "male/female/unknown",
      "description": "角色描述（外貌、特征等）"
    }}
  ],
  "scenes": [
    {{
      "name": "场景名称",
      "description": "场景描述（环境、氛围等）"
    }}
  ],
  "items": [
    {{
      "name": "道具名称",
      "description": "道具描述（外观、用途等）"
    }}
  ],
  "costumes": [
    {{
      "character_name": "角色名称（如果能关联到角色）",
      "name": "服装名称",
      "description": "服装描述（款式、颜色等）"
    }}
  ]
}}

注意：
1. 只提取明确出现的资产，不要臆测
2. 角色名称要统一（同一角色的不同称呼要归一）
3. 描述要具体，便于后续生成图像
4. 如果某类资产没有，返回空数组

只返回JSON，不要其他说明文字。"""

        response = await self.llm_service.generate_text(prompt, use_reasoning=True)

        # 解析JSON响应
        try:
            # 尝试提取JSON（可能包含在markdown代码块中）
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()

            result = json.loads(json_str)
            return result
        except json.JSONDecodeError as e:
            # 如果解析失败，返回空结果
            return {
                "characters": [],
                "scenes": [],
                "items": [],
                "costumes": []
            }

    async def generate_asset_prompt(
        self,
        asset_type: str,
        asset_name: str,
        asset_description: str,
        additional_context: Optional[str] = None
    ) -> str:
        """为资产生成图像提示词"""
        context_text = f"\n相关上下文：{additional_context}" if additional_context else ""

        prompt = f"""请为以下{asset_type}生成一个详细的图像生成提示词（prompt）。

{asset_type}名称：{asset_name}
{asset_type}描述：{asset_description}{context_text}

要求：
1. 提示词要详细具体，包含视觉细节（颜色、材质、光照、构图等）
2. 适合用于AI图像生成（如Stable Diffusion、Midjourney等）
3. 使用英文，专业术语准确
4. 长度控制在100-200词之间
5. 如果是角色，要包含外貌、服装、姿态等
6. 如果是场景，要包含环境、氛围、光线等
7. 如果是道具或服装，要包含材质、细节、风格等

只返回提示词本身，不要其他说明。"""

        return await self.llm_service.generate_text(prompt, use_reasoning=True)

    async def generate_video_prompt(
        self,
        segment_content: str,
        character_images: Dict[str, str],
        scene_image: Optional[str] = None,
        item_images: Optional[Dict[str, str]] = None
    ) -> str:
        """为分镜生成视频提示词"""
        # 构建资产信息
        assets_info = "可用资产：\n"
        if character_images:
            assets_info += "角色：" + ", ".join(character_images.keys()) + "\n"
        if scene_image:
            assets_info += f"场景：已提供\n"
        if item_images:
            assets_info += "道具：" + ", ".join(item_images.keys()) + "\n"

        prompt = f"""请为以下分镜生成一个详细的视频生成提示词（prompt）。

分镜内容：{segment_content}

{assets_info}

要求：
1. 提示词要描述动作、运镜、节奏等视频特有元素
2. 要考虑已有的角色和场景资产，保持一致性
3. 使用英文，适合AI视频生成模型
4. 长度控制在150-250词之间
5. 包含：
   - 镜头运动（推拉摇移跟等）
   - 角色动作和表情
   - 场景氛围和光线变化
   - 时长和节奏感
   - 画面构图

只返回提示词本身，不要其他说明。"""

        return await self.llm_service.generate_text(prompt, use_reasoning=True)

    async def optimize_storyboard(
        self,
        segments: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """使用LLM优化分镜（可选功能）"""
        segments_text = "\n\n".join([
            f"镜号{s.get('镜号', '')}\n镜头内容：{s.get('镜头内容', '')}\n画面：{s.get('画面', '')}"
            for s in segments
        ])

        prompt = f"""请分析以下分镜脚本，提出优化建议。

{segments_text}

请从以下角度分析：
1. 镜头连贯性（是否有跳跃或不连贯的地方）
2. 节奏把控（是否有节奏问题）
3. 视觉表现（是否有更好的视觉呈现方式）
4. 叙事清晰度（是否容易理解故事）

返回JSON格式：
{{
  "overall_assessment": "整体评价",
  "suggestions": [
    {{
      "segment_number": "镜号",
      "issue": "问题描述",
      "suggestion": "优化建议"
    }}
  ],
  "optimized_segments": [
    {{
      "镜号": "...",
      "镜头内容": "...",
      "画面": "..."
    }}
  ]
}}

只返回JSON，不要其他说明。"""

        response = await self.llm_service.generate_text(prompt, use_reasoning=True)

        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()

            result = json.loads(json_str)
            return result.get("optimized_segments", segments)
        except json.JSONDecodeError:
            return segments
