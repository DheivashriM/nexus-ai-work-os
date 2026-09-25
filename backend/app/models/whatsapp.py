import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


def utc_now():
    return datetime.now(timezone.utc)


class WhatsAppAccount(Base):
    __tablename__ = "whatsapp_accounts"
    __table_args__ = (UniqueConstraint("workspace_id", "provider_account_id", name="uq_whatsapp_account_provider"),)

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(64), nullable=False, index=True, default="default")
    provider = Column(String(32), nullable=False, default="meta")
    phone_number = Column(String(64), nullable=True)
    display_name = Column(String(255), nullable=True)
    status = Column(String(32), nullable=False, default="pending")
    provider_account_id = Column(String(128), nullable=False)
    last_connected_at = Column(DateTime(timezone=True), nullable=True)
    last_disconnected_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    conversations = relationship("WhatsAppConversation", back_populates="account")


class WhatsAppConfiguration(Base):
    __tablename__ = "whatsapp_configuration"

    id = Column(Integer, primary_key=True, default=1)
    workspace_id = Column(String(64), nullable=False, unique=True, default="default")
    phone_number_id = Column(String(128), nullable=True)
    access_token_encrypted = Column(Text, nullable=True)
    app_secret_encrypted = Column(Text, nullable=True)
    verify_token_encrypted = Column(Text, nullable=True)
    public_api_url = Column(String(512), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class WhatsAppConversation(Base):
    __tablename__ = "whatsapp_conversations"
    __table_args__ = (UniqueConstraint("workspace_id", "external_conversation_id", name="uq_whatsapp_conversation_external"),)

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(64), nullable=False, index=True, default="default")
    whatsapp_account_id = Column(String(36), ForeignKey("whatsapp_accounts.id"), nullable=False, index=True)
    external_conversation_id = Column(String(128), nullable=False)
    contact_phone = Column(String(64), nullable=True)
    contact_name = Column(String(255), nullable=True)
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    last_message_preview = Column(Text, nullable=True)
    unread_count = Column(Integer, nullable=False, default=0)
    status = Column(String(32), nullable=False, default="open")
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    account = relationship("WhatsAppAccount", back_populates="conversations")
    messages = relationship("WhatsAppMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="WhatsAppMessage.provider_timestamp")


class WhatsAppMessage(Base):
    __tablename__ = "whatsapp_messages"
    __table_args__ = (UniqueConstraint("workspace_id", "external_message_id", name="uq_whatsapp_message_external"),)

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(64), nullable=False, index=True, default="default")
    whatsapp_conversation_id = Column(String(36), ForeignKey("whatsapp_conversations.id"), nullable=False, index=True)
    external_message_id = Column(String(255), nullable=False)
    direction = Column(String(16), nullable=False)
    sender_phone = Column(String(64), nullable=True)
    sender_name = Column(String(255), nullable=True)
    message_type = Column(String(32), nullable=False, default="text")
    body = Column(Text, nullable=True)
    provider_timestamp = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(32), nullable=True)
    media_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    conversation = relationship("WhatsAppConversation", back_populates="messages")