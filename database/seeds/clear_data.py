import sys
from pathlib import Path
from sqlalchemy import text

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.core.database import SessionLocal, Base, engine
from app.models import *  # Ensure models are imported for metadata reflection

def clear_database():
    print("Clearing all existing database tables and demo data...")
    try:
        with engine.begin() as conn:
            if "postgresql" in str(engine.url):
                tables = ", ".join([f'"{table.name}"' for table in Base.metadata.sorted_tables])
                conn.execute(text(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE;"))
            else:
                for table in reversed(Base.metadata.sorted_tables):
                    conn.execute(text(f'DELETE FROM "{table.name}";'))
        print("Database tables truncated successfully. Database is 100% empty and ready for real user data!")
    except Exception as e:
        print(f"Error clearing database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    clear_database()


