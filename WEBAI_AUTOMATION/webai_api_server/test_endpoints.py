import requests

API_URL = "http://localhost:8000"
API_KEY = "o3-pxCyR0eY8dqI-iCHW6AVGGwrjQU8aJw-VBIt1f-8"

# Test simpler endpoints first
print("Testing API Endpoints...")
print("="*60)

# 1. Health check
print("\n1️⃣ Testing /health...")
try:
    r = requests.get(f"{API_URL}/health", timeout=5)
    print(f"✅ Health: {r.status_code} - {r.json()}")
except Exception as e:
    print(f"❌ Health failed: {e}")

# 2. List automations
print("\n2️⃣ Testing /automations...")
try:
    r = requests.get(
        f"{API_URL}/automations",
        headers={"X-API-Key": API_KEY},
        timeout=5
    )
    print(f"✅ Automations: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"   Found {len(data)} automations")
except Exception as e:
    print(f"❌ Automations failed: {e}")

# 3. Get specific automation
print("\n3️⃣ Testing /automations/1...")
try:
    r = requests.get(
        f"{API_URL}/automations/1",
        headers={"X-API-Key": API_KEY},
        timeout=5
    )
    print(f"✅ Get Automation: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"   Name: {data['name']}")
except Exception as e:
    print(f"❌ Get Automation failed: {e}")

# 4. Create execution record
print("\n4️⃣ Testing POST /execute...")
try:
    r = requests.post(
        f"{API_URL}/execute",
        json={"automation_id": 1},
        headers={"X-API-Key": API_KEY},
        timeout=10
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 201:
        data = r.json()
        print(f"✅ Created execution ID: {data['id']}")
        print(f"   Started at: {data['started_at']}")
    else:
        print(f"❌ Error {r.status_code}: {r.text[:300]}")
except Exception as e:
    print(f"❌ Exception: {e}")

print("\n" + "="*60)
