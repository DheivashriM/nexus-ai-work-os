import sys
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Add parent backend directory to sys.path so app can be imported
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.models.user import User
from main import app

@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(setup_test_db):
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def seed_users(db_session):
    admin = User(
        name="Admin Test User",
        email="admin@test.com",
        password_hash=get_password_hash("password123"),
        role="ADMIN",
        status="ACTIVE"
    )
    manager = User(
        name="Manager Test User",
        email="manager@test.com",
        password_hash=get_password_hash("password123"),
        role="MANAGER",
        status="ACTIVE"
    )
    member = User(
        name="Member Test User",
        email="member@test.com",
        password_hash=get_password_hash("password123"),
        role="MEMBER",
        status="ACTIVE"
    )
    db_session.add_all([admin, manager, member])
    db_session.commit()
    for u in [admin, manager, member]:
        db_session.refresh(u)
    return {"admin": admin, "manager": manager, "member": member}
