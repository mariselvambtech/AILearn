"""
CRUD operations for execution logging
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime, timedelta
from typing import List, Optional
import models
from log_schemas import LogEntryCreate, LogBatchCreate


# ===== LOG OPERATIONS =====

def create_log_entry(db: Session, execution_id: int, log: LogEntryCreate):
    """Create single log entry"""
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


def create_log_batch(db: Session, batch: LogBatchCreate):
    """Create multiple log entries at once (efficient)"""
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
                       limit: int = 100):
    """Get logs for an execution with optional filtering"""
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


def delete_old_logs(db: Session, days: int = 7):
    """Delete logs older than specified days (retention policy)"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    deleted_count = db.query(models.ExecutionLog).filter(
        models.ExecutionLog.created_at < cutoff_date
    ).delete()
    
    db.commit()
    return {"deleted": deleted_count, "cutoff_date": cutoff_date.isoformat()}


def cleanup_logs_for_execution(db: Session, execution_id: int):
    """Delete all logs for a specific execution"""
    deleted_count = db.query(models.ExecutionLog).filter(
        models.ExecutionLog.execution_id == execution_id
    ).delete()
    
    db.commit()
    return {"deleted": deleted_count}


def get_log_stats(db: Session, execution_id: int):
    """Get statistics about logs for an execution"""
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
