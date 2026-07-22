"""
Database configuration and session management for MSSQL.

This file is the "cable" that connects the WebAI API server to Microsoft SQL
Server (see walkthrough.md → "Component 1: The Warehouse"). It does three
things:

1. Reads the `DATABASE_URL` from the `.env` file and builds a SQLAlchemy
   connection URL using the ODBC driver.
2. Creates a shared `engine` (the actual connection pool) and a `SessionLocal`
   factory that produces database sessions on demand.
3. Provides `get_db()` — a FastAPI dependency that hands a fresh session to
   each request and closes it automatically when the request ends.

It also exposes `init_db()` (create all tables) and `test_connection()`
(quick connectivity check) used by `init_db.py` and on server startup.

Connection details (from `webai_api_server/.env`):
    SERVER   = sweet\MSSQL   (a named SQL Server instance)
    DATABASE = webai_automation
    USER     = sa
    DRIVER   = ODBC Driver 17 for SQL Server
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
import os
import urllib.parse
from dotenv import load_dotenv
import urllib

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in environment variables")

# Create connection URL for SQLAlchemy using direct ODBC string
# For named instances like sweet\MSSQL, use direct connection string
connection_url = f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(DATABASE_URL)}"

# Create engine with MSSQL-specific settings
engine = create_engine(
    connection_url,
    echo=True,  # Set to False in production
    pool_pre_ping=True,  # Verify connections before using
    connect_args={
        "timeout": 30,
    }
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency for FastAPI routes
def get_db():
    """
    FastAPI dependency that yields a database session for one request.

    FastAPI calls this once per incoming HTTP request. The function opens a
    session, hands it to the route handler (via `Depends(get_db)`), and then
    closes the session in the `finally` block — even if the handler raised
    an exception. This prevents connection leaks.

    Yields:
        Session: An open SQLAlchemy session bound to the MSSQL engine.

    Example:
        @app.get("/automations")
        async def list_automations(db: Session = Depends(get_db)):
            return db.query(models.Automation).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Create every database table defined in `models.py` if it doesn't exist.

    Imports `models` for its side effect (registering the table classes on
    `Base.metadata`), then asks SQLAlchemy to run `CREATE TABLE IF NOT EXISTS`
    for each one. Safe to call repeatedly — existing tables are left alone.

    Call this once when setting up the server for the first time
    (see `init_db.py` and walkthrough.md → "First-time setup").
    """
    import models  # Import models to register them
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")


def test_connection():
    """
    Run a trivial query (`SELECT 1`) to confirm the database is reachable.

    Used on server startup (see `main.py` → `startup()`) and by
    `init_db.py` before creating tables. Prints a friendly status line.

    Note: Emojis were removed from the status print statements to prevent
    UnicodeEncodeError on Windows terminals.

    Returns:
        bool: True if the query succeeded, False if the connection failed
        (wrong password, database missing, ODBC driver not installed, etc.).
    """
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Database connection successful!")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
