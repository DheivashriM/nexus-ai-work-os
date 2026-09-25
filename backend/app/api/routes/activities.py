from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.activity import ActivityRead
from app.services.activity_service import ActivityService

router = APIRouter(prefix="/activities", tags=["Activities"])

@router.get("", response_model=List[ActivityRead])
def get_activities(
    skip: int = 0,
    limit: int = 50,
    user_id: Optional[str] = None,
    project_id: Optional[str] = None,
    task_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = ActivityService(db)
    return service.get_activities(
        skip=skip,
        limit=limit,
        user_id=user_id,
        project_id=project_id,
        task_id=task_id
    )
