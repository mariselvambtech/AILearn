"""
Server-side logging module for the WebAI local WebSocket server.

This module is responsible for batching and asynchronously transmitting 
diagnostic and execution logs from the AI server (the Brain) to the 
FastAPI backend (the Warehouse) via `POST /logs/batch`. By batching logs, 
it avoids excessive HTTP overhead during high-frequency reasoning steps.
"""
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional
import time


class ServerLogger:
    """
    Manages server-side logging with buffering and batch sending to API
    """
    
    def __init__(self, api_url: str, api_key: str, execution_id: int):
        """
        Initialize server logger
        
        Args:
            api_url: API base URL (e.g., http://localhost:8000)
            api_key: API authentication key
            execution_id: Execution record ID to link logs to
        """
        self.api_url = api_url
        self.api_key = api_key
        self.execution_id = execution_id
        self.buffer: List[Dict[str, Any]] = []
        self.enabled = True  # Can be disabled if API is unreachable
        
        # Test API connection
        try:
            response = requests.get(
                f"{api_url}/health",
                timeout=2
            )
            if response.status_code != 200:
                print(f"⚠️ API health check failed, logging disabled")
                self.enabled = False
        except Exception as e:
            print(f"⚠️ Cannot reach API at {api_url}, logging disabled: {e}")
            self.enabled = False
    
    def log(self, level: str, message: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Add log entry to buffer
        
        Args:
            level: Log level (INFO, WARN, ERROR, DEBUG)
            message: Log message
            metadata: Additional structured data (step_number, action_type, etc.)
        """
        if not self.enabled:
            return
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level.upper(),
            "source": "server",
            "message": message,
            "metadata": metadata or {}
        }
        
        self.buffer.append(log_entry)
        
        # Auto-flush if buffer gets large
        if len(self.buffer) >= 20:
            self.flush()
    
    def flush(self, silent: bool = False):
        """
        Send buffered logs to API
        
        Args:
            silent: If True, suppress error messages
        """
        if not self.enabled or not self.buffer:
            return
        
        try:
            payload = {
                "execution_id": self.execution_id,
                "logs": self.buffer
            }
            
            response = requests.post(
                f"{self.api_url}/logs/batch",
                json=payload,
                headers={"X-API-Key": self.api_key},
                timeout=5
            )
            
            if response.status_code == 201:
                if not silent:
                    print(f"📤 Sent {len(self.buffer)} server logs to database")
                self.buffer = []
            else:
                if not silent:
                    print(f"⚠️ Failed to send logs: {response.status_code}")
        
        except Exception as e:
            if not silent:
                print(f"⚠️ Error sending logs: {e}")
    
    def log_action(
        self,
        action_type: str,
        message: str,
        step_number: Optional[int] = None,
        success: bool = True,
        duration_ms: Optional[int] = None,
        **extra_metadata
    ):
        """
        Convenience method for logging actions with standardized metadata
        
        Args:
            action_type: Type of action (click, type, navigate, etc.)
            message: Log message
            step_number: Step number in plan
            success: Whether action succeeded
            duration_ms: Duration in milliseconds
            **extra_metadata: Additional metadata fields
        """
        metadata = {
            "action_type": action_type,
            "step_number": step_number,
            "success": success,
            **extra_metadata
        }
        
        if duration_ms is not None:
            metadata["duration_ms"] = duration_ms
        
        level = "INFO" if success else "ERROR"
        self.log(level, message, metadata)
    
    def __enter__(self):
        """Context manager support"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Flush logs on exit"""
        self.flush(silent=True)
        return False


# Helper function for timing actions
class ActionTimer:
    """Context manager for timing actions"""
    
    def __init__(self):
        self.start_time = None
        self.duration_ms = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            self.duration_ms = int((time.time() - self.start_time) * 1000)
        return False
