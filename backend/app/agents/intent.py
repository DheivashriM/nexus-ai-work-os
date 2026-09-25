from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class EntitySlot(BaseModel):
    raw_text: Optional[str] = None
    resolved_id: Optional[str] = None
    resolved_name: Optional[str] = None
    confidence: float = 0.0

class StructuredIntent(BaseModel):
    intent_type: str = Field(..., description="Action or query intent type (assign_task, create_task, get_user_tasks, etc.)")
    actor_id: Optional[str] = Field(None, description="Authenticated user ID performing request")
    
    # Explicit Semantic Role Slots
    assignee: EntitySlot = Field(default_factory=EntitySlot, description="Target assignee user slot")
    task: EntitySlot = Field(default_factory=EntitySlot, description="Target task resource slot")
    project: EntitySlot = Field(default_factory=EntitySlot, description="Target project context filter slot")
    
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None
    reason: Optional[str] = None
    
    missing_fields: List[str] = Field(default_factory=list)
    ambiguities: List[str] = Field(default_factory=list)
    needs_clarification: bool = False
