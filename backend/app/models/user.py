import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON, Boolean, Integer, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="MEMBER")  # ADMIN, MANAGER, MEMBER
    status = Column(String(50), nullable=False, default="ACTIVE")  # ACTIVE, INACTIVE
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    knowledge_settings = Column(JSON, nullable=True, default=dict)

    # WhatsApp & Personal Privacy Settings
    whatsapp_number = Column(String(50), nullable=True, index=True)
    whatsapp_enabled = Column(Boolean, default=False, nullable=False)
    whatsapp_notify_blockers = Column(Boolean, default=True, nullable=False)
    whatsapp_notify_daily_plan = Column(Boolean, default=False, nullable=False)
    email_privacy_locked = Column(Boolean, default=True, nullable=False)

    # User-owned email connection. The password is encrypted at rest.
    email_connection_enabled = Column(Boolean, default=False, nullable=False)
    email_address = Column(String(255), nullable=True)
    email_imap_host = Column(String(255), nullable=True)
    email_imap_port = Column(Integer, nullable=True)
    email_smtp_host = Column(String(255), nullable=True)
    email_smtp_port = Column(Integer, nullable=True)
    email_password_encrypted = Column(Text, nullable=True)

    # Relationships
    team_memberships = relationship("TeamMember", back_populates="user", cascade="all, delete-orphan")
    project_memberships = relationship("ProjectMember", back_populates="user", cascade="all, delete-orphan")
    owned_projects = relationship("Project", back_populates="owner")
    assigned_tasks = relationship("Task", foreign_keys="Task.assignee_id", back_populates="assignee")
    created_tasks = relationship("Task", foreign_keys="Task.created_by", back_populates="creator")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
