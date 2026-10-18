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

                # Check weekly_plans table columns
                res_wp = conn.execute(text("PRAGMA table_info(weekly_plans)")).fetchall()
                existing_wp_cols = {row[1] for row in res_wp}
                if "prerequisite_rationale" not in existing_wp_cols:
                    conn.execute(text("ALTER TABLE weekly_plans ADD COLUMN prerequisite_rationale TEXT"))

                # Check learning_requests table columns
                res_lr = conn.execute(text("PRAGMA table_info(learning_requests)")).fetchall()
                existing_lr_cols = {row[1] for row in res_lr}
                lr_cols_to_add = [
                    ("user_id", "VARCHAR(36)"),
                    ("guest_session_id", "VARCHAR(64)"),
                    ("is_benchmark", "BOOLEAN DEFAULT 0")
                ]
                for col_name, col_type in lr_cols_to_add:
                    if col_name not in existing_lr_cols:
                        conn.execute(text(f"ALTER TABLE learning_requests ADD COLUMN {col_name} {col_type}"))

                # Mark legacy unowned records as shared benchmarks to protect them from mutation
                conn.execute(text("UPDATE learning_requests SET is_benchmark = 1 WHERE user_id IS NULL AND guest_session_id IS NULL AND (is_benchmark IS NULL OR is_benchmark = 0)"))
                conn.commit()
            else:
                conn.execute(text("ALTER TABLE weekly_plans ADD COLUMN IF NOT EXISTS prerequisite_rationale TEXT"))
                conn.execute(text("ALTER TABLE learning_requests ADD COLUMN IF NOT EXISTS user_id VARCHAR(36)"))
                conn.execute(text("ALTER TABLE learning_requests ADD COLUMN IF NOT EXISTS guest_session_id VARCHAR(64)"))
                conn.execute(text("ALTER TABLE learning_requests ADD COLUMN IF NOT EXISTS is_benchmark BOOLEAN DEFAULT FALSE"))
                conn.execute(text("UPDATE learning_requests SET is_benchmark = TRUE WHERE user_id IS NULL AND guest_session_id IS NULL AND (is_benchmark IS NULL OR is_benchmark = FALSE)"))
                conn.commit()
    except Exception as e:
        # Ignore if tables do not exist yet (create_all will create them)
        pass

