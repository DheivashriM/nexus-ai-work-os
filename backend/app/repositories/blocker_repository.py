from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.blocker import Blocker

class BlockerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, blocker_id: str) -> Optional[Blocker]:
        return self.db.query(Blocker).filter(Blocker.id == blocker_id).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> List[Blocker]:
        query = self.db.query(Blocker)
        if status:
            query = query.filter(Blocker.status == status)
        if task_id:
            query = query.filter(Blocker.task_id == task_id)
        return query.order_by(Blocker.created_at.desc()).offset(skip).limit(limit).all()

    def create(self, blocker: Blocker) -> Blocker:
        self.db.add(blocker)
        self.db.commit()
        self.db.refresh(blocker)
        return blocker

    def update(self, blocker: Blocker) -> Blocker:
        self.db.commit()
        self.db.refresh(blocker)
        return blocker
