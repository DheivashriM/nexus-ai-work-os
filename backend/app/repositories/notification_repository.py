from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.notification import Notification

class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, notification: Notification) -> Notification:
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def get_by_user(self, user_id: str, skip: int = 0, limit: int = 50) -> List[Notification]:
        return self.db.query(Notification).filter(
            Notification.user_id == user_id
        ).order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()

    def get_by_id(self, notification_id: str) -> Optional[Notification]:
        return self.db.query(Notification).filter(Notification.id == notification_id).first()

    def mark_as_read(self, notification: Notification) -> Notification:
        notification.read = True
        self.db.commit()
        self.db.refresh(notification)
        return notification
