"""
FastAPI Server for WebAI Automation System
Main entry point with all API routes
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import timedelta, datetime

import models
import schemas
import crud
import auth
from database import get_db, init_db, test_connection
from encryption import credential_manager
import utils
import log_schemas
import log_crud

# Create FastAPI app
app = FastAPI(
    title="WebAI Automation API",
    description="REST API for managing web automation recordings and playback",
    version="1.0.0"
)

# CORS middleware (allow frontend to call API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== STARTUP & HEALTH ENDPOINTS =====

@app.on_event("startup")
async def startup():
    """Test database connection on startup"""
    print("🚀 Starting WebAI API Server...")
    if test_connection():
        print("✅ Database connected successfully")
    else:
        print("❌ Database connection failed - check your .env file")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "WebAI Automation API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Detailed health check"""
    try:
        # Test DB connection
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "encryption": "configured" if credential_manager else "not_configured"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }


# ===== AUTHENTICATION ENDPOINTS =====

@app.post("/auth/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Register new user
    Returns user info with API key
    """
    # Check if username exists
    existing_user = crud.get_user_by_username(db, user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Create user
    db_user = crud.create_user(db, user)
    return db_user


@app.post("/auth/login", response_model=schemas.Token)
async def login(login_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    """
    Login with username/password
    Returns JWT access token and API key
    """
    user = auth.authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, 
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "api_key": user.api_key
    }


# ===== AUTOMATION ENDPOINTS =====

@app.post("/automations", response_model=schemas.AutomationResponse, status_code=status.HTTP_201_CREATED)
async def create_automation(
    automation: schemas.AutomationCreate,
    current_user: models.User = Depends(auth.get_current_user_by_api_key),
    db: Session = Depends(get_db)
):
    """
    Create new automation
    Requires API key authentication
    """
    return crud.create_automation(db, automation, current_user.id)


@app.get("/automations", response_model=List[schemas.AutomationResponse])
async def list_automations(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(auth.get_current_user_by_api_key),
    db: Session = Depends(get_db)
):
    """
    List all automations owned by current user
    """
    return crud.get_user_automations(db, current_user.id, skip, limit)


@app.get("/automations/{automation_id}", response_model=schemas.AutomationWithSteps)
async def get_automation(
    automation_id: int,
    current_user: models.User = Depends(auth.get_current_user_by_api_key),
    db: Session = Depends(get_db)
):
    """
    Get specific automation with steps
    """
    automation = crud.get_automation(db, automation_id, current_user.id)
    if not automation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Automation not found"
        )
    return automation


@app.put("/automations/{automation_id}", response_model=schemas.AutomationResponse)
async def update_automation(
    automation_id: int,
    updates: schemas.AutomationUpdate,
    current_user: models.User = Depends(auth.get_current_user_by_api_key),
    db: Session = Depends(get_db)
):
    """
    Update automation
    """
    automation = crud.update_automation(db, automation_id, current_user.id, updates)
    if not automation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Automation not found or you don't have permission"
        )
    return automation


@app.delete("/automations/{automation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_automation(
    automation_id: int,
    current_user: models.User = Depends(auth.get_current_user_by_api_key),
    db: Session = Depends(get_db)
):
    """
    Delete automation
    """
    success = crud.delete_automation(db, automation_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Automation not found"
        )
    return None


# ===== TEMPLATE ENDPOINTS =====

@app.get("/templates", response_model=List[schemas.AutomationResponse])
async def list_templates(
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List public automation templates
    No authentication required
    """
    return crud.get_template_automations(db, category)


# ===== CONFIG ENDPOINTS =====

@app.post("/configs", response_model=schemas.ConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_config(
    config: schemas.ConfigCreate,
    current_user: models.User = Depends(auth.get_current_user_by_api_key),
    db: Session = Depends(get_db)
):
    """
    Create configuration for an automation
    Secrets are automatically encrypted
    """
    return crud.create_automation_config(db, config, current_user.id)


@app.get("/configs/automation/{automation_id}", response_model=schemas.ConfigResponse)
async def get_automation_config(
    automation_id: int,
    current_user: models.User = Depends(auth.get_current_user_by_api_key),
    db: Session = Depends(get_db)
):
    """
    Get user's configuration for specific automation
    """
    config = crud.get_automation_config(db, automation_id, current_user.id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )
    return config


@app.put("/configs/{config_id}", response_model=schemas.ConfigResponse)
async def update_config(
    config_id: int,
    updates: schemas.ConfigUpdate,
    current_user: models.User = Depends(auth.get_current_user_by_api_key),
    db: Session = Depends(get_db)
):
    """
    Update configuration
    """
    config = crud.update_automation_config(db, config_id, current_user.id, updates)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )
    return config


# ===== EXECUTION ENDPOINTS =====

@app.post("/execute", response_model=schemas.ExecutionResponse, status_code=status.HTTP_201_CREATED)
async def execute_automation(
    request: schemas.ExecutionRequest,
    current_user: models.User = Depends(auth.get_current_user_by_api_key),
    db: Session = Depends(get_db)
):
    """
    Execute an automation
    This creates an execution record and returns the prepared steps
    The actual execution happens on the client side (playback server)
    """
    # Get automation
    automation = crud.get_automation(db, request.automation_id, current_user.id)
    if not automation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Automation not found"
        )
    
    # Get config
    if request.config_id:
        config = db.query(models.AutomationConfig).filter(
            models.AutomationConfig.id == request.config_id
        ).first()
    else:
        config = crud.get_automation_config(db, request.automation_id, current_user.id)
    
    # Create execution record
    execution = crud.create_execution(db, request.automation_id, current_user.id)
    
    return execution


