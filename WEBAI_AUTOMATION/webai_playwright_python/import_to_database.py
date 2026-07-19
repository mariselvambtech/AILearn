"""
Import recorded_steps.json into the WebAI API database
"""
import json
import requests
from pathlib import Path

# Configuration
API_URL = "http://localhost:8000"
RECORDING_FILE = "recorded_steps.json"

def main():
    print("="*60)
    print("📤 WebAI Recording Importer")
    print("="*60)
    
    # Load recording
    if not Path(RECORDING_FILE).exists():
        print(f"❌ Error: {RECORDING_FILE} not found!")
        return
    
    with open(RECORDING_FILE, 'r', encoding='utf-8') as f:
        steps = json.load(f)
    
    print(f"\n✅ Loaded {len(steps)} steps from {RECORDING_FILE}")
    
    # Check if user already registered
    print("\n" + "="*60)
    print("Step 1: User Authentication")
    print("="*60)
    
    choice = input("\nDo you already have an account? (y/n): ").strip().lower()
    
    if choice != 'y':
        # Register new user
        print("\n📝 Creating new account...")
        username = input("Enter username: ").strip()
        email = input("Enter email: ").strip()
        password = input("Enter password: ").strip()
        
        try:
            response = requests.post(
                f"{API_URL}/auth/register",
                json={
                    "username": username,
                    "email": email,
                    "password": password
                }
            )
            
            if response.status_code == 201:
                print(f"✅ User '{username}' created successfully!")
            else:
                print(f"❌ Registration failed: {response.json()}")
                return
        except Exception as e:
            print(f"❌ Error connecting to API: {e}")
            print(f"   Make sure the API server is running at {API_URL}")
            return
    else:
        username = input("Enter username: ").strip()
        password = input("Enter password: ").strip()
    
    # Login
    print(f"\n🔐 Logging in as '{username}'...")
    try:
        response = requests.post(
            f"{API_URL}/auth/login",
            json={
                "username": username,
                "password": password
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            api_key = data['api_key']
            print(f"✅ Login successful!")
            print(f"📋 Your API Key: {api_key}")
            print(f"   (Save this for future API calls)")
        else:
            print(f"❌ Login failed: {response.json()}")
            return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Import recording
    print("\n" + "="*60)
    print("Step 2: Import Recording")
    print("="*60)
    
    name = input("\nEnter automation name (e.g., 'Wikipedia Search'): ").strip()
    if not name:
        name = "Imported Automation"
    
    description = input("Enter description (optional): ").strip()
    
    print(f"\n📤 Importing to database...")
    try:
        response = requests.post(
            f"{API_URL}/migrate/import-recording",
            params={
                "name": name,
                "description": description or "Imported from recorded_steps.json"
            },
            json=steps,
            headers={"X-API-Key": api_key}
        )
        
        if response.status_code == 200:
            data = response.json()
            automation_id = data['automation_id']
            print(f"\n✅ SUCCESS!")
            print(f"   Automation ID: {automation_id}")
            print(f"   Name: {name}")
            print(f"   Steps: {data['message']}")
            
            # Show next steps
            print("\n" + "="*60)
            print("🎉 What's Next?")
            print("="*60)
            print(f"\n1. View in API docs:")
            print(f"   http://localhost:8000/docs")
            print(f"\n2. Get automation with steps:")
            print(f"   GET http://localhost:8000/automations/{automation_id}")
            print(f"\n3. Add configuration (variables/secrets):")
            print(f"   POST http://localhost:8000/configs")
            print(f"\n4. Execute automation:")
            print(f"   POST http://localhost:8000/execute")
            print(f"   (automation_id: {automation_id})")
            
        else:
            print(f"❌ Import failed: {response.json()}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
