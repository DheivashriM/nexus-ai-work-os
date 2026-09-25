from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class WhatsAppAccountRead(BaseModel):
    id: str
    provider: str
    phone_number: Optional[str] = None
    display_name: Optional[str] = None
    status: str
    last_connected_at: Optional[datetime] = None
    last_disconnected_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class WhatsAppStatusRead(BaseModel):
    configured: bool
    connected: bool
    status: str
    accounts: list[WhatsAppAccountRead]


class WhatsAppConfigUpdate(BaseModel):
    phone_number_id: str = Field(..., min_length=1, max_length=128)
    access_token: str = Field(..., min_length=1)
    app_secret: str = ""
    verify_token: str = Field(..., min_length=8, max_length=255)
    public_api_url: str = Field(..., min_length=8, max_length=512)


class WhatsAppConfigRead(BaseModel):
    configured: bool
    phone_number_id: str | None = None
    public_api_url: str | None = None
    webhook_url: str | None = None


class WhatsAppConversationRead(BaseModel):
    id: str
    whatsapp_account_id: str
    external_conversation_id: int
    contact_phone: Optional[str] = None
    contact_name: Optional[str] = None
    last_message_at: Optional[datetime] = None
    last_message_preview: Optional[str] = None
    unread_count: int
    status: str

    model_config = ConfigDict(from_attributes=True)


class WhatsAppMessageRead(BaseModel):
    id: str
    whatsapp_conversation_id: str
    external_message_id: str
    direction: str
    sender_phone: Optional[str] = None
    sender_name: Optional[str] = None
    message_type: str
    body: Optional[str] = None
    provider_timestamp: datetime
    status: Optional[str] = None
    media_metadata: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class WhatsAppSendText(BaseModel):
    body: str = Field(..., min_length=1, max_length=2000)