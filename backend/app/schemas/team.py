from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from app.schemas.user import UserRead

class TeamMemberBase(BaseModel):
    user_id: str
    role: str = "MEMBER"

class TeamMemberCreate(TeamMemberBase):
    pass

class TeamMemberRead(TeamMemberBase):
    id: str
    team_id: str
    created_at: datetime
    user: Optional[UserRead] = None

    model_config = ConfigDict(from_attributes=True)

class TeamBase(BaseModel):
    name: str
    description: Optional[str] = None

class TeamCreate(TeamBase):
    pass

class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class TeamRead(TeamBase):
    id: str
    created_at: datetime
    updated_at: datetime
    members: List[TeamMemberRead] = []

    model_config = ConfigDict(from_attributes=True)
