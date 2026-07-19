import requests
from datetime import datetime

# Get recent executions
r = requests.get(
    'http://localhost:8000/executions',
    headers={'X-API-Key': 'o3-pxCyR0eY8dqI-iCHW6AVGGwrjQU8aJw-VBIt1f-8'}
)

print("=" * 60)
print("EXECUTION HISTORY CHECK")
print("=" * 60)
print(f"\nCurrent time (Local): {datetime.now()}")
print(f"Current time (UTC): {datetime.utcnow()}")
print(f"\nAPI Status: {r.status_code}\n")

if r.status_code == 200:
    execs = r.json()
    print(f"Total executions: {len(execs)}\n")
    print("Recent 10 executions:")
    print("-" * 60)
    for e in execs[:10]:
        print(f"ID {e['id']:3d} | {e['started_at']} | Status: {e['status']}")
    
    # Check for today's executions
    today = datetime.now().strftime('%Y-%m-%d')
    today_execs = [e for e in execs if e['started_at'].startswith(today)]
    print(f"\n📅 Executions today ({today}): {len(today_execs)}")
    
    # Check for today's executions in UTC
    today_utc = datetime.utcnow().strftime('%Y-%m-%d')
    today_utc_execs = [e for e in execs if e['started_at'].startswith(today_utc)]
    print(f"📅 Executions today UTC ({today_utc}): {len(today_utc_execs)}")
else:
    print(f"Error: {r.text}")
