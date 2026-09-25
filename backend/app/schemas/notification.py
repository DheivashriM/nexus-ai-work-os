from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class NotificationCreate(BaseModel):
    user_id: str
    type: str
    title: str
    message: str

class NotificationRead(BaseModel):
    id: str
    user_id: str
    type: str
    title: str
    message: str
    read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
