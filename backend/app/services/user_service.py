from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.models.chat import Channel, ChannelMember
from app.schemas.user import UserCreate, UserUpdate
from app.repositories.user_repository import UserRepository
from app.core.security import get_password_hash, verify_password

class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = UserRepository(db)

    def create_user(self, user_in: UserCreate) -> User:
        existing = self.repo.get_by_email(user_in.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email '{user_in.email}' already exists."
            )

        # First user registered in an empty DB defaults to ADMIN
        user_count = self.db.query(User).count()
        role = "ADMIN" if user_count == 0 else "MEMBER"

        hashed_password = get_password_hash(user_in.password)
        db_user = User(
            name=user_in.name,
            email=user_in.email,
            password_hash=hashed_password,
            role=role,
            status=user_in.status or "ACTIVE"
        )
        created_user = self.repo.create(db_user)

        # Ensure default workspace channels exist
        self._ensure_default_channels(created_user)

        return created_user

    def _ensure_default_channels(self, user: User):
        """Ensures #general and #announcements channels exist and adds user as a member."""
        default_channel_names = [
            ("general", "Company-wide announcements & general discussions"),
            ("announcements", "Important workspace updates and announcements")
        ]

        group_channels = self.db.query(Channel).filter(Channel.type == "GROUP").all()
        if not group_channels:
            for name, desc in default_channel_names:
                ch = Channel(
                    name=name,
                    type="GROUP",
                    description=desc,
                    created_by=user.id
                )
                self.db.add(ch)
                self.db.commit()
                self.db.refresh(ch)

        # Add user to all existing GROUP channels if not already a member
        all_group_channels = self.db.query(Channel).filter(Channel.type == "GROUP").all()
        for ch in all_group_channels:
            is_member = self.db.query(ChannelMember).filter(
                ChannelMember.channel_id == ch.id,
                ChannelMember.user_id == user.id
            ).first()
            if not is_member:
                member = ChannelMember(channel_id=ch.id, user_id=user.id)
                self.db.add(member)
        self.db.commit()

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = self.repo.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{user_id}' not found."
            )
        return user

    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        return self.repo.get_all(skip=skip, limit=limit)

    def update_user(self, user_id: str, user_in: UserUpdate) -> User:
        user = self.get_user_by_id(user_id)
        if user_in.name is not None:
            user.name = user_in.name
        if user_in.email is not None:
            user.email = user_in.email
        if user_in.role is not None:
            user.role = user_in.role
        if user_in.status is not None:
            user.status = user_in.status
        if user_in.password is not None:
            user.password_hash = get_password_hash(user_in.password)
        if user_in.whatsapp_number is not None:
            user.whatsapp_number = user_in.whatsapp_number
        if user_in.whatsapp_enabled is not None:
            user.whatsapp_enabled = user_in.whatsapp_enabled
        if user_in.whatsapp_notify_blockers is not None:
            user.whatsapp_notify_blockers = user_in.whatsapp_notify_blockers
        if user_in.whatsapp_notify_daily_plan is not None:
            user.whatsapp_notify_daily_plan = user_in.whatsapp_notify_daily_plan
        if user_in.email_privacy_locked is not None:
            user.email_privacy_locked = user_in.email_privacy_locked

        return self.repo.update(user)

