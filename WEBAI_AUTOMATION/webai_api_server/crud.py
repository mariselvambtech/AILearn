"""
CRUD (Create, Read, Update, Delete) operations for database models
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from typing import List, Optional
import models
import schemas
from auth import get_password_hash, generate_api_key
from encryption import credential_manager


# ===== USER OPERATIONS =====

def create_user(db: Session, user: schemas.UserCreate):
    """Create new user with hashed password and API key"""
    hashed_password = get_password_hash(user.password)
    api_key = generate_api_key()
    
    db_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        api_key=api_key
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_username(db: Session, username: str):
    """Get user by username"""
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_api_key(db: Session, api_key: str):
    """Get user by API key"""
    return db.query(models.User).filter(models.User.api_key == api_key).first()


# ===== AUTOMATION OPERATIONS =====

def create_automation(db: Session, automation: schemas.AutomationCreate, user_id: int):
    """Create new automation"""
    db_automation = models.Automation(
        user_id=user_id,
        name=automation.name,
        description=automation.description,
        base_url=automation.base_url,
        steps_json=automation.steps_json,
        is_template=automation.is_template,
        template_category=automation.template_category
    )
    db.add(db_automation)
    db.commit()
    db.refresh(db_automation)
    return db_automation


def get_automation(db: Session, automation_id: int, user_id: int):
    """Get automation by ID (only if user owns it or it's a template)"""
    return db.query(models.Automation).filter(
        and_(
            models.Automation.id == automation_id,
            (models.Automation.user_id == user_id) | (models.Automation.is_template == True)
        )
    ).first()


def get_user_automations(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """Get all automations owned by user"""
    return db.query(models.Automation).filter(
        models.Automation.user_id == user_id
    ).offset(skip).limit(limit).all()


def get_template_automations(db: Session, category: Optional[str] = None):
    """Get public template automations"""
    query = db.query(models.Automation).filter(models.Automation.is_template == True)
    if category:
        query = query.filter(models.Automation.template_category == category)
    return query.all()


def update_automation(db: Session, automation_id: int, user_id: int, updates: schemas.AutomationUpdate):
    """Update automation"""
    db_automation = get_automation(db, automation_id, user_id)
    if not db_automation:
        return None
    
    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_automation, field, value)
    
    db_automation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_automation)
    return db_automation


def delete_automation(db: Session, automation_id: int, user_id: int):
    """Delete automation"""
    db_automation = db.query(models.Automation).filter(
        and_(
            models.Automation.id == automation_id,
            models.Automation.user_id == user_id
        )
    ).first()
    
    if db_automation:
        db.delete(db_automation)
        db.commit()
        return True
    return False


# ===== CONFIG OPERATIONS =====

def create_automation_config(db: Session, config: schemas.ConfigCreate, user_id: int):
    """Create automation configuration with encrypted secrets"""
    encrypted_secrets = None
    if config.secrets:
        encrypted_secrets = credential_manager.encrypt_secrets(config.secrets)
    
    db_config = models.AutomationConfig(
        automation_id=config.automation_id,
        user_id=user_id,
        variables=config.variables or {},
        encrypted_secrets=encrypted_secrets
    )
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


def get_automation_config(db: Session, automation_id: int, user_id: int):
    """Get user's configuration for an automation"""
    return db.query(models.AutomationConfig).filter(
        and_(
            models.AutomationConfig.automation_id == automation_id,
            models.AutomationConfig.user_id == user_id,
            models.AutomationConfig.is_active == True
        )
    ).first()


def update_automation_config(db: Session, config_id: int, user_id: int, updates: schemas.ConfigUpdate):
    """Update automation configuration"""
    db_config = db.query(models.AutomationConfig).filter(
        and_(
            models.AutomationConfig.id == config_id,
            models.AutomationConfig.user_id == user_id
        )
    ).first()
    
    if not db_config:
        return None
    
    if updates.variables is not None:
        db_config.variables = updates.variables
    
    if updates.secrets is not None:
        db_config.encrypted_secrets = credential_manager.encrypt_secrets(updates.secrets)
    
    if updates.is_active is not None:
        db_config.is_active = updates.is_active
    
    db_config.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_config)
    return db_config


# ===== EXECUTION OPERATIONS =====

def create_execution(db: Session, automation_id: int, user_id: int):
    """Create new execution record"""
    db_execution = models.ExecutionHistory(
        automation_id=automation_id,
        user_id=user_id,
        status="running"
    )
    db.add(db_execution)
    db.commit()
    db.refresh(db_execution)
    return db_execution


def update_execution(db: Session, execution_id: int, status: str, 
                     error_message: Optional[str] = None,
                     extracted_data: Optional[dict] = None,
                     steps_completed: int = 0,
                     steps_failed: int = 0):
    """Update execution status and results"""
    db_execution = db.query(models.ExecutionHistory).filter(
        models.ExecutionHistory.id == execution_id
    ).first()
    
    if not db_execution:
        return None
    
    db_execution.status = status
    db_execution.error_message = error_message
    db_execution.extracted_data = extracted_data
    db_execution.steps_completed = steps_completed
    db_execution.steps_failed = steps_failed
    
    if status in ["success", "failed"]:
        db_execution.completed_at = datetime.utcnow()
        if db_execution.started_at:
            duration = (db_execution.completed_at - db_execution.started_at).total_seconds()
            db_execution.duration_seconds = duration
    
    db.commit()
    db.refresh(db_execution)
    return db_execution


def get_execution(db: Session, execution_id: int, user_id: int):
    """Get execution by ID"""
    return db.query(models.ExecutionHistory).filter(
        and_(
            models.ExecutionHistory.id == execution_id,
            models.ExecutionHistory.user_id == user_id
        )
    ).first()


def get_user_executions(db: Session, user_id: int, skip: int = 0, limit: int = 50):
    """Get user's execution history"""
    return db.query(models.ExecutionHistory).filter(
        models.ExecutionHistory.user_id == user_id
    ).order_by(models.ExecutionHistory.started_at.desc()).offset(skip).limit(limit).all()


# ===== SCHEDULE OPERATIONS =====

def create_schedule(db: Session, schedule: schemas.ScheduleCreate, user_id: int):
    """Create new scheduled run"""
    from croniter import croniter
    from datetime import datetime
    
    # Calculate next run time from cron expression
    base_time = datetime.utcnow()
    iter = croniter(schedule.cron_expression, base_time)
    next_run = iter.get_next(datetime)
    
    db_schedule = models.ScheduledRun(
        automation_id=schedule.automation_id,
        user_id=user_id,
        cron_expression=schedule.cron_expression,
        is_active=schedule.is_active,
        next_run_at=next_run
    )
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule


def get_user_schedules(db: Session, user_id: int):
    """Get all schedules for user"""
    return db.query(models.ScheduledRun).filter(
        models.ScheduledRun.user_id == user_id
    ).all()


def get_due_schedules(db: Session):
    """Get all active schedules that are due to run"""
    now = datetime.utcnow()
    return db.query(models.ScheduledRun).filter(
        and_(
            models.ScheduledRun.is_active == True,
            models.ScheduledRun.next_run_at <= now
        )
    ).all()
