# WebAI API Server - Quick Start Guide

## ✅ What You Now Have

A complete **FastAPI REST API server** for managing web automations with database storage!

### **Core Features**
1. ✅ **User Authentication** - Register, login, API keys
2. ✅ **Automation Storage** - Replace recorded_steps.json with database
3. ✅ **Variable Substitution** - `{{user_wait_time}}` → actual values
4. ✅ **Encrypted Credentials** - Secure password/API key storage
5. ✅ **Execution History** - Track all runs, debug failures
6. ✅ **Templates** - Share automations across users
7. ✅ **Scheduling** - Run automations on cron schedules

---

## 🚀 Start the Server

```bash
cd e:\webai_api_server
python main.py
```

**Server will start on:** `http://localhost:8000`

**API Documentation:** `http://localhost:8000/docs` (✨ Interactive Swagger UI)

---

## 📖 API Endpoints Overview

### **Authentication**
- `POST /auth/register` - Create new user
- `POST /auth/login` - Login (get API key)

### **Automations (CRUD)**
- `POST /automations` - Create automation
- `GET /automations` - List my automations
- `GET /automations/{id}` - Get specific automation
- `PUT /automations/{id}` - Update automation
- `DELETE /automations/{id}` - Delete automation

### **Templates**
- `GET /templates` - Browse public templates
- `GET /templates?category=E-commerce` - Filter by category

### **Configs (Variables & Secrets)**
- `POST /configs` - Create config for automation
- `GET /configs/automation/{id}` - Get my config
- `PUT /configs/{id}` - Update config

### **Execution**
- `POST /execute` - Run automation
- `GET /execute/{id}/steps` - Get steps with variables substituted
- `GET /executions` - View history
- `GET /executions/{id}` - Get execution results
- `PUT /executions/{id}` - Update execution status (from client)

### **Scheduling**
- `POST /schedules` - Create cron schedule
- `GET /schedules` - List my schedules

### **Migration**
- `POST /migrate/import-recording` - Import existing JSON files

---

## 🔑 How to Use the API

### Step 1: Register User

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@example.com",
    "password": "securepass123"
  }'
```

**Response:**
```json
{
  "id": 1,
  "username": "alice",
  "email": "alice@example.com",
  "created_at": "2026-02-14T10:00:00",
  "is_active": true
}
```

### Step 2: Login (Get API Key)

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "password": "securepass123"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "api_key": "ABC123XYZ456..."  ← USE THIS FOR API CALLS
}
```

**Save the `api_key`!** You'll use it in all future requests.

### Step 3: Create Automation

```bash
curl -X POST http://localhost:8000/automations \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ABC123XYZ456..." \
  -d '{
    "name": "IRCTC Login",
    "description": "Login to IRCTC website",
    "base_url": "https://www.irctc.co.in",
    "steps_json": [
      {
        "action": "navigate",
        "url": "https://www.irctc.co.in/nget/train-search"
      },
      {
        "action": "type",
        "locators": [{"id": "userId"}],
        "value": "{{irctc_username}}"
      },
      {
        "action": "type",
        "locators": [{"id": "pwd"}],
        "value": "{{irctc_password}}"
      },
      {
        "action": "click",
        "locators": [{"css": "button.search_btn"}]
      }
    ],
    "is_template": false
  }'
```

**Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "name": "IRCTC Login",
  "description": "Login to IRCTC website",
  "created_at": "2026-02-14T10:05:00",
  ...
}
```

### Step 4: Create Config (Variables + Secrets)

```bash
curl -X POST http://localhost:8000/configs \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ABC123XYZ456..." \
  -d '{
    "automation_id": 1,
    "variables": {
      "wait_time": 5,
      "retry_count": 3
    },
    "secrets": {
      "irctc_username": "myusername",
      "irctc_password": "mypassword123"
    }
  }'
```

**Result:**
- Variables stored in plain text (for wait times, counts, etc.)
- Secrets **encrypted** using Fernet before storage

### Step 5: Execute Automation

```bash
# Get steps with variables substituted
curl http://localhost:8000/execute/1/steps \
  -H "X-API-Key: ABC123XYZ456..."
