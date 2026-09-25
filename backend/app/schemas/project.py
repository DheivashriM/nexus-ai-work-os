from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from app.schemas.user import UserRead

class ProjectMemberCreate(BaseModel):
    user_id: str
    role: str = "MEMBER"

class ProjectMemberRead(BaseModel):
    id: str
    project_id: str
    user_id: str
    role: str
    created_at: datetime
    user: Optional[UserRead] = None

    model_config = ConfigDict(from_attributes=True)

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = "ACTIVE" # PLANNING, ACTIVE, ON_HOLD, COMPLETED, ARCHIVED
    priority: str = "MEDIUM" # LOW, MEDIUM, HIGH, URGENT
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None

class ProjectCreate(ProjectBase):
    owner_id: str

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    owner_id: Optional[str] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None

class ProjectRead(ProjectBase):
    id: str
    owner_id: str
    created_at: datetime
    updated_at: datetime
    owner: Optional[UserRead] = None
    members: List[ProjectMemberRead] = []

    model_config = ConfigDict(from_attributes=True)
