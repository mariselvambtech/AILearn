"""
SQLAlchemy Models for WebAI Automation System.

This file is the "blueprints" of the WebAI API server (see walkthrough.md →
"Component 1: The Warehouse"). Each class below becomes one table in the
Microsoft SQL Server database. The tables and their relationships:

    users
      └── automations            (a user owns many automations)
            ├── automation_configs    (per-user variables + encrypted secrets)
            ├── execution_history     (one row per run)
            │     └── execution_logs  (step-by-step diary of each run)
            └── scheduled_runs        (cron schedules)

Run `python init_db.py` once to create all these tables. After that,
`crud.py` reads and writes them, and `main.py` exposes them over the API.

Note on time: all timestamps are stored in UTC. IST (Indian Standard Time)
columns (`*_ist`) are SQL Server computed columns that add 330 minutes —
they're added by `migrate_ist_and_automation_id.py`, not by this file.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, JSON, Interval, FetchedValue
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    """
    User accounts — one row per registered user.

    Stores the username, a bcrypt-hashed password (never plain text), a
    unique API key used for machine-to-machine auth, and an `is_active`
    flag so an admin can disable an account without deleting it.

    Relationships: a user owns many automations, configs, executions, and
    schedules; deleting a user cascades to delete all of them.
    """
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)  # Hashed password
    api_key = Column(String(100), unique=True, index=True)  # For API authentication
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    automations = relationship("Automation", back_populates="owner", cascade="all, delete-orphan")
    configs = relationship("AutomationConfig", back_populates="user", cascade="all, delete-orphan")
    executions = relationship("ExecutionHistory", back_populates="user", cascade="all, delete-orphan")
    schedules = relationship("ScheduledRun", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class Automation(Base):
    """
    Recorded automations — the "recipe book" of the system.

    Each row is one recorded set of browser steps, stored as a JSON array
    in `steps_json` (e.g. `[{"action": "click", "locators": [...]}, ...]`).
    This table replaces the old `recorded_steps.json` file so automations
    can be shared, scheduled, and replayed by ID.

    `is_template=True` marks an automation as public — other users can
    browse and clone it via `GET /templates`.
    """
    __tablename__ = 'automations'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Metadata
    name = Column(String(200), nullable=False)
    description = Column(Text)
    base_url = Column(String(500))  # Starting URL
    
    # The recorded steps (replaces recorded_steps.json)
    # Stored as JSON array: [{"action": "click", "locators": [...], ...}, ...]
    steps_json = Column(JSON, nullable=False)
    
    # Template management
    is_template = Column(Boolean, default=False)  # Can others see/clone this?
    template_category = Column(String(50))  # E.g., "E-commerce", "Banking"
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="automations")
    configs = relationship("AutomationConfig", back_populates="automation", cascade="all, delete-orphan")
    executions = relationship("ExecutionHistory", back_populates="automation", cascade="all, delete-orphan")
    schedules = relationship("ScheduledRun", back_populates="automation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Automation(id={self.id}, name='{self.name}')>"


class AutomationConfig(Base):
    """
    Per-user settings for an automation — variables and encrypted secrets.

    Lets two users run the same automation with different values: e.g.
    Alice's `irctc_password` differs from Bob's. `variables` is plain JSON
    (for non-sensitive values like wait_time); `encrypted_secrets` is a
    Fernet-encrypted blob (see `encryption.py`) for passwords and API keys.

    `log_retention_days` controls how long this automation's logs are kept
    (default 7 days). `is_active` lets a user disable a config without
    deleting it.
    """
    __tablename__ = 'automation_configs'
    
    id = Column(Integer, primary_key=True, index=True)
    automation_id = Column(Integer, ForeignKey('automations.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Configuration variables as JSON
    # Example: {"wait_time": 5, "retry_count": 3, "timeout": 30}
    # Used for variable substitution in steps: {{wait_time}} -> 5
    variables = Column(JSON, default={})
    
    # Encrypted credentials (username, password, API keys)
    # Encrypted JSON blob: {"irctc_username": "user", "irctc_password": "pass"}
    encrypted_secrets = Column(Text)
    
    # Log retention configuration (1-10 days)
    log_retention_days = Column(Integer, default=7)  # Default 7 days
    
    # Active/inactive flag
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    automation = relationship("Automation", back_populates="configs")
    user = relationship("User", back_populates="configs")
    
    def __repr__(self):
        return f"<AutomationConfig(id={self.id}, automation_id={self.automation_id}, user_id={self.user_id})>"


class ExecutionHistory(Base):
    """
    One row per automation run — the "logbook" of the system.

    Created with status "running" when a run starts (see
    `crud.create_execution`) and updated to "success" or "failed" when it
    ends (see `crud.update_execution`, which also fills `completed_at` and
    `duration_seconds`). `extracted_data` holds any scraped data from the
    run as JSON.

    Used to answer "why did my automation fail at 3 AM?" and "how long does
    this usually take?".
    """
    __tablename__ = 'execution_history'
    
    id = Column(Integer, primary_key=True, index=True)
    automation_id = Column(Integer, ForeignKey('automations.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Execution metadata
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    started_at_ist = Column(DateTime, server_default=FetchedValue())
    completed_at = Column(DateTime)
    completed_at_ist = Column(DateTime, server_default=FetchedValue())
    status = Column(String(20), index=True)  # "running", "success", "failed"
    
    # Results and logs
    error_message = Column(Text)
    extracted_data = Column(JSON)  # If table extraction, store results here
    
    # Performance metrics
    duration_seconds = Column(Float)
    steps_completed = Column(Integer, default=0)
    steps_failed = Column(Integer, default=0)
    
    # Relationships
    automation = relationship("Automation", back_populates="executions")
    user = relationship("User", back_populates="executions")
    logs = relationship("ExecutionLog", back_populates="execution", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ExecutionHistory(id={self.id}, status='{self.status}')>"


class ExecutionLog(Base):
    """
    Step-by-step diary of a single execution — the most detailed log level.

    Each row is one event during a run: a click, a type, a navigation, an
    error, etc. `level` is INFO/WARN/ERROR/DEBUG, `source` is which
    component wrote it (client = browser robot, server = AI brain,
    api = this server). `log_metadata` holds structured extras like
    `{"step_number": 5, "locator_type": "role", "duration_ms": 234}`.

    Logs are usually saved in batches via `POST /logs/batch` (see
    `log_crud.create_log_batch`) to avoid one HTTP request per log line.
    """
    __tablename__ = 'execution_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey('execution_history.id'), nullable=False, index=True)
    automation_id = Column(Integer, ForeignKey('automations.id'), nullable=False, index=True)
    
    # Log metadata
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    timestamp_ist = Column(DateTime, server_default=FetchedValue())
    level = Column(String(10), index=True)  # INFO, WARN, ERROR, DEBUG
    source = Column(String(20), index=True)  # client, server, api
    
    # Log content
    message = Column(Text, nullable=False)
    
    # Additional structured data (step_number, locator_type, timing, etc.)
    # Example: {"step_number": 5, "locator_type": "role", "duration_ms": 234}
    log_metadata = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    execution = relationship("ExecutionHistory", back_populates="logs")
    
    def __repr__(self):
        return f"<ExecutionLog(id={self.id}, level='{self.level}', source='{self.source}')>"


class ScheduledRun(Base):
    """
    Cron-based schedules — the "alarm clock" for recurring automations.

    `cron_expression` is a standard cron string (e.g. "0 9 * * *" = daily
    at 9 AM). `next_run_at` is precomputed by `croniter` when the schedule
    is created (see `crud.create_schedule`); an external worker checks
    `get_due_schedules()` to find runs that are due and kicks them off.
    `last_run_at` / `last_status` record the most recent execution.
    """
    __tablename__ = 'scheduled_runs'
    
    id = Column(Integer, primary_key=True, index=True)
    automation_id = Column(Integer, ForeignKey('automations.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Schedule configuration
    cron_expression = Column(String(100))  # "0 9 * * *" = Daily at 9 AM
    is_active = Column(Boolean, default=True)
    
    # Execution tracking
    next_run_at = Column(DateTime, index=True)
    last_run_at = Column(DateTime)
    last_status = Column(String(20))  # Last execution status
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    automation = relationship("Automation", back_populates="schedules")
    user = relationship("User", back_populates="schedules")
    
    def __repr__(self):
        return f"<ScheduledRun(id={self.id}, cron='{self.cron_expression}')>"
