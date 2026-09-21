from app.models.base import Base
from app.models.user import User
from app.models.user_settings import UserSettings
from app.models.project import Project
from app.models.script import Script
from app.models.storyboard import StoryboardSegment, SegmentStatus
from app.models.character import Character, GenerationStatus as CharacterGenerationStatus
from app.models.asset import UserAsset
from app.models.scene import Scene, SceneType, GenerationStatus as SceneGenerationStatus
from app.models.item import Item, ItemType, GenerationStatus as ItemGenerationStatus
from app.models.costume import Costume, GenerationStatus as CostumeGenerationStatus
from app.models.generation_task import GenerationTask, TaskType, TaskStatus
from app.models.segment_asset import SegmentAsset, AssetType
from app.models.user_asset_relation import UserAssetRelation, RelationType

# Unified GenerationStatus (use CharacterGenerationStatus as the canonical one)
GenerationStatus = CharacterGenerationStatus

__all__ = [
    "Base",
    "User",
    "UserSettings",
    "Project",
    "Script",
    "StoryboardSegment",
    "SegmentStatus",
    "Character",
    "CharacterGenerationStatus",
    "GenerationStatus",
    "UserAsset",
    "Scene",
    "SceneType",
    "SceneGenerationStatus",
    "Item",
    "ItemType",
    "ItemGenerationStatus",
    "Costume",
    "CostumeGenerationStatus",
    "GenerationTask",
    "TaskType",
    "TaskStatus",
    "SegmentAsset",
    "AssetType",
    "UserAssetRelation",
    "RelationType",
]
