"""角色识别与管理服务 - 从skill.py提取"""
import json
import re
from typing import Dict, List, Optional

from app.services.llm_service import LLMService
from app.services.seedream_service import SeedreamService


class CharacterService:
    def __init__(self, llm_service: LLMService, seedream_service: SeedreamService):
        self.llm = llm_service
        self.seedream = seedream_service

    async def extract_characters(self, scenes_data: List[Dict]) -> Dict:
        """从分镜数据中LLM提取角色信息"""
        all_content = []
        for scene in scenes_data[:10]:
            content = scene.get("镜头内容", "")
            dialogue = scene.get("台词", "")
            if content:
                all_content.append(f"分镜{scene.get('镜号', '?')}: {content}")
            if dialogue and dialogue.strip() and dialogue != "无":
                all_content.append(f"台词: {dialogue}")

        prompt = f"""分析以下剧本分镜，提取所有角色信息。

分镜内容：
{chr(10).join(all_content[:15])}

请识别所有出现的人物角色，并为每个角色生成形象描述。

要求：
1. 只提取人物角色，不要提取地点、物品
2. 形象描述格式：[年龄段][性别]，[外貌特征]，穿[服装]
3. 如果信息不足，根据上下文合理推测
4. 为每个角色分配代号：男角色1、男角色2...、女角色1、女角色2...（按性别分组编号）
5. image_url字段留空

返回JSON格式：
{{
  "原始角色名1": {{
    "alias": "女角色1",
    "gender": "female",
    "description": "22岁年轻女性，短发，穿银色维护服",
    "image_url": ""
  }}
}}

只返回JSON，不要其他内容。"""

        result_text = await self.llm.generate_text(prompt, model="reasoning")
        result_text = re.sub(r"^```json\s*|\s*```$", "", result_text, flags=re.MULTILINE)

        # 解析JSON，尝试多次
        for _ in range(3):
            try:
                characters = json.loads(result_text)
                return characters
            except json.JSONDecodeError:
                result_text = re.sub(r"^[^{]*", "", result_text)
                result_text = re.sub(r"[^}]*$", "", result_text)

        return {}

    @staticmethod
    def generate_alias(characters: Dict) -> Dict:
        """为角色生成代指别名"""
        male_count = 0
        female_count = 0
        unknown_count = 0

        for char_name, char_info in characters.items():
            gender = char_info.get("gender", "unknown")
            if gender == "male":
                male_count += 1
                char_info["alias"] = f"男角色{male_count}"
            elif gender == "female":
                female_count += 1
                char_info["alias"] = f"女角色{female_count}"
            else:
                unknown_count += 1
                char_info["alias"] = f"角色{unknown_count}"

        return characters

    async def generate_character_images(
        self, characters: Dict, count: int = 4
    ) -> Dict:
        """为角色生成候选参考图"""
        for char_name, char_info in characters.items():
            if char_info.get("image_url"):
                continue

            images = []
            for i in range(count):
                try:
                    image_url = await self.seedream.generate_image(
                        char_info["description"]
                    )
                    if image_url:
                        images.append(image_url)
                except Exception:
                    continue

            char_info["candidate_images"] = images

        return characters
