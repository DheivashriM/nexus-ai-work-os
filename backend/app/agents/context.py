from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User

class AgentContext:
    def __init__(self, user: User, db: Session, conversation_id: Optional[str] = None):
        self.user = user
        self.db = db
        self.conversation_id = conversation_id
