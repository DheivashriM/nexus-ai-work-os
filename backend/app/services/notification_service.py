from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.repositories.notification_repository import NotificationRepository

class NotificationService:
    def __init__(self, db: Session):
        self.repo = NotificationRepository(db)

    def create_notification(
        self,
        user_id: str,
        type: str,
        title: str,
        message: str
    ) -> Notification:
        notif = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message
        )
        created_notif = self.repo.create(notif)

        # Trigger outbound WhatsApp notification if user has enabled WhatsApp alerts
        try:
            from app.models.user import User
            from app.integrations.whatsapp.meta.provider import MetaWhatsAppProvider
            user = self.repo.db.query(User).filter(User.id == user_id).first()
            if user and user.whatsapp_number and user.whatsapp_enabled:
                if user.whatsapp_notify_blockers or "BLOCKER" in type.upper() or "URGENT" in type.upper():
                    wa_alert = f"🚨 *Nexus Alert: {title}*\n\n{message}"
                    MetaWhatsAppProvider().send_text_message(user.whatsapp_number, wa_alert)
        except Exception as wa_err:
            print(f"[NotificationService] Outbound WA Alert Error: {wa_err}")

        return created_notif

    def get_user_notifications(self, user_id: str, skip: int = 0, limit: int = 50) -> List[Notification]:
        return self.repo.get_by_user(user_id, skip=skip, limit=limit)

    def mark_read(self, notification_id: str) -> Optional[Notification]:
        notif = self.repo.get_by_id(notification_id)
        if notif:
            return self.repo.mark_as_read(notif)
        return None
