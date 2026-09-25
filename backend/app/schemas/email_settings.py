from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class EmailSettingsUpdate(BaseModel):
    enabled: bool = True
    email_address: EmailStr
    password: str = Field(..., min_length=1, max_length=512)
    imap_host: str = Field(..., min_length=1, max_length=255)
    imap_port: int = Field(993, ge=1, le=65535)
    smtp_host: str = Field(..., min_length=1, max_length=255)
    smtp_port: int = Field(587, ge=1, le=65535)


class EmailSettingsRead(BaseModel):
    configured: bool
    enabled: bool
    email_address: Optional[EmailStr] = None
    imap_host: Optional[str] = None
    imap_port: Optional[int] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None