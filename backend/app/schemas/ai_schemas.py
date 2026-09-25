from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any

class AIChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ToolExecutionStep(BaseModel):
    step_number: int
    tool_name: str
    description: str
    status: str # EXECUTING, SUCCESS, FAILED, UNAUTHORIZED
    arguments: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None

class AIChatResponse(BaseModel):
    conversation_id: str
    reply: str
    execution_steps: List[ToolExecutionStep] = []
    actions_taken: List[str] = []

class AIMessageRead(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    tool_calls: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AIConversationRead(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[AIMessageRead] = []

    model_config = ConfigDict(from_attributes=True)

class AIActionLogRead(BaseModel):
    id: str
    conversation_id: Optional[str] = None
    user_id: str
    tool_name: str
    target_resource: Optional[str] = None
    risk_level: str
    arguments_json: Optional[Dict[str, Any]] = None
    result_json: Optional[Dict[str, Any]] = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
