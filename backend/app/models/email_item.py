import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class EmailItem(Base):
    __tablename__ = "email_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    sender = Column(String(255), nullable=False)
    sender_email = Column(String(255), nullable=False)
    subject = Column(String(512), nullable=False)
    body = Column(Text, nullable=False)
    urgency = Column(String(50), default="MEDIUM") # CRITICAL, HIGH, MEDIUM, LOW
    category = Column(String(50), default="GENERAL") # CLIENT_BUG, MEETING_REQUEST, APPROVAL, GENERAL
    ai_summary = Column(Text, nullable=True)
    ai_draft_reply = Column(Text, nullable=True)
    status = Column(String(50), default="UNREAD") # UNREAD, ACTIONED, ARCHIVED
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", backref="emails")
