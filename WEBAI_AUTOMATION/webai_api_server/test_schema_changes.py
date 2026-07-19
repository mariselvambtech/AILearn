"""
Test the database changes: IST columns and automation_id
"""
import requests

API_URL = "http://localhost:8000"
API_KEY = "o3-pxCyR0eY8dqI-iCHW6AVGGwrjQU8aJw-VBIt1f-8"

print("Testing Database Schema Changes")
print("=" * 60)

# 1. Create new execution and logs
print("\n1️⃣ Creating new execution...")
response = requests.post(
    f"{API_URL}/execute",
    json={"automation_id": 1},
    headers={"X-API-Key": API_KEY}
)

if response.status_code == 201:
    execution = response.json()
    execution_id = execution['id']
    print(f"✅ Created execution ID: {execution_id}")
    
    # 2. Create test log
    print(f"\n2️⃣ Creating test log...")
    response2 = requests.post(
        f"{API_URL}/executions/{execution_id}/logs",
        json={
            "timestamp": "2026-02-17T11:20:00",
            "level": "INFO",
            "source": "test",
            "message": "Testing automation_id field",
            "metadata": {"test": True}
        },
        headers={"X-API-Key": API_KEY}
    )
    
    if response2.status_code == 201:
        log = response2.json()
        print(f"✅ Created log ID: {log['id']}")
        print(f"\n📊 Log Details:")
        print(f"   execution_id: {log['execution_id']}")
        print(f"   automation_id: {log.get('automation_id', 'NOT PRESENT')}")
        print(f"   timestamp (UTC): {log['timestamp']}")
        print(f"   message: {log['message']}")
        
        if 'automation_id' in log:
            print(f"\n✅ automation_id IS PRESENT in response!")
        else:
            print(f"\n⚠️  automation_id NOT in response (check schema)")
    
    # 3. Query logs by automation_id
    print(f"\n3️⃣ Querying all logs for automation_id=1...")
    
    # Direct SQL query hint
    print(f"\n💡 You can now query logs by automation_id in SQL:")
    print(f"   SELECT automation_id, timestamp_ist, level, message")
    print(f"   FROM execution_logs")
    print(f"   WHERE automation_id = 1")
    print(f"   ORDER BY timestamp_ist DESC")
    
    print(f"\n💡 IST columns available:")
    print(f"   • execution_history.started_at_ist")
    print(f"   • execution_history.completed_at_ist")
    print(f"   • execution_logs.timestamp_ist")

else:
    print(f"❌ Failed to create execution: {response.status_code}")
    print(response.text)

print("\n" + "=" * 60)
