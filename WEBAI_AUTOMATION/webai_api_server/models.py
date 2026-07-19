"""
SQLAlchemy Models for WebAI Automation System
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, JSON, Interval, FetchedValue
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    """
    User table - Stores user accounts
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
    Automation table - Stores automation blueprints (steps)
    This replaces the recorded_steps.json file
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
    Configuration for an automation run
    Allows different users to have different settings for the same automation
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
    Track automation execution history
    Used for debugging, analytics, and audit trail
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
    Detailed logs for each execution
    Stores client and server logs for debugging and analytics
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
    Scheduled automation runs
    Supports cron-based scheduling for recurring automations
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
