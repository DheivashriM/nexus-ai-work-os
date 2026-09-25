from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.activity import Activity

class ActivityRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, activity: Activity) -> Activity:
        self.db.add(activity)
        self.db.commit()
        self.db.refresh(activity)
        return activity

    def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> List[Activity]:
        query = self.db.query(Activity)
        if user_id:
            query = query.filter(Activity.user_id == user_id)
        if project_id:
            query = query.filter(Activity.project_id == project_id)
        if task_id:
            query = query.filter(Activity.task_id == task_id)
        return query.order_by(Activity.created_at.desc()).offset(skip).limit(limit).all()
