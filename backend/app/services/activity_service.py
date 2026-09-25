from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.activity import Activity
from app.repositories.activity_repository import ActivityRepository

class ActivityService:
    def __init__(self, db: Session):
        self.repo = ActivityRepository(db)

    def log_activity(
        self,
        activity_type: str,
        description: str,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Activity:
        activity = Activity(
            activity_type=activity_type,
            description=description,
            user_id=user_id,
            project_id=project_id,
            task_id=task_id,
            metadata_json=metadata
        )
        return self.repo.create(activity)

    def get_activities(
        self,
        skip: int = 0,
        limit: int = 50,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> List[Activity]:
        return self.repo.get_all(skip=skip, limit=limit, user_id=user_id, project_id=project_id, task_id=task_id)
