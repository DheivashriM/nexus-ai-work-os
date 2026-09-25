from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

db_url = settings.DATABASE_URL

connect_args = {}
if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def ensure_user_email_columns():
    """Add the user-owned email columns for databases created before email setup existed."""
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("users")}
    columns = {
        "email_connection_enabled": "BOOLEAN NOT NULL DEFAULT FALSE",
        "email_address": "VARCHAR(255)",
        "email_imap_host": "VARCHAR(255)",
        "email_imap_port": "INTEGER",
        "email_smtp_host": "VARCHAR(255)",
        "email_smtp_port": "INTEGER",
        "email_password_encrypted": "TEXT",
    }
    with engine.begin() as connection:
        for name, definition in columns.items():
            if name not in existing:
                connection.execute(text(f"ALTER TABLE users ADD COLUMN {name} {definition}"))


def ensure_whatsapp_tables():
    """Create isolated WhatsApp tables for databases initialized before this integration."""
    Base.metadata.create_all(bind=engine, tables=[
        table for table in Base.metadata.sorted_tables
        if table.name in {"whatsapp_configuration", "whatsapp_accounts", "whatsapp_conversations", "whatsapp_messages"}
    ])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
