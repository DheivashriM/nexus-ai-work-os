from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class ProviderAccount(BaseModel):
    provider_account_id: str
    phone_number: Optional[str] = None
    display_name: Optional[str] = None
    status: str
    connected_on: Optional[str] = None


class ProviderMessage(BaseModel):
    uid: str
    chat_id: str
    sender_phone: Optional[str] = None
    sender_name: Optional[str] = None
    recipient_phone: Optional[str] = None
    recipient_name: Optional[str] = None
    from_me: bool = False
    text: Optional[str] = None
    timestamp: Optional[str] = None
    received_timestamp: Optional[str] = None
    status: Optional[str] = None
    message_type: str = "whatsapp"
    data: dict[str, Any] = {}

    model_config = ConfigDict(extra="allow")