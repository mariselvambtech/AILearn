"""
Pydantic schemas for API request/response validation

Note: EmailStr was replaced with Optional[str] since email-validator is not installed.
"""
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime


# ===== USER SCHEMAS =====

class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    api_key: str


# ===== AUTOMATION SCHEMAS =====

class AutomationCreate(BaseModel):
    name: str
    description: Optional[str] = None
    base_url: Optional[str] = None
    steps_json: List[Dict[str, Any]]  # The recorded steps
    is_template: bool = False
    template_category: Optional[str] = None


class AutomationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    steps_json: Optional[List[Dict[str, Any]]] = None
    is_template: Optional[bool] = None


class AutomationResponse(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str]
    base_url: Optional[str]
    is_template: bool
    template_category: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AutomationWithSteps(AutomationResponse):
    """
    Automation with actual steps included
    """
    steps_json: List[Dict[str, Any]]


# ===== CONFIG SCHEMAS =====

class ConfigCreate(BaseModel):
    automation_id: int
    variables: Optional[Dict[str, Any]] = {}
    secrets: Optional[Dict[str, str]] = {}  # Will be encrypted server-side


class ConfigUpdate(BaseModel):
    variables: Optional[Dict[str, Any]] = None
    secrets: Optional[Dict[str, str]] = None
    is_active: Optional[bool] = None


class ConfigResponse(BaseModel):
    id: int
    automation_id: int
    user_id: int
    variables: Dict[str, Any]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ===== EXECUTION SCHEMAS =====

class ExecutionRequest(BaseModel):
    automation_id: int
    config_id: Optional[int] = None  # If None, use default config


class ExecutionResponse(BaseModel):
    id: int
    automation_id: int
    user_id: int
    started_at: datetime
    completed_at: Optional[datetime]
    status: str
    error_message: Optional[str]
    duration_seconds: Optional[float]
    steps_completed: int
    steps_failed: int
    
    class Config:
        from_attributes = True


class ExecutionWithData(ExecutionResponse):
    """
    Execution with extracted data included
    """
    extracted_data: Optional[Dict[str, Any]]


# ===== SCHEDULE SCHEMAS =====

class ScheduleCreate(BaseModel):
    automation_id: int
    cron_expression: str  # e.g., "0 9 * * *"
    is_active: bool = True


class ScheduleResponse(BaseModel):
    id: int
    automation_id: int
    user_id: int
    cron_expression: str
    is_active: bool
    next_run_at: Optional[datetime]
    last_run_at: Optional[datetime]
    last_status: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
