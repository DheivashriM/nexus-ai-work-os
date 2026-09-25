from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str = "MEMBER" # ADMIN, MANAGER, MEMBER
    status: str = "ACTIVE"
    whatsapp_number: Optional[str] = None
    whatsapp_enabled: bool = False
    whatsapp_notify_blockers: bool = True
    whatsapp_notify_daily_plan: bool = False
    email_privacy_locked: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    status: Optional[str] = None
    password: Optional[str] = None
    whatsapp_number: Optional[str] = None
    whatsapp_enabled: Optional[bool] = None
    whatsapp_notify_blockers: Optional[bool] = None
    whatsapp_notify_daily_plan: Optional[bool] = None
    email_privacy_locked: Optional[bool] = None

class UserRead(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
