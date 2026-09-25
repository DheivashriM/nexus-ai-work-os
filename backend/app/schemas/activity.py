from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any
from app.schemas.user import UserRead

class ActivityRead(BaseModel):
    id: str
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    activity_type: str
    description: str
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    user: Optional[UserRead] = None

    model_config = ConfigDict(from_attributes=True)
