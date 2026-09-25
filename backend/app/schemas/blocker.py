from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from app.schemas.user import UserRead

class BlockerBase(BaseModel):
    description: str
    severity: str = "HIGH" # LOW, MEDIUM, HIGH, CRITICAL

class BlockerCreate(BlockerBase):
    task_id: str

class BlockerUpdate(BaseModel):
    description: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None # OPEN, RESOLVED

class BlockerRead(BlockerBase):
    id: str
    task_id: str
    reported_by: str
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    reporter: Optional[UserRead] = None

    model_config = ConfigDict(from_attributes=True)
