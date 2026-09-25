from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.chat_repository import ChatRepository
from app.schemas.chat import ChannelRead, ChatMessageRead, ChatMessageCreate, ChannelMemberRead
from app.schemas.user import UserRead
from app.models.chat import Channel, ChatMessage
from app.core.websocket_manager import ws_manager

class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ChatRepository(db)

    def get_user_channels(self, user_id: str) -> List[ChannelRead]:
        channels = self.repo.get_user_channels(user_id)
        result = []
        for ch in channels:
            # Determine last message
            last_msg = ch.messages[-1] if ch.messages else None
            last_msg_schema = ChatMessageRead.model_validate(last_msg) if last_msg else None

            # Calculate unread count
            unread_count = self.repo.get_unread_count(ch.id, user_id)

            # Build member schemas
            members_schema = [ChannelMemberRead.model_validate(m) for m in ch.members]

            ch_read = ChannelRead(
                id=ch.id,
                name=ch.name,
                type=ch.type,
                description=ch.description,
                created_by=ch.created_by,
                created_at=ch.created_at,
                updated_at=ch.updated_at,
                members=members_schema,
                last_message=last_msg_schema,
                unread_count=unread_count
            )
            result.append(ch_read)
        return result

    def get_or_create_direct_chat(self, user_id: str, recipient_id: str) -> ChannelRead:
        ch = self.repo.create_direct_channel(user_id, recipient_id)
        last_msg = ch.messages[-1] if ch.messages else None
        last_msg_schema = ChatMessageRead.model_validate(last_msg) if last_msg else None
        unread_count = self.repo.get_unread_count(ch.id, user_id)
        members_schema = [ChannelMemberRead.model_validate(m) for m in ch.members]

        return ChannelRead(
            id=ch.id,
            name=ch.name,
            type=ch.type,
            description=ch.description,
            created_by=ch.created_by,
            created_at=ch.created_at,
            updated_at=ch.updated_at,
            members=members_schema,
            last_message=last_msg_schema,
            unread_count=unread_count
        )

    def create_group_channel(self, creator_id: str, name: str, description: Optional[str], member_ids: List[str]) -> ChannelRead:
        ch = self.repo.create_group_channel(name, description, creator_id, member_ids)
        last_msg = ch.messages[-1] if ch.messages else None
        last_msg_schema = ChatMessageRead.model_validate(last_msg) if last_msg else None
        members_schema = [ChannelMemberRead.model_validate(m) for m in ch.members]

        return ChannelRead(
            id=ch.id,
            name=ch.name,
            type=ch.type,
            description=ch.description,
            created_by=ch.created_by,
            created_at=ch.created_at,
            updated_at=ch.updated_at,
            members=members_schema,
            last_message=last_msg_schema,
            unread_count=0
        )

    def get_channel_messages(self, channel_id: str, user_id: str, limit: int = 100) -> List[ChatMessageRead]:
        if not self.repo.is_member(channel_id, user_id):
            raise ValueError("User is not a member of this channel")

        # Mark read when fetching messages
        self.repo.mark_read(channel_id, user_id)
        messages = self.repo.get_messages(channel_id, limit)
        return [ChatMessageRead.model_validate(m) for m in messages]

    async def send_message(self, channel_id: str, sender_id: str, content: str, message_type: str = "TEXT") -> ChatMessageRead:
        channel = self.repo.get_channel_by_id(channel_id)
        if not channel:
            raise ValueError("Channel not found")

        if not self.repo.is_member(channel_id, sender_id):
            raise ValueError("User is not a member of this channel")

        message = self.repo.create_message(channel_id, sender_id, content, message_type)
        msg_read = ChatMessageRead.model_validate(message)

        # Broadcast via WebSockets to channel members
        member_user_ids = [m.user_id for m in channel.members]
        event_payload = {
            "event": "new_message",
            "channel_id": channel_id,
            "message": msg_read.model_dump(mode="json")
        }
        await ws_manager.broadcast_to_users(event_payload, member_user_ids)

        return msg_read

    def mark_channel_read(self, channel_id: str, user_id: str) -> None:
        self.repo.mark_read(channel_id, user_id)
