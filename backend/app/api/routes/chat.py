from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, status
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.core.database import get_db
from app.core.config import settings
from app.api.deps import get_current_user
from app.models.user import User
from app.services.chat_service import ChatService
from app.schemas.chat import (
    ChannelRead,
    ChatMessageRead,
    ChatMessageCreate,
    DirectChatCreate,
    GroupChannelCreate
)
from app.core.websocket_manager import ws_manager

router = APIRouter(prefix="/chat", tags=["Chat & Messaging"])

@router.get("/channels", response_model=List[ChannelRead])
def get_user_channels(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = ChatService(db)
    return service.get_user_channels(current_user.id)

@router.post("/direct", response_model=ChannelRead)
def get_or_create_direct_chat(
    data: DirectChatCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if data.recipient_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot create direct message with yourself")
    service = ChatService(db)
    return service.get_or_create_direct_chat(current_user.id, data.recipient_id)

@router.post("/group", response_model=ChannelRead)
def create_group_channel(
    data: GroupChannelCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not data.name.strip():
        raise HTTPException(status_code=400, detail="Channel name cannot be empty")
    service = ChatService(db)
    return service.create_group_channel(current_user.id, data.name, data.description, data.member_ids)

@router.get("/channels/{channel_id}/messages", response_model=List[ChatMessageRead])
def get_channel_messages(
    channel_id: str,
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = ChatService(db)
    try:
        return service.get_channel_messages(channel_id, current_user.id, limit)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.post("/channels/{channel_id}/messages", response_model=ChatMessageRead)
async def send_message(
    channel_id: str,
    data: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not data.content.strip():
        raise HTTPException(status_code=400, detail="Message content cannot be empty")
    service = ChatService(db)
    try:
        return await service.send_message(channel_id, current_user.id, data.content, data.message_type or "TEXT")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/channels/{channel_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def mark_channel_read(
    channel_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = ChatService(db)
    service.mark_channel_read(channel_id, current_user.id)

@router.get("/online-users", response_model=List[str])
def get_online_users():
    """Get list of currently connected user IDs."""
    return ws_manager.get_online_users()

# WebSocket Route for Real-time Connection
@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    target_user_id = None
    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            target_user_id = payload.get("sub")
        except JWTError:
            pass

    if not target_user_id and user_id:
        target_user_id = user_id

    if not target_user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await ws_manager.connect(target_user_id, websocket)
    try:
        while True:
            # Keep socket open and listen for client ping/messages
            data = await websocket.receive_text()
            # If client sends a JSON message over websocket
            import json
            try:
                payload = json.loads(data)
                if payload.get("action") == "send_message":
                    service = ChatService(db)
                    ch_id = payload.get("channel_id")
                    content = payload.get("content")
                    if ch_id and content:
                        await service.send_message(ch_id, target_user_id, content)
            except Exception:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(target_user_id, websocket)
