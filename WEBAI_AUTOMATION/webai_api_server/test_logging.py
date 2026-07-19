"""
Test logging endpoints with sample data
"""
import requests
from datetime import datetime

API_URL = "http://localhost:8000"
API_KEY = "o3-pxCyR0eY8dqI-iCHW6AVGGwrjQU8aJw-VBIt1f-8"  # Your API key

# Create a sample log entry
def test_create_log():
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "level": "INFO",
        "source": "client",
        "message": "Test log entry from client",
        "metadata": {"test": True, "step_number": 1}
    }
    
    response = requests.post(
        f"{API_URL}/executions/4/logs",  # Using execution ID 4 from earlier
        json=log_data,
        headers={"X-API-Key": API_KEY}
    )
    
    print(f"Create Log: {response.status_code}")
    if response.status_code == 200 or response.status_code == 201:
        print(response.json())
    else:
        print(f"ERROR: {response.text}")


# Create batch logs
def test_batch_logs():
    batch_data = {
        "execution_id": 4,
        "logs": [
            {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "source": "server",
                "message": "Starting automation",
                "metadata": {"step_number": 1}
            },
            {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "source": "server",
                "message": "Navigating to page",
                "metadata": {"step_number": 2, "url": "https://wikipedia.org"}
            },
            {
                "timestamp": datetime.now().isoformat(),
                "level": "ERROR",
                "source": "server",
                "message": "Element not found",
                "metadata": {"step_number": 3, "locator": "button[name='submit']"}
            }
        ]
    }
    
    response = requests.post(
        f"{API_URL}/logs/batch",
        json=batch_data,
        headers={"X-API-Key": API_KEY}
    )
    
    print(f"\nBatch Logs: {response.status_code}")
    print(response.json())


# Get logs
def test_get_logs():
    response = requests.get(
        f"{API_URL}/executions/4/logs",
        headers={"X-API-Key": API_KEY}
    )
    
    print(f"\nGet Logs: {response.status_code}")
    logs = response.json()
    print(f"Total logs: {len(logs)}")
    for log in logs[:3]:  # Show first 3
        print(f"  [{log['level']}] {log['message']}")


# Get log stats
def test_log_stats():
    response = requests.get(
        f"{API_URL}/executions/4/logs/stats",
        headers={"X-API-Key": API_KEY}
    )
    
    print(f"\nLog Stats: {response.status_code}")
    print(response.json())


if __name__ == "__main__":
    print("Testing Logging Endpoints...")
    print("="*60)
    
    test_create_log()
    test_batch_logs()
    test_get_logs()
    test_log_stats()
    
    print("\n" + "="*60)
    print("✅ All tests complete!")