@app.get("/execute/{automation_id}/steps")
async def get_execution_steps(
    automation_id: int,
    current_user: models.User = Depends(auth.get_current_user_by_api_key),
    db: Session = Depends(get_db)
):
    """
    Get automation steps with variables substituted
    Returns ready-to-execute steps
    """
    # Get automation
    automation = crud.get_automation(db, automation_id, current_user.id)
    if not automation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Automation not found"
        )
    
    # Get user's config (optional - may not exist)
    try:
        config = crud.get_automation_config(db, automation_id, current_user.id)
    except Exception:
        config = None
    
    if not config:
        # No config - return steps as-is
        return {
            "automation_id": automation_id,
            "steps": automation.steps_json,
            "base_url": automation.base_url
        }
    
    # Merge variables and decrypted secrets
    all_vars = config.variables.copy() if config.variables else {}
    if config.encrypted_secrets:
        try:
            secrets = credential_manager.decrypt_secrets(config.encrypted_secrets)
            all_vars.update(secrets)
        except Exception:
            pass  # If decryption fails, just use variables
    
    # Substitute variables in steps
    final_steps = utils.substitute_variables(automation.steps_json, all_vars)
    
    return {
        "automation_id": automation_id,
        "steps": final_steps,
        "base_url": automation.base_url
    }


@app.put("/executions/{execution_id}")
async def update_execution_status(
    execution_id: int,
    status: str,
    error_message: Optional[str] = None,
    extracted_data: Optional[dict] = None,
    steps_completed: int = 0,
    steps_failed: int = 0,
    current_user: models.User = Depends(auth.get_current_user_by_api_key),
    db: Session = Depends(get_db)
):
    """
    Update execution status (called by playback client)
    """
    execution = crud.update_execution(
        db, execution_id, status, error_message, 
        extracted_data, steps_completed, steps_failed
    )
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )
    
    return execution


@app.get("/executions", response_model=List[schemas.ExecutionResponse])
async def list_executions(
    skip: int = 0,
    limit: int = 50,
    current_user: models.User = Depends(auth.get_current_user_by_api_key),
    db: Session = Depends(get_db)
):
    """
    List execution history for current user
    """
    return crud.get_user_executions(db, current_user.id, skip, limit)


@app.get("/executions/{execution_id}", response_model=schemas.ExecutionWithData)
async def get_execution(
    execution_id: int,
    current_user: models.User = Depends(auth.get_current_user_by_api_key),
    db: Session = Depends(get_db)
):
    """
    Get specific execution with results
    """
    execution = crud.get_execution(db, execution_id, current_user.id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )
    return execution


# ===== SCHEDULE ENDPOINTS =====

@app.post("/schedules", response_model=schemas.ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule: schemas.ScheduleCreate,
    current_user: models.User = Depends(auth.get_current_user_by_api_key),
    db: Session = Depends(get_db)
):
    """
    Create scheduled automation run
    """
    try:
        return crud.create_schedule(db, schedule, current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid cron expression: {str(e)}"
        )


