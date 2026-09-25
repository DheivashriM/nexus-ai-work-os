from typing import Optional
from pydantic import BaseModel, Field

class EmailSimulateRequest(BaseModel):
    sender: str = Field(..., description="Sender Name (e.g. 'John Client')")
    sender_email: str = Field(..., description="Sender Email (e.g. 'john@clientcompany.com')")
    subject: str = Field(..., description="Email Subject Line")
    body: str = Field(..., description="Email Body Content")

class EmailItemResponse(BaseModel):
    id: str
    user_id: str
    sender: str
    sender_email: str
    subject: str
    body: str
    urgency: str
    category: str
    ai_summary: Optional[str] = None
    ai_draft_reply: Optional[str] = None
    status: str
    created_at: str

    class Config:
        from_attributes = True

class SendEmailReplyRequest(BaseModel):
    recipient_email: Optional[str] = Field(None, description="Optional target recipient email address")
    reply_body: Optional[str] = Field(None, description="Custom or edited reply body")
