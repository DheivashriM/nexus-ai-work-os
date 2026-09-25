from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.ai_schemas import (
    AIChatRequest,
    AIChatResponse,
    AIConversationRead,
    AIActionLogRead
)
from app.agents.agent_service import AIAgentService

router = APIRouter(prefix="/ai", tags=["AI Agent"])

@router.post("/chat", response_model=AIChatResponse)
def chat_with_agent(
    req: AIChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = AIAgentService(db, current_user)
    return service.process_chat(req.message, req.conversation_id)

@router.get("/conversations", response_model=List[AIConversationRead])
def get_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = AIAgentService(db, current_user)
    return service.get_user_conversations()

@router.get("/conversations/{conversation_id}", response_model=AIConversationRead)
def get_conversation_by_id(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = AIAgentService(db, current_user)
    conv = service.get_conversation_by_id(conversation_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found."
        )
    return conv

@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = AIAgentService(db, current_user)
    success = service.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found."
        )

@router.get("/action-logs", response_model=List[AIActionLogRead])
def get_action_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = AIAgentService(db, current_user)
    return service.get_user_action_logs(limit=limit)
