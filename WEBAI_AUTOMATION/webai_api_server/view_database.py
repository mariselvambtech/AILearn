import os
import sys
from pathlib import Path

# Add project directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from database import SessionLocal
from models import User, Automation, ExecutionHistory, ExecutionLog

def main():
    """
    Print a summary of the current database state to the console.
    
    Queries the users, automations, execution_history, and execution_logs tables,
    and prints a formatted overview of the data. Useful for quick debugging and 
    verification of the database contents without needing SQL Server Management Studio.
    """
    db = SessionLocal()
    try:
        print("="*60)
        print("📊 WebAI Database Overview")
        print("="*60)

        # Users
        users = db.query(User).all()
        print(f"\n👤 Users ({len(users)}):")
        for u in users:
            print(f"  - ID: {u.id} | Username: {u.username} | Email: {u.email} | API Key: {u.api_key[:10]}...")

        # Automations
        automations = db.query(Automation).all()
        print(f"\n🤖 Automations ({len(automations)}):")
        for a in automations:
            steps_preview = str(a.steps_json)[:50] + "..." if a.steps_json else "None"
            print(f"  - ID: {a.id} | User: {a.user_id} | Name: {a.name}")
            print(f"    Steps Preview: {steps_preview}")

        # Execution History
        history = db.query(ExecutionHistory).order_by(ExecutionHistory.started_at.desc()).limit(5).all()
        print(f"\n⏳ Recent Executions (Top 5):")
        for h in history:
            print(f"  - ID: {h.id} | Automation: {h.automation_id} | Status: {h.status} | Started: {h.started_at}")

        # Execution Logs
        logs = db.query(ExecutionLog).order_by(ExecutionLog.timestamp.desc()).limit(10).all()
        print(f"\n📝 Recent Logs (Top 10):")
        for log in logs:
            print(f"  - [{log.level}] {log.timestamp} | Execution ID: {log.execution_id}")
            print(f"    Message: {log.message}")
            if log.log_metadata:
                print(f"    Metadata: {log.log_metadata}")

        print("\n" + "="*60)
    finally:
        db.close()

if __name__ == "__main__":
    main()
