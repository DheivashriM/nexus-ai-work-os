from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from app.schemas.user import UserRead

class ChatMessageCreate(BaseModel):
    content: str
    message_type: Optional[str] = "TEXT"

class ChatMessageRead(BaseModel):
    id: str
    channel_id: str
    sender_id: str
    sender: Optional[UserRead] = None
    content: str
    message_type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ChannelMemberRead(BaseModel):
    id: str
    channel_id: str
    user_id: str
    user: Optional[UserRead] = None
    joined_at: datetime
    last_read_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DirectChatCreate(BaseModel):
    recipient_id: str

class GroupChannelCreate(BaseModel):
    name: str
    description: Optional[str] = None
    member_ids: List[str]

class ChannelRead(BaseModel):
    id: str
    name: Optional[str] = None
    type: str
    description: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    members: List[ChannelMemberRead] = []
    last_message: Optional[ChatMessageRead] = None
    unread_count: int = 0

    model_config = ConfigDict(from_attributes=True)
