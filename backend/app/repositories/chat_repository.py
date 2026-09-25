from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func
from app.models.chat import Channel, ChannelMember, ChatMessage
from app.models.user import User

class ChatRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_channels(self, user_id: str) -> List[Channel]:
        """Fetch all channels (DIRECT and GROUP) where the user is a member."""
        from sqlalchemy import select
        member_subquery = (
            select(ChannelMember.channel_id)
            .filter(ChannelMember.user_id == user_id)
        )
        channels = (
            self.db.query(Channel)
            .filter(Channel.id.in_(member_subquery))
            .options(
                joinedload(Channel.members).joinedload(ChannelMember.user),
                joinedload(Channel.messages).joinedload(ChatMessage.sender)
            )
            .order_by(Channel.updated_at.desc())
            .all()
        )
        return channels

    def get_channel_by_id(self, channel_id: str) -> Optional[Channel]:
        return (
            self.db.query(Channel)
            .filter(Channel.id == channel_id)
            .options(
                joinedload(Channel.members).joinedload(ChannelMember.user),
                joinedload(Channel.messages).joinedload(ChatMessage.sender)
            )
            .first()
        )

    def find_direct_channel(self, user1_id: str, user2_id: str) -> Optional[Channel]:
        """Find existing 1-on-1 direct channel between two users."""
        # Find channels of type DIRECT that have user1_id
        user1_channels = (
            self.db.query(ChannelMember.channel_id)
            .join(Channel, Channel.id == ChannelMember.channel_id)
            .filter(Channel.type == "DIRECT", ChannelMember.user_id == user1_id)
            .all()
        )
        channel_ids = [c[0] for c in user1_channels]
        if not channel_ids:
            return None

        # Check which of these channels also has user2_id
        match = (
            self.db.query(ChannelMember.channel_id)
            .filter(
                ChannelMember.channel_id.in_(channel_ids),
                ChannelMember.user_id == user2_id
            )
            .first()
        )
        if match:
            return self.get_channel_by_id(match[0])
        return None

    def create_direct_channel(self, user1_id: str, user2_id: str) -> Channel:
        existing = self.find_direct_channel(user1_id, user2_id)
        if existing:
            return existing

        now = datetime.now(timezone.utc)
        channel = Channel(type="DIRECT", created_by=user1_id, created_at=now, updated_at=now)
        self.db.add(channel)
        self.db.commit()
        self.db.refresh(channel)

        m1 = ChannelMember(channel_id=channel.id, user_id=user1_id, joined_at=now, last_read_at=now)
        m2 = ChannelMember(channel_id=channel.id, user_id=user2_id, joined_at=now, last_read_at=now)
        self.db.add_all([m1, m2])
        self.db.commit()

        return self.get_channel_by_id(channel.id)

    def create_group_channel(self, name: str, description: Optional[str], creator_id: str, member_ids: List[str]) -> Channel:
        now = datetime.now(timezone.utc)
        channel = Channel(
            name=name,
            type="GROUP",
            description=description,
            created_by=creator_id,
            created_at=now,
            updated_at=now
        )
        self.db.add(channel)
        self.db.commit()
        self.db.refresh(channel)

        # Make sure creator is in member_ids
        all_members = set(member_ids)
        all_members.add(creator_id)

        members = [
            ChannelMember(channel_id=channel.id, user_id=uid, joined_at=now, last_read_at=now)
            for uid in all_members
        ]
        self.db.add_all(members)

        # System message for channel creation
        sys_msg = ChatMessage(
            channel_id=channel.id,
            sender_id=creator_id,
            content=f"Channel #{name} created.",
            message_type="SYSTEM",
            created_at=now
        )
        self.db.add(sys_msg)
        self.db.commit()

        return self.get_channel_by_id(channel.id)

    def is_member(self, channel_id: str, user_id: str) -> bool:
        member = (
            self.db.query(ChannelMember)
            .filter(ChannelMember.channel_id == channel_id, ChannelMember.user_id == user_id)
            .first()
        )
        return member is not None

    def create_message(self, channel_id: str, sender_id: str, content: str, message_type: str = "TEXT") -> ChatMessage:
        now = datetime.now(timezone.utc)
        message = ChatMessage(
            channel_id=channel_id,
            sender_id=sender_id,
            content=content,
            message_type=message_type,
            created_at=now
        )
        self.db.add(message)

        # Update channel updated_at
        channel = self.db.query(Channel).filter(Channel.id == channel_id).first()
        if channel:
            channel.updated_at = now

        # Update sender's last_read_at
        sender_member = (
            self.db.query(ChannelMember)
            .filter(ChannelMember.channel_id == channel_id, ChannelMember.user_id == sender_id)
            .first()
        )
        if sender_member:
            sender_member.last_read_at = now

        self.db.commit()
        self.db.refresh(message)

        # Ensure sender relationship is loaded
        message.sender = self.db.query(User).filter(User.id == sender_id).first()
        return message

    def get_messages(self, channel_id: str, limit: int = 100) -> List[ChatMessage]:
        return (
            self.db.query(ChatMessage)
            .filter(ChatMessage.channel_id == channel_id)
            .options(joinedload(ChatMessage.sender))
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
            .all()
        )

    def mark_read(self, channel_id: str, user_id: str) -> None:
        member = (
            self.db.query(ChannelMember)
            .filter(ChannelMember.channel_id == channel_id, ChannelMember.user_id == user_id)
            .first()
        )
        if member:
            member.last_read_at = datetime.now(timezone.utc)
            self.db.commit()

    def get_unread_count(self, channel_id: str, user_id: str) -> int:
        member = (
            self.db.query(ChannelMember)
            .filter(ChannelMember.channel_id == channel_id, ChannelMember.user_id == user_id)
            .first()
        )
        if not member or not member.last_read_at:
            return 0

        count = (
            self.db.query(func.count(ChatMessage.id))
            .filter(
                ChatMessage.channel_id == channel_id,
                ChatMessage.created_at > member.last_read_at,
                ChatMessage.sender_id != user_id
            )
            .scalar()
        )
        return count or 0
