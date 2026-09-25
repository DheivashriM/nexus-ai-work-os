from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from app.schemas.user import UserRead

class TaskCommentCreate(BaseModel):
    content: str

class TaskCommentRead(BaseModel):
    id: str
    task_id: str
    user_id: str
    content: str
    created_at: datetime
    updated_at: datetime
    user: Optional[UserRead] = None

    model_config = ConfigDict(from_attributes=True)

class TaskAssignPayload(BaseModel):
    assignee_id: Optional[str] = None

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "TODO" # TODO, IN_PROGRESS, IN_REVIEW, COMPLETED, BLOCKED
    priority: str = "MEDIUM" # LOW, MEDIUM, HIGH, URGENT
    due_date: Optional[datetime] = None

class TaskCreate(TaskBase):
    project_id: str
    assignee_id: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee_id: Optional[str] = None
    due_date: Optional[datetime] = None

class TaskRead(TaskBase):
    id: str
    project_id: str
    assignee_id: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime
    assignee: Optional[UserRead] = None
    creator: Optional[UserRead] = None
    comments: List[TaskCommentRead] = []

    model_config = ConfigDict(from_attributes=True)
