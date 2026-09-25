import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.core.database import SessionLocal, Base, engine
from app.core.security import get_password_hash
from app.models import User, Team, TeamMember, Project, ProjectMember, Task, TaskComment, Blocker, Activity, Notification, Channel, ChannelMember, ChatMessage

def seed_database():
    print("Database seeding is disabled in production mode. Tables are initialized empty for real user data.")
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    seed_database()

