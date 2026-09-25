import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class Channel(Base):
    __tablename__ = "channels"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=True) # None for Direct Messages, Channel Name (e.g., "engineering") for Group
    type = Column(String, default="DIRECT") # "DIRECT" or "GROUP"
    description = Column(String, nullable=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    members = relationship("ChannelMember", back_populates="channel", cascade="all, delete-orphan")
    messages = relationship("ChatMessage", back_populates="channel", cascade="all, delete-orphan", order_by="ChatMessage.created_at")

class ChannelMember(Base):
    __tablename__ = "channel_members"

    id = Column(String, primary_key=True, default=generate_uuid)
    channel_id = Column(String, ForeignKey("channels.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    joined_at = Column(DateTime(timezone=True), default=utc_now)
    last_read_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    channel = relationship("Channel", back_populates="members")
    user = relationship("User")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    channel_id = Column(String, ForeignKey("channels.id"), nullable=False)
    sender_id = Column(String, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(String, default="TEXT") # "TEXT", "SYSTEM"
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    channel = relationship("Channel", back_populates="messages")
    sender = relationship("User")
