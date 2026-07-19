"""
Pydantic schemas for logging operations
"""
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime


# ===== LOG SCHEMAS =====

class LogEntryCreate(BaseModel):
    """Schema for creating a single log entry"""
    timestamp: datetime
    level: str  # INFO, WARN, ERROR, DEBUG
    source: str  # client, server, api
    message: str
    metadata: Optional[Dict[str, Any]] = None


class LogBatchCreate(BaseModel):
    """Schema for creating multiple log entries at once (efficient)"""
    execution_id: int
    logs: List[LogEntryCreate]


class LogEntryResponse(BaseModel):
    """Response schema for log entry"""
    id: int
    execution_id: int
    automation_id: int  # NEW: For easier filtering
    timestamp: datetime
    timestamp_ist: Optional[datetime] = None
    level: str
    source: str
    message: str
    log_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class LogQueryParams(BaseModel):
    """Query parameters for filtering logs"""
    level: Optional[str] = None  # Filter by level
    source: Optional[str] = None  # Filter by source
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = 100
