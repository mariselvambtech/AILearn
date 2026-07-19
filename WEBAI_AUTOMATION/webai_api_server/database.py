"""
Database configuration and session management for MSSQL
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
    Database session dependency for FastAPI.
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Create all tables in the database.
    Call this when starting the server for the first time.
    """
    import models  # Import models to register them
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")


def test_connection():
    """
    Test database connection
    """
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful!")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
