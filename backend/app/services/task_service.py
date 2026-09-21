"""任务管理服务 - 管理生成任务状态和进度"""
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional, List
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectStatus
from app.models.storyboard import StoryboardSegment, SegmentStatus
from app.repositories.project_repository import ProjectRepository
from app.repositories.storyboard_repository import StoryboardRepository


@dataclass
class TaskInfo:
    task_id: str
    project_id: int
    user_id: int
    status: str  # running, completed, failed, cancelled
    progress: Dict = field(default_factory=lambda: {"done": 0, "total": 0, "current_scene": None})
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    error_message: Optional[str] = None
    final_video_url: Optional[str] = None


class TaskService:
    """轻量级任务管理器 - 内存存储，应用重启后丢失"""

    def __init__(self):
        self._tasks: Dict[str, TaskInfo] = {}

    def create_task(self, project_id: int, user_id: int, total_scenes: int) -> TaskInfo:
        task_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        task = TaskInfo(
            task_id=task_id,
            project_id=project_id,
            user_id=user_id,
            status="running",
            progress={"done": 0, "total": total_scenes, "current_scene": None},
            started_at=now,
        )
        self._tasks[task_id] = task
        return task

    def update_progress(self, task_id: str, done: int, current_scene: Optional[int] = None):
        task = self._tasks.get(task_id)
        if task:
            task.progress["done"] = done
            if current_scene:
                task.progress["current_scene"] = current_scene

    def complete_task(self, task_id: str, video_url: Optional[str] = None):
        task = self._tasks.get(task_id)
        if task:
            task.status = "completed"
            task.completed_at = datetime.now(timezone.utc)
            task.final_video_url = video_url

    def fail_task(self, task_id: str, error: str):
        task = self._tasks.get(task_id)
        if task:
            task.status = "failed"
            task.error_message = error
            task.completed_at = datetime.now(timezone.utc)

    def cancel_task(self, task_id: str) -> bool:
        task = self._tasks.get(task_id)
        if task and task.status == "running":
            task.status = "cancelled"
            return True
        return False

    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        return self._tasks.get(task_id)

    async def get_user_tasks(
        self, user_id: int, db: AsyncSession
    ) -> Dict[str, List[Dict]]:
        """获取用户的生成任务列表（正在生成+已完成）"""
        proj_repo = ProjectRepository(db)
        running = []
        completed = []

        for task in list(self._tasks.values()):
            if task.user_id != user_id:
                continue

            project = await proj_repo.get_by_id(task.project_id)
            title = project.title if project else f"项目#{task.project_id}"

            item = {
                "task_id": task.task_id,
                "project_id": task.project_id,
                "project_title": title,
                "progress": task.progress,
                "status": task.status,
                "started_at": task.started_at,
                "completed_at": task.completed_at,
                "final_video_url": task.final_video_url,
                "error_message": task.error_message,
            }

            if task.status == "running":
                running.append(item)
            elif task.status in ("completed", "failed"):
                completed.append(item)

        return {"generating": running, "completed": completed}
