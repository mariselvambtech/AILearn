"""
Run automation from API database - Simple file-based approach.

This script demonstrates the end-to-end integration of the "Client" (this script) 
with the "Warehouse" (API Server) and the "Brain" (Local AI Server). It fetches 
a stored automation and its decrypted secrets from the API Server, saves the 
steps locally, creates an execution record, and then delegates the actual 
browser playback to `run_from_task_txt_guided.py` while tracking logs.
"""
import json
import requests
import subprocess
import traceback  # For capturing full error stacktraces
from pathlib import Path
from datetime import datetime


def log(message: str):
    """Print message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


# Logging infrastructure
logs_buffer = []  # Buffer for batch logging
current_execution_id = None  # Track current execution


def buffer_log(level: str, message: str, metadata: dict = None):
    """Add log to buffer for batch sending"""
    logs_buffer.append({
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "source": "client",
        "message": message,
        "metadata": metadata or {}
    })


def flush_logs(execution_id: int):
    """Send all buffered logs to API in batch"""
    if not logs_buffer or not execution_id:
        return
    
    try:
        response = requests.post(
            f"{API_URL}/logs/batch",
            json={
                "execution_id": execution_id,
                "logs": logs_buffer
            },
            headers={"X-API-Key": API_KEY},
            timeout=5
        )
        
        if response.status_code == 201:
            count = len(logs_buffer)
            logs_buffer.clear()
            log(f"📤 Sent {count} logs to database")
        else:
            log(f"⚠️  Failed to send logs: {response.status_code}")
    except Exception as e:
        # Don't fail execution if logging fails
        log(f"⚠️  Logging error: {e}")
    finally:
        logs_buffer.clear()  # Clear buffer even on error

# Configuration
API_URL = "http://localhost:8000"
API_KEY = "o3-pxCyR0eY8dqI-iCHW6AVGGwrjQU8aJw-VBIt1f-8"
OUTPUT_FILE = "recorded_steps.json"  # Same file playback server uses


def fetch_automation_steps(automation_id: int, api_key: str):
    """Fetch automation steps from API with variables substituted"""
    log(f"📥 Fetching automation {automation_id} from API...")
    buffer_log("INFO", f"Fetching automation {automation_id} from API", {"automation_id": automation_id})
    
    try:
        response = requests.get(
            f"{API_URL}/execute/{automation_id}/steps",
            headers={"X-API-Key": api_key}
        )
        
        if response.status_code == 200:
            data = response.json()
            steps = data['steps']
            base_url = data.get('base_url')
            
            log(f"✅ Fetched {len(steps)} steps")
            buffer_log("INFO", f"Successfully fetched {len(steps)} steps", {"step_count": len(steps), "base_url": base_url})
            
            if base_url:
                log(f"   Base URL: {base_url}")
            
            return steps, base_url
        else:
            log(f"❌ API Error: {response.status_code}")
            buffer_log("ERROR", f"API error when fetching automation", {"status_code": response.status_code})
            print(response.json())
            return None, None
    
    except Exception as e:
        log(f"❌ Error: {e}")
        buffer_log("ERROR", f"Exception while fetching automation: {str(e)}", {"error": str(e)})
        log(f"   Make sure API server is running at {API_URL}")
        return None, None


def save_steps_to_file(steps: list, filename: str = OUTPUT_FILE):
    """Save steps to JSON file"""
    log(f"💾 Saving steps to {filename}...")
    buffer_log("INFO", f"Saving {len(steps)} steps to file", {"filename": filename, "step_count": len(steps)})
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(steps, f, indent=2)
        
        log(f"✅ Saved {len(steps)} steps to {filename}")
        buffer_log("INFO", "Successfully saved steps to file", {"filename": filename})
        return True
    except Exception as e:
        log(f"❌ Error saving file: {e}")
        error_trace = traceback.format_exc()
        buffer_log("ERROR", f"Failed to save steps to file: {str(e)}", {
            "error": str(e),
            "filename": filename,
            "stacktrace": error_trace
        })
        return False


def create_execution_record(automation_id: int, api_key: str):
    """Create execution record in API"""
    log(f"📊 Creating execution record...")
    buffer_log("INFO", f"Attempting to create execution record", {"automation_id": automation_id})
    
    try:
        response = requests.post(
            f"{API_URL}/execute",
            json={"automation_id": automation_id},
            headers={"X-API-Key": api_key}
        )
        
        if response.status_code == 201:
            execution_id = response.json()['id']
            log(f"✅ Execution record created (ID: {execution_id})")
            buffer_log("INFO", f"Execution record created successfully", {"execution_id": execution_id})
            return execution_id
        else:
            log(f"⚠️  Could not create execution record: {response.status_code}")
            buffer_log("ERROR", f"Failed to create execution record", {"status_code": response.status_code, "response": response.text[:200]})
            return None
    
    except Exception as e:
        log(f"⚠️  Error creating execution record: {e}")
        error_trace = traceback.format_exc()
        buffer_log("ERROR", f"Exception creating execution record: {str(e)}", {
            "error": str(e),
            "stacktrace": error_trace
        })
        return None


def run_playback(execution_id: int = None):
    """Run the existing playback script"""
    import sys
    import os
    
    log("🚀 Starting playback...")
    buffer_log("INFO", "Starting automation playback")
    print("="*60)
    print("📺 Browser will open and execute the automation")
    print("="*60)
    print()
    
    try:
        # Create environment with execution_id and API credentials for server logging
        env = os.environ.copy()
        if execution_id:
            env['WEBAI_EXECUTION_ID'] = str(execution_id)
            env['WEBAI_API_URL'] = API_URL
            env['WEBAI_API_KEY'] = API_KEY
            log(f"📊 Passing execution ID {execution_id} to playback server")
        
        # Run the existing playback script using the same Python interpreter
        subprocess.run(
            [sys.executable, "run_from_task_txt_guided.py"],
            env=env,
            check=True
        )
        buffer_log("INFO", "Playback completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        log(f"❌ Playback failed: {e}")
        error_trace = traceback.format_exc()
        buffer_log("ERROR", f"Playback process failed: {str(e)}", {
            "error": str(e),
            "returncode": e.returncode,
            "stacktrace": error_trace
        })
        return False
    except FileNotFoundError:
        log("❌ Could not find run_from_task_txt_guided.py")
        buffer_log("ERROR", "Playback script not found", {"script": "run_from_task_txt_guided.py"})
        print("   Trying alternative method...")
        
        # Try alternative: just tell user to run it manually
        print("\n📝 Steps saved to recorded_steps.json")
        print("\n▶️  To execute, run:")
        print("   python run_from_task_txt_guided.py")
        return False


def main():
    print("="*60)
    print("🎮 WebAI Automation Runner (API → JSON → Playback)")
    print("="*60)
    
    # Get automation ID from user
    automation_id = input("\nEnter Automation ID to run (default: 1): ").strip()
    if not automation_id:
        automation_id = 1
    else:
        automation_id = int(automation_id)
    
    # Fetch from API
    steps, base_url = fetch_automation_steps(automation_id, API_KEY)
    
    if not steps:
        print("\n❌ Could not fetch automation. Exiting.")
        return
    
    # Show steps preview
    print("\n📋 Steps to execute:")
    for i, step in enumerate(steps[:5], 1):  # Show first 5
        action = step.get('action', 'unknown')
        value = step.get('value', '')
        url = step.get('url', '')
        display = f" - {value[:50]}" if value else (f" - {url[:50]}" if url else "")
        print(f"   {i}. {action}{display}")
    
    if len(steps) > 5:
        print(f"   ... and {len(steps) - 5} more steps")
    
    # Save to file (this is what the playback server reads)
    if not save_steps_to_file(steps):
        return
    
    # Create execution record in API
    execution_id = create_execution_record(automation_id, API_KEY)
    
    # Confirm execution
    print("\n" + "="*60)
    confirm = input("▶️  Execute this automation now? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Cancelled.")
        print(f"   Steps are saved in {OUTPUT_FILE}")
        print("   You can run later with: python run_from_task_txt_guided.py")
        return
    
    # Run playback
    success = run_playback(execution_id)
    
    # Final status
    if success:
        print("\n" + "="*60)
        print("🎉 SUCCESS!")
        print("="*60)
        print("\n✅ Automation executed from database!")
        
        # Send all logs to database
        if execution_id:
            flush_logs(execution_id)
    else:
        print("\n" + "="*60)
        print("📝 READY TO EXECUTE")
        print("="*60)
        print(f"\nSteps saved to {OUTPUT_FILE}")
        print("\n▶️  Run playback with:")
        print("   python run_from_task_txt_guided.py")
        
        # Send logs even on failure
        if execution_id:
            flush_logs(execution_id)
    
    print("\n💡 Tip: View execution history in API:")
    print(f"   GET {API_URL}/executions")
    
    # Show logs if we have an execution ID
    if execution_id:
        print(f"\n💡 View execution logs:")
        print(f"   GET {API_URL}/executions/{execution_id}/logs")
        print(f"   {API_URL}/docs#/default/get_execution_logs")
    
    print("\n💡 Or browse all executions:")
    print(f"   {API_URL}/docs#/default/list_executions_executions_get")


if __name__ == "__main__":
    main()
