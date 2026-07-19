"""
Test execution record creation and logging
"""
import requests

API_URL = "http://localhost:8000"
API_KEY = "o3-pxCyR0eY8dqI-iCHW6AVGGwrjQU8aJw-VBIt1f-8"

print("Testing Execution Flow...")
print("=" * 60)

# 1. Create execution record
print("\n1️⃣ Creating execution record...")
response = requests.post(
    f"{API_URL}/execute",
    json={"automation_id": 1},
    headers={"X-API-Key": API_KEY}
)

print(f"Status: {response.status_code}")
if response.status_code == 201:
    data = response.json()
    execution_id = data['id']
    print(f"✅ Created execution ID: {execution_id}")
    print(f"   Started at: {data['started_at']}")
    
    # 2. Send test logs
    print(f"\n2️⃣ Sending logs to execution {execution_id}...")
    from datetime import datetime
    
    log_batch = {
        "execution_id": execution_id,
        "logs": [
            {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "source": "client",
                "message": "TEST: Fetching automation",
                "metadata": {"test": True}
            },
            {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "source": "client",
                "message": "TEST: Saving steps",
                "metadata": {"test": True}
            },
            {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "source": "client",
                "message": "TEST: Playback complete",
                "metadata": {"test": True}
            }
        ]
    }
    
    response2 = requests.post(
        f"{API_URL}/logs/batch",
        json=log_batch,
        headers={"X-API-Key": API_KEY}
    )
    
    print(f"Logs Status: {response2.status_code}")
    if response2.status_code == 201:
        print(f"✅ Sent {len(log_batch['logs'])} logs")
    
    # 3. Retrieve logs
    print(f"\n3️⃣ Retrieving logs for execution {execution_id}...")
    response3 = requests.get(
        f"{API_URL}/executions/{execution_id}/logs",
        headers={"X-API-Key": API_KEY}
    )
    
    if response3.status_code == 200:
        logs = response3.json()
        print(f"✅ Retrieved {len(logs)} logs:")
        for log in logs:
            print(f"   [{log['level']}] {log['message']}")
    
    print(f"\n🎯 SUCCESS! Check:")
    print(f"   • execution_history for ID {execution_id}")
    print(f"   • execution_logs for execution_id {execution_id}")
    
else:
    print(f"❌ Failed: {response.text}")
