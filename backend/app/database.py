from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# Prepare database URL (normalize postgres:// to postgresql:// for SQLAlchemy compatibility)
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# SQLite connection args
connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from sqlalchemy.orm import declarative_base
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema_migrations():
    """
    Ensures newly added columns exist in the database without requiring external migration tools.
    Supports SQLite and PostgreSQL gracefully.
    """
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            # Check users table columns
            if "sqlite" in str(engine.url):
                res = conn.execute(text("PRAGMA table_info(users)")).fetchall()
                existing_cols = {row[1] for row in res}
                cols_to_add = [
                    ("google_id", "TEXT"),
                    ("avatar_url", "TEXT"),
                    ("auth_provider", "TEXT DEFAULT 'email'"),
                    ("google_calendar_refresh_token", "TEXT"),
                    ("google_calendar_access_token", "TEXT"),
                    ("google_calendar_token_expiry", "TIMESTAMP"),
                    ("google_calendar_email", "TEXT"),
                    ("google_calendar_connected_at", "TIMESTAMP"),
                    ("google_calendar_scope", "TEXT"),
                ]
                for col_name, col_type in cols_to_add:
                    if col_name not in existing_cols:
                        conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                conn.commit()
    except Exception as e:
        # Ignore if tables do not exist yet (create_all will create them)
        pass

