"""
Import recorded_steps.json into the WebAI API database.

This script bridges the local recording tool (Playwright CDP) with the 
centralized API Server (Warehouse). It reads a locally generated 
`recorded_steps.json` file, authenticates with the FastAPI backend, and 
creates a new database-backed automation record so that the steps can be 
scheduled, shared, and securely parameterized.

The interactive `main()` CLI is a thin wrapper around the programmatic
functions (`register_user`, `login_user`, `import_recording`) which are also
reused by the WebAI dashboard server.
"""
import json
import requests
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configuration
API_URL = "http://localhost:8000"
RECORDING_FILE = "recorded_steps.json"


def register_user(username: str, email: str, password: str, api_url: str = API_URL) -> bool:
    """
    Register a new user account via the API server.

    Args:
        username: Desired unique username.
        email: User's email address.
        password: Plain-text password (hashed server-side with bcrypt).
        api_url: Base URL of the WebAI API server.

    Returns:
        True when registration succeeds (HTTP 201), False otherwise.
    """
    try:
        response = requests.post(
            f"{api_url}/auth/register",
            json={
                "username": username,
                "email": email,
                "password": password
            }
        )

        if response.status_code == 201:
            print(f" User '{username}' created successfully!")
            return True

        print(f" Registration failed: {response.json()}")
        return False
    except requests.RequestException as e:
        print(f" Error connecting to API: {e}")
        print(f"   Make sure the API server is running at {api_url}")
        return False


def login_user(username: str, password: str, api_url: str = API_URL) -> Optional[str]:
    """
    Authenticate a user and retrieve their API key.

    Args:
        username: Registered username.
        password: User's password.
        api_url: Base URL of the WebAI API server.

    Returns:
        The user's X-API-Key string on success, None on failure.
    """
    print(f"\n Logging in as '{username}'...")
    try:
        response = requests.post(
            f"{api_url}/auth/login",
            json={
                "username": username,
                "password": password
            }
        )

        if response.status_code == 200:
            data = response.json()
            api_key = data['api_key']
            print(f" Login successful!")
            print(f" Your API Key: {api_key}")
            print(f"   (Save this for future API calls)")
            return api_key

        print(f" Login failed: {response.json()}")
        return None
    except requests.RequestException as e:
        print(f" Error: {e}")
        return None


def import_recording(steps: List[Dict[str, Any]], name: str, description: str,
                     api_key: str, api_url: str = API_URL) -> Optional[int]:
    """
    Upload recorded steps to the API database as a new automation.

    Args:
        steps: List of recorded step dictionaries (from `recorded_steps.json`).
        name: Human-friendly automation name.
        description: Optional automation description.
        api_key: User's X-API-Key for authentication.
        api_url: Base URL of the WebAI API server.

    Returns:
        The new automation's database ID on success, None on failure.
    """
    print(f"\n Importing to database...")
    try:
        response = requests.post(
            f"{api_url}/migrate/import-recording",
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
            print(f"\n SUCCESS!")
            print(f"   Automation ID: {automation_id}")
            print(f"   Name: {name}")
            print(f"   Steps: {data['message']}")
            return automation_id

        print(f" Import failed: {response.json()}")
        return None
    except requests.RequestException as e:
        print(f" Error: {e}")
        return None


def main():
    """
    Interactive CLI wrapper for importing `recorded_steps.json` into the database.

    Prompts for registration/login credentials and automation metadata, then
    delegates to `register_user()`, `login_user()`, and `import_recording()`.
    """
    print("="*60)
    print(" WebAI Recording Importer")
    print("="*60)

    # Load recording
    if not Path(RECORDING_FILE).exists():
        print(f" Error: {RECORDING_FILE} not found!")
        return

    with open(RECORDING_FILE, 'r', encoding='utf-8') as f:
        steps = json.load(f)

    print(f"\n Loaded {len(steps)} steps from {RECORDING_FILE}")

    # Check if user already registered
    print("\n" + "="*60)
    print("Step 1: User Authentication")
    print("="*60)

    choice = input("\nDo you already have an account? (y/n): ").strip().lower()

    if choice != 'y':
        # Register new user
        print("\n Creating new account...")
        username = input("Enter username: ").strip()
        email = input("Enter email: ").strip()
        password = input("Enter password: ").strip()

        if not register_user(username, email, password):
            return
    else:
        username = input("Enter username: ").strip()
        password = input("Enter password: ").strip()

    # Login
    api_key = login_user(username, password)
    if not api_key:
        return

    # Import recording
    print("\n" + "="*60)
    print("Step 2: Import Recording")
    print("="*60)

    name = input("\nEnter automation name (e.g., 'Wikipedia Search'): ").strip()
    if not name:
        name = "Imported Automation"

    description = input("Enter description (optional): ").strip()

    automation_id = import_recording(steps, name, description, api_key)

    if automation_id:
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

    print("\n" + "="*60)

if __name__ == "__main__":
    main()
