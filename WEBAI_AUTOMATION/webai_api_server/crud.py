"""
CRUD (Create, Read, Update, Delete) operations for database models.

This file is the "librarian" of the WebAI API server (see walkthrough.md →
"Component 1: The Warehouse"). Every endpoint in `main.py` that needs to
read or change the database calls one of the functions here — none of them
write raw SQL. The functions are grouped by table:

    USER OPERATIONS         — create_user, get_user_by_*, ...
    AUTOMATION OPERATIONS   — create/get/update/delete_automation, templates
    CONFIG OPERATIONS       — create/get/update_automation_config (encrypts secrets)
    EXECUTION OPERATIONS    — create/update/get_execution, history listing
    SCHEDULE OPERATIONS     — create_schedule, get_user_schedules, get_due_schedules

Every function takes an open SQLAlchemy `Session` as its first argument
(injected by FastAPI via `Depends(get_db)` in `main.py`) and returns model
objects (or None / False) — never raw rows.
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

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """
    Register a brand-new user: hash the password and mint an API key.

    Called by `POST /auth/register`. The password is scrambled with bcrypt
    (via `auth.get_password_hash`) and a random API key is generated so the
    user can call the API without sending their password.

    Args:
        db (Session): Open database session.
        user (schemas.UserCreate): {username, email, password} from the
            request body (validated by Pydantic).

    Returns:
        models.User: The newly created user, with `id`, `api_key`, and
        `created_at` populated after the commit/refresh.

    Example:
        >>> create_user(db, UserCreate(username="alice", email="a@x.com",
        ...                            password="secret"))
        <User(id=2, username='alice')>
    """
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


def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """
    Look up a single user by their unique username.

    Used by `POST /auth/register` (to reject duplicate usernames) and by
    `auth.authenticate_user` (to verify login).

    Args:
        db (Session): Open database session.
        username (str): The exact username to find.

    Returns:
        Optional[models.User]: The matching user, or None if not found.
    """
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_api_key(db: Session, api_key: str) -> Optional[models.User]:
    """
    Look up a single user by their API key.

    Used by `auth.get_current_user_by_api_key` on every authenticated
    request — the key in the `X-API-Key` header is matched to a user here.

    Args:
        db (Session): Open database session.
        api_key (str): The API key from the request header.

    Returns:
        Optional[models.User]: The matching user, or None if the key is
        unknown (which the caller turns into a 401).
    """
    return db.query(models.User).filter(models.User.api_key == api_key).first()


# ===== AUTOMATION OPERATIONS =====

def create_automation(db: Session, automation: schemas.AutomationCreate, user_id: int) -> models.Automation:
    """
    Save a new recorded automation (a "recipe" of browser steps) to the DB.

    Called by `POST /automations` and `POST /migrate/import-recording`.
    The `steps_json` field holds the list of recorded actions as JSON
    (e.g. `[{"action": "click", "locators": [...]}, ...]`).

    Args:
        db (Session): Open database session.
        automation (schemas.AutomationCreate): {name, description, base_url,
            steps_json, is_template, template_category}.
        user_id (int): The owner (from the authenticated API key).

    Returns:
        models.Automation: The created automation with its new `id`.

    Example:
        >>> create_automation(db, AutomationCreate(
        ...     name="Sastra Search", steps_json=[{"action":"open",...}]),
        ...     user_id=1)
        <Automation(id=1, name='Sastra Search')>
    """
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


def get_automation(db: Session, automation_id: int, user_id: int) -> Optional[models.Automation]:
    """
    Fetch one automation by ID, but only if the caller is allowed to see it.

    Permission rule: the caller may read an automation if they OWN it OR if
    it is a public template (`is_template == True`). This is what lets users
    browse and clone shared templates while keeping private automations
    private.

    Args:
        db (Session): Open database session.
        automation_id (int): The automation to fetch.
        user_id (int): The caller's user id.

    Returns:
        Optional[models.Automation]: The automation, or None if it does not
        exist or the caller has no rights to it.
    """
    return db.query(models.Automation).filter(
        and_(
            models.Automation.id == automation_id,
            (models.Automation.user_id == user_id) | (models.Automation.is_template == True)
        )
    ).first()


def get_user_automations(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.Automation]:
    """
    List every automation owned by a user (paginated).

    Used by `GET /automations`. Templates owned by other users are NOT
    included here — those come from `get_template_automations`.

    Args:
        db (Session): Open database session.
        user_id (int): The owner.
        skip (int): Number of records to skip (for pagination). Default 0.
        limit (int): Max records to return. Default 100.

    Returns:
        List[models.Automation]: The user's automations, newest-first by id.
    """
    return db.query(models.Automation).filter(
        models.Automation.user_id == user_id
    ).offset(skip).limit(limit).all()


def get_template_automations(db: Session, category: Optional[str] = None) -> List[models.Automation]:
    """
    List public template automations that any user can browse and clone.

    Used by `GET /templates` (no authentication required). Optionally
    filtered by `template_category` (e.g. "E-commerce", "Banking").

    Args:
        db (Session): Open database session.
        category (Optional[str]): If given, only return templates in this
            category. If None, return all templates.

    Returns:
        List[models.Automation]: All matching template automations.
    """
    query = db.query(models.Automation).filter(models.Automation.is_template == True)
    if category:
        query = query.filter(models.Automation.template_category == category)
    return query.all()


def update_automation(db: Session, automation_id: int, user_id: int, updates: schemas.AutomationUpdate) -> Optional[models.Automation]:
    """
    Update fields of an automation the caller owns.

    Only the fields actually present in `updates` are changed (Pydantic's
    `exclude_unset=True`), so callers can PATCH a single field. Ownership is
    enforced via `get_automation`.

    Args:
        db (Session): Open database session.
        automation_id (int): The automation to update.
        user_id (int): The caller (must own it).
        updates (schemas.AutomationUpdate): Fields to change.

    Returns:
        Optional[models.Automation]: The updated automation, or None if it
        was not found / not owned by the caller.
    """
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


def delete_automation(db: Session, automation_id: int, user_id: int) -> bool:
    """
    Permanently delete an automation owned by the caller.

    Only the owner can delete (templates owned by others are not deletable
    here). Cascading relationships remove the automation's configs,
    executions, and schedules too (see `models.py` `cascade="all, delete-orphan"`).

    Args:
        db (Session): Open database session.
        automation_id (int): The automation to delete.
        user_id (int): The caller (must own it).

    Returns:
        bool: True if deleted, False if not found / not owned.
    """
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

def create_automation_config(db: Session, config: schemas.ConfigCreate, user_id: int) -> models.AutomationConfig:
    """
    Save a user's personal config (variables + secrets) for an automation.

    Called by `POST /configs`. The `variables` dict is stored as plain JSON
    (for non-sensitive values like wait_time). The `secrets` dict is
    encrypted with Fernet (via `credential_manager.encrypt_secrets`) before
    storage, so passwords never sit in the DB in plain text.

    Args:
        db (Session): Open database session.
        config (schemas.ConfigCreate): {automation_id, variables, secrets}.
        user_id (int): The owner of this config.

    Returns:
        models.AutomationConfig: The created config row.

    Example:
        >>> create_automation_config(db, ConfigCreate(
        ...     automation_id=1, variables={"wait_time": 5},
        ...     secrets={"irctc_password": "p@ss"}), user_id=1)
        <AutomationConfig(id=1, automation_id=1, user_id=1)>
    """
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


def get_automation_config(db: Session, automation_id: int, user_id: int) -> Optional[models.AutomationConfig]:
    """
    Fetch the caller's active config for a given automation.

    Used by `GET /execute/{id}/steps` to find the variables/secrets that must
    be substituted into the steps before playback. Only the user's own
    active config is returned.

    Args:
        db (Session): Open database session.
        automation_id (int): The automation whose config we want.
        user_id (int): The caller.

    Returns:
        Optional[models.AutomationConfig]: The active config, or None if the
        user has no config for this automation (steps are returned as-is).
    """
    return db.query(models.AutomationConfig).filter(
        and_(
            models.AutomationConfig.automation_id == automation_id,
            models.AutomationConfig.user_id == user_id,
            models.AutomationConfig.is_active == True
        )
    ).first()


def update_automation_config(db: Session, config_id: int, user_id: int, updates: schemas.ConfigUpdate) -> Optional[models.AutomationConfig]:
    """
    Update a user's config: variables, secrets, or the active flag.

    Only supplied fields are changed. If `secrets` is supplied it is
    re-encrypted (the previous encrypted blob is replaced).

    Args:
        db (Session): Open database session.
        config_id (int): The config row to update.
        user_id (int): The caller (must own the config).
        updates (schemas.ConfigUpdate): {variables?, secrets?, is_active?}.

    Returns:
        Optional[models.AutomationConfig]: The updated config, or None if it
        was not found / not owned.
    """
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

def create_execution(db: Session, automation_id: int, user_id: int) -> models.ExecutionHistory:
    """
    Start a new execution record with status "running".

    Called by `POST /execute` before the browser robot begins replaying the
    steps. The returned `id` is the execution_id that the client later uses
    when uploading logs and the final status.

    Args:
        db (Session): Open database session.
        automation_id (int): Which automation is being run.
        user_id (int): Who started it.

    Returns:
        models.ExecutionHistory: The new record (status="running",
        started_at set by the model default).

    Example:
        >>> exec = create_execution(db, automation_id=1, user_id=1)
        >>> exec.id, exec.status
        (42, 'running')
    """
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
                     steps_failed: int = 0) -> Optional[models.ExecutionHistory]:
    """
    Update the status and results of an execution.

    Called by `PUT /executions/{id}` from the playback client at the end of
    a run. When `status` becomes "success" or "failed", the `completed_at`
    timestamp is set and `duration_seconds` is computed from `started_at`.

    Args:
        db (Session): Open database session.
        execution_id (int): The execution to update.
        status (str): New status — typically "success" or "failed".
        error_message (Optional[str]): Failure reason, if any.
        extracted_data (Optional[dict]): Data scraped during the run (e.g.
            table rows), stored as JSON.
        steps_completed (int): How many steps succeeded.
        steps_failed (int): How many steps failed.

    Returns:
        Optional[models.ExecutionHistory]: The updated record, or None if the
        execution_id was not found.
    """
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


def get_execution(db: Session, execution_id: int, user_id: int) -> Optional[models.ExecutionHistory]:
    """
    Fetch one execution, scoped to the caller (so users can't read others' runs).

    Args:
        db (Session): Open database session.
        execution_id (int): The execution to fetch.
        user_id (int): The caller (must own the execution).

    Returns:
        Optional[models.ExecutionHistory]: The execution, or None if it
        doesn't exist or belongs to someone else.
    """
    return db.query(models.ExecutionHistory).filter(
        and_(
            models.ExecutionHistory.id == execution_id,
            models.ExecutionHistory.user_id == user_id
        )
    ).first()


def get_user_executions(db: Session, user_id: int, skip: int = 0, limit: int = 50) -> List[models.ExecutionHistory]:
    """
    List a user's execution history, newest first (paginated).

    Used by `GET /executions` for the audit/debugging view.

    Args:
        db (Session): Open database session.
        user_id (int): The caller.
        skip (int): Records to skip (pagination). Default 0.
        limit (int): Max records. Default 50.

    Returns:
        List[models.ExecutionHistory]: The user's runs, newest first.
    """
    return db.query(models.ExecutionHistory).filter(
        models.ExecutionHistory.user_id == user_id
    ).order_by(models.ExecutionHistory.started_at.desc()).offset(skip).limit(limit).all()


# ===== SCHEDULE OPERATIONS =====

def create_schedule(db: Session, schedule: schemas.ScheduleCreate, user_id: int) -> models.ScheduledRun:
    """
    Create a recurring schedule for an automation using a cron expression.

    Called by `POST /schedules`. Uses `croniter` to compute the next run
    time from the cron expression (e.g. "0 9 * * *" = daily at 9 AM) and
    stores it in `next_run_at`.

    Args:
        db (Session): Open database session.
        schedule (schemas.ScheduleCreate): {automation_id, cron_expression,
            is_active}.
        user_id (int): The owner.

    Returns:
        models.ScheduledRun: The created schedule, with `next_run_at` set.

    Raises:
        Exception: If `cron_expression` is not a valid cron string (caught
        in `main.create_schedule` and returned as a 400).

    Example:
        >>> create_schedule(db, ScheduleCreate(automation_id=1,
        ...     cron_expression="0 9 * * *"), user_id=1)
        <ScheduledRun(id=1, cron='0 9 * * *')>
    """
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


def get_user_schedules(db: Session, user_id: int) -> List[models.ScheduledRun]:
    """
    List all schedules owned by a user.

    Used by `GET /schedules`.

    Args:
        db (Session): Open database session.
        user_id (int): The caller.

    Returns:
        List[models.ScheduledRun]: All of the user's schedules (active and
        inactive).
    """
    return db.query(models.ScheduledRun).filter(
        models.ScheduledRun.user_id == user_id
    ).all()


def get_due_schedules(db: Session) -> List[models.ScheduledRun]:
    """
    Find all active schedules whose next run time has arrived.

    Used by an external scheduler/worker (not currently wired into the API
    server itself) to decide which automations to kick off right now.

    Args:
        db (Session): Open database session.

    Returns:
        List[models.ScheduledRun]: Every active schedule with
        `next_run_at <= now`.
    """
    now = datetime.utcnow()
    return db.query(models.ScheduledRun).filter(
        and_(
            models.ScheduledRun.is_active == True,
            models.ScheduledRun.next_run_at <= now
        )
    ).all()