@app.get("/schedules", response_model=List[schemas.ScheduleResponse])
async def list_schedules(
    current_user: models.User = Depends(auth.get_current_user_by_api_key),
    db: Session = Depends(get_db)
):
    """
    List all schedules for current user
    """
    return crud.get_user_schedules(db, current_user.id)


# ===== LOGGING ENDPOINTS =====

@app.post("/executions/{execution_id}/logs", response_model=log_schemas.LogEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_log(
    execution_id: int,
    log: log_schemas.LogEntryCreate,
    current_user: models.User = Depends(auth.get_current_user_by_api_key),
    db: Session = Depends(get_db)
):
    """
    Create a single log entry for an execution
    """
    # Verify execution belongs to user
    execution = crud.get_execution(db, execution_id, current_user.id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )
    
    return log_crud.create_log_entry(db, execution_id, log)


@app.post("/logs/batch", status_code=status.HTTP_201_CREATED)
async def create_log_batch(
    batch: log_schemas.LogBatchCreate,
    current_user: models.User = Depends(auth.get_current_user_by_api_key),
    db: Session = Depends(get_db)
):
    """
    Create multiple log entries at once (efficient for bulk inserts)
    """
    # Verify execution belongs to user  
    execution = crud.get_execution(db, batch.execution_id, current_user.id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )
    
    return log_crud.create_log_batch(db, batch)


@app.get("/executions/{execution_id}/logs", response_model=List[log_schemas.LogEntryResponse])
async def get_execution_logs(
    execution_id: int,
    level: Optional[str] = None,
    source: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
    current_user: models.User = Depends(auth.get_current_user_by_api_key),
    db: Session = Depends(get_db)
):
    """
    Get logs for an execution with optional filtering
    - level: Filter by log level (INFO, WARN, ERROR, DEBUG)
    - source: Filter by source (client, server, api)
    - start_time/end_time: Filter by timestamp range
    - limit: Maximum number of logs to return
    """
    # Verify execution belongs to user
    execution = crud.get_execution(db, execution_id, current_user.id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )
    
    return log_crud.get_execution_logs(
        db, execution_id, level, source, start_time, end_time, limit
    )


@app.get("/executions/{execution_id}/logs/stats")
async def get_log_stats(
    execution_id: int,
    current_user: models.User = Depends(auth.get_current_user_by_api_key),
    db: Session = Depends(get_db)
):
    """
    Get statistics about logs for an execution
    Returns total logs, errors, warnings, info counts
    """
    # Verify execution belongs to user
    execution = crud.get_execution(db, execution_id, current_user.id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )
    
    return log_crud.get_log_stats(db, execution_id)


@app.delete("/logs/cleanup")
async def cleanup_old_logs(
    days: int = 7,
    current_user: models.User = Depends(auth.get_current_user_by_api_key),
    db: Session = Depends(get_db)
):
    """
    Delete logs older than specified days (retention policy)
    Default: 7 days, Max: 10 days
    Requires authentication to prevent abuse
    """
    if days < 1 or days > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Days must be between 1 and 10"
        )
    
    return log_crud.delete_old_logs(db, days)


# ===== MIGRATION ENDPOINT =====

@app.post("/migrate/import-recording")
async def import_recording(
    name: str,
    description: str,
    steps: List[dict],
    current_user: models.User = Depends(auth.get_current_user_by_api_key),
    db: Session = Depends(get_db)
):
    """
    Import existing recorded_steps.json file into database
    """
    automation = crud.create_automation(
        db,
        schemas.AutomationCreate(
            name=name,
            description=description,
            steps_json=steps,
            is_template=False
        ),
        current_user.id
    )
    
    return {
        "success": True,
        "automation_id": automation.id,
        "message": f"Imported {len(steps)} steps successfully"
    }


# Run server
if __name__ == "__main__":
    import uvicorn
    # Initialize database tables if not exists
    # init_db()  # Uncomment if you want auto-init on startup
    
    print("="*60)
    print("🚀 Starting WebAI API Server")
    print("="*60)
    print("📍 Server: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    print("📊 Health: http://localhost:8000/health")
    print("="*60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
