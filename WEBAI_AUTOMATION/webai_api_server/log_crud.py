"""
CRUD operations for execution logging.

This file handles the "diary" of the WebAI API server (see walkthrough.md →
"Component 1: The Warehouse" → ExecutionLogs drawer). Every step the browser
robot and the AI brain perform during a run produces a log entry; those
entries are saved here so users can later answer questions like "why did my
automation fail at 3 AM?".

Two ways to save logs:
- `create_log_entry`  — saves ONE log (used rarely).
- `create_log_batch`  — saves MANY logs in one DB write (the normal case;
  the client buffers logs and flushes them at the end of a run, see
  walkthrough.md → "Batch Logging").

Other helpers: query logs with filters, delete old logs (retention policy),
and compute simple stats (total / errors / warnings / info).
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime, timedelta
from typing import List, Optional
import models
from log_schemas import LogEntryCreate, LogBatchCreate


# ===== LOG OPERATIONS =====

def create_log_entry(db: Session, execution_id: int, log: LogEntryCreate) -> models.ExecutionLog:
    """
    Save a single log line for an execution.

    Used by `POST /executions/{id}/logs`. The `automation_id` is looked up
    from the execution so logs can later be filtered by automation without
    joining tables.

    Args:
        db (Session): Open database session.
        execution_id (int): Which execution this log belongs to.
        log (LogEntryCreate): {timestamp, level, source, message, metadata}.

    Returns:
        models.ExecutionLog: The saved log row (with its new `id`).

    Raises:
        ValueError: If `execution_id` does not exist (caller should turn
        this into a 404).
    """
    # Get automation_id from execution_history
    execution = db.query(models.ExecutionHistory).filter(
        models.ExecutionHistory.id == execution_id
    ).first()

    if not execution:
        raise ValueError(f"Execution {execution_id} not found")

    db_log = models.ExecutionLog(
        execution_id=execution_id,
        automation_id=execution.automation_id,  # NEW: Set automation_id
        timestamp=log.timestamp,
        level=log.level,
        source=log.source,
        message=log.message,
        log_metadata=log.metadata
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


def create_log_batch(db: Session, batch: LogBatchCreate) -> dict:
    """
    Save many log entries for an execution in a single database write.

    This is the efficient path used by `POST /logs/batch`. The browser robot
    and AI brain buffer logs during a run and flush them all at once at the
    end (see walkthrough.md → "Batch Logging"), which is ~50x fewer HTTP
    requests than sending logs one by one.

    Args:
        db (Session): Open database session.
        batch (LogBatchCreate): {execution_id, logs: [LogEntryCreate, ...]}.

    Returns:
        dict: {"inserted": <int>, "execution_id": <int>} — how many rows
        were saved.

    Raises:
        ValueError: If `batch.execution_id` does not exist.
    """
    # Get automation_id from execution_history
    execution = db.query(models.ExecutionHistory).filter(
        models.ExecutionHistory.id == batch.execution_id
    ).first()

    if not execution:
        raise ValueError(f"Execution {batch.execution_id} not found")

    db_logs = []
    for log in batch.logs:
        db_log = models.ExecutionLog(
            execution_id=batch.execution_id,
            automation_id=execution.automation_id,  # NEW: Set automation_id
            timestamp=log.timestamp,
            level=log.level,
            source=log.source,
            message=log.message,
            log_metadata=log.metadata
        )
        db_logs.append(db_log)

    db.add_all(db_logs)
    db.commit()
    return {"inserted": len(db_logs), "execution_id": batch.execution_id}


def get_execution_logs(db: Session, execution_id: int,
                       level: Optional[str] = None,
                       source: Optional[str] = None,
                       start_time: Optional[datetime] = None,
                       end_time: Optional[datetime] = None,
                       limit: int = 100) -> List[models.ExecutionLog]:
    """
    Fetch logs for an execution, with optional filters, ordered by time.

    Used by `GET /executions/{id}/logs`. All filters are optional; supply
    only the ones you care about.

    Args:
        db (Session): Open database session.
        execution_id (int): Which execution's logs to fetch.
        level (Optional[str]): Filter by level — "INFO", "WARN", "ERROR",
            or "DEBUG" (case-insensitive, uppercased internally).
        source (Optional[str]): Filter by source — "client", "server", or
            "api" (lowercased internally).
        start_time (Optional[datetime]): Only logs at/after this time.
        end_time (Optional[datetime]): Only logs at/before this time.
        limit (int): Max rows to return. Default 100.

    Returns:
        List[models.ExecutionLog]: Matching logs, oldest first.
    """
    query = db.query(models.ExecutionLog).filter(
        models.ExecutionLog.execution_id == execution_id
    )

    if level:
        query = query.filter(models.ExecutionLog.level == level.upper())

    if source:
        query = query.filter(models.ExecutionLog.source == source.lower())

    if start_time:
        query = query.filter(models.ExecutionLog.timestamp >= start_time)

    if end_time:
        query = query.filter(models.ExecutionLog.timestamp <= end_time)

    return query.order_by(models.ExecutionLog.timestamp).limit(limit).all()


def delete_old_logs(db: Session, days: int = 7) -> dict:
    """
    Delete every log older than `days` days (the retention policy).

    Used by `DELETE /logs/cleanup` (which enforces 1 <= days <= 10 in
    `main.py`). Keeps the database from growing forever.

    Args:
        db (Session): Open database session.
        days (int): Logs older than this many days are removed. Default 7.

    Returns:
        dict: {"deleted": <int>, "cutoff_date": <iso string>} — how many
        rows were removed and the cutoff timestamp that was used.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    deleted_count = db.query(models.ExecutionLog).filter(
        models.ExecutionLog.created_at < cutoff_date
    ).delete()

    db.commit()
    return {"deleted": deleted_count, "cutoff_date": cutoff_date.isoformat()}


def cleanup_logs_for_execution(db: Session, execution_id: int) -> dict:
    """
    Delete every log belonging to a single execution.

    Handy for re-running a test execution without leaving stale logs behind.
    Not currently exposed as an endpoint, but available for scripts.

    Args:
        db (Session): Open database session.
        execution_id (int): The execution whose logs should be wiped.

    Returns:
        dict: {"deleted": <int>} — how many rows were removed.
    """
    deleted_count = db.query(models.ExecutionLog).filter(
        models.ExecutionLog.execution_id == execution_id
    ).delete()

    db.commit()
    return {"deleted": deleted_count}


def get_log_stats(db: Session, execution_id: int) -> dict:
    """
    Summarise an execution's logs: how many total, errors, warnings, info.

    Used by `GET /executions/{id}/logs/stats` for a quick health overview of
    a run (e.g. "3 errors, 12 warnings, 80 info").

    Args:
        db (Session): Open database session.
        execution_id (int): Which execution to summarise.

    Returns:
        dict: {"total_logs": int, "errors": int, "warnings": int,
        "info": int}. `info` is computed as total - errors - warnings.
    """
    total = db.query(models.ExecutionLog).filter(
        models.ExecutionLog.execution_id == execution_id
    ).count()

    errors = db.query(models.ExecutionLog).filter(
        and_(
            models.ExecutionLog.execution_id == execution_id,
            models.ExecutionLog.level == "ERROR"
        )
    ).count()

    warnings = db.query(models.ExecutionLog).filter(
        and_(
            models.ExecutionLog.execution_id == execution_id,
            models.ExecutionLog.level == "WARN"
        )
    ).count()

    return {
        "total_logs": total,
        "errors": errors,
        "warnings": warnings,
        "info": total - errors - warnings
    }