```

**Response:**
```json
{
  "automation_id": 1,
  "base_url": "https://www.irctc.co.in",
  "steps": [
    {
      "action": "type",
      "value": "myusername"  ← {{irctc_username}} replaced!
    },
    {
      "action": "type",
      "value": "mypassword123"  ← {{irctc_password}} replaced!
    }
  ]
}
```

**Send these steps to your playback server!**

---

## 🔐 Variable Substitution Example

### **Recording Phase:**
User records steps and sees dialog:
```
Enter variable name for "myusername": irctc_username
Enter variable name for "5" (wait time): user_wait_time
```

**Stored in DB:**
```json
{
  "action": "type",
  "value": "{{irctc_username}}"
},
{
  "action": "wait",
  "value": "{{user_wait_time}}"
}
```

### **Playback Phase:**
User has config:
```json
{
  "variables": {"user_wait_time": 3},
  "secrets": {"irctc_username": "alice123"}
}
```

**Server returns:**
```json
{
  "action": "type",
  "value": "alice123"   ← Decrypted from secrets
},
{
  "action": "wait",
  "value": 3  ← From variables
}
```

---

## 📊 Migration from JSON Files

### Import Existing `recorded_steps.json`:

```bash
curl -X POST "http://localhost:8000/migrate/import-recording" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ABC123XYZ456..." \
  -d @recorded_steps.json
```

Or using Python:

```python
import json
import requests

# Read your existing file
with open('e:/webai_playwright_python/recorded_steps.json', 'r') as f:
    steps = json.load(f)

# Upload to API
response = requests.post(
    'http://localhost:8000/migrate/import-recording',
    json={
        "name": "Imported Automation",
        "description": "Migrated from recorded_steps.json",
        "steps": steps
    },
    headers={"X-API-Key": "your-api-key"}
)

print(f"✅ Imported as automation ID: {response.json()['automation_id']}")
```

---

## 🔄 Client Integration (Next Step)

### **Recorder Changes:**
Instead of saving to `recorded_steps.json`:
```python
# Old way
with open('recorded_steps.json', 'w') as f:
    json.dump(steps, f)

# New way
requests.post(
    'http://localhost:8000/automations',
    json={"name": "My Recording", "steps_json": steps},
    headers={"X-API-Key": api_key}
)
```

### **Playback Changes:**
Instead of reading `recorded_steps.json`:
```python
# Old way
with open('recorded_steps.json', 'r') as f:
    steps = json.load(f)

# New way
response = requests.get(
    f'http://localhost:8000/execute/{automation_id}/steps',
    headers={"X-API-Key": api_key}
)
steps = response.json()['steps']  # Already has variables substituted!
```

---

## 🧪 Test Your Server

### 1. Health Check
```bash
curl http://localhost:8000/health
```

**Expected:**
```json
{
  "status": "healthy",
  "database": "connected",
  "encryption": "configured"
}
```

### 2. Interactive API Docs
Open in browser: **http://localhost:8000/docs**

You can test all endpoints directly in the Swagger UI!

---

## 📁 Final File Structure

```
e:\webai_api_server\
├── .env                    ← DB config, encryption key
├── requirements.txt        ← Dependencies
├── database.py             ← SQLAlchemy connection
├── models.py               ← 5 database tables
├── schemas.py              ← Pydantic request/response models
├── crud.py                 ← Database operations
├── auth.py                 ← Authentication logic
├── encryption.py           ← Fernet credential encryption
├── utils.py                ← Variable substitution
├── main.py                 ← FastAPI server (run this)
├── init_db.py              ← Database initialization
├── test_connection.py      ← Connection testing
└── SETUP_GUIDE.md          ← Detailed setup instructions
```

---

## 🎯 Next Steps

### Immediate:
1. **Start the server:** `python main.py`
2. **Test with Swagger:** http://localhost:8000/docs
3. **Register a user** and get API key

### Soon:
1. Modify `recorder.py` to save to API
2. Modify playback to fetch from API
3. Add variable prompt dialog in recorder
4. Test end-to-end flow

---

## ❓ Common Questions

**Q: What if I lose my encryption key?**  
A: All encrypted credentials will be lost. Backup your `.env` file!

**Q: Can I run this on a different port?**  
A: Yes! Edit `main.py`: `uvicorn.run(app, port=9000)`

**Q: How do I deploy to production?**  
A: Use a proper WSGI server, change DB to PostgreSQL, use environment secrets manager for keys

**Q: Can I use this offline?**  
A: Yes! It's all local. Only you and your clients access the API.

---

**Ready to start!** 🎉  
Run `python main.py` and visit http://localhost:8000/docs
