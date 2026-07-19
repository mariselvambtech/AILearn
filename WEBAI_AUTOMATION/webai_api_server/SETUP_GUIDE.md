# WebAI API Server - Database Integration Setup Guide

## ✅ What's Been Created

### Project Structure
```
e:\webai_api_server\
├── .env                    # Environment configuration (DB connection, keys)
├── requirements.txt        # Python dependencies
├── database.py            # SQLAlchemy setup for MSSQL
├── models.py              # Database models (5 tables)
├── encryption.py          # Credential encryption (Fernet)
├── schemas.py             # Pydantic API models
├── auth.py                # Authentication & API key validation
└── [NEXT: crud.py, main.py, utils.py]
```

### Database Models Created
1. **users** - User accounts with API keys
2. **automations** - Recorded steps (replaces recorded_steps.json)
3. **automation_configs** - User-specific variables & encrypted secrets
4 **execution_history** - Track all runs (debugging, analytics)
5. **scheduled_runs** - Cron-based scheduling

---

## 🚀 Next Steps

### Step 1: Install Dependencies

```bash
cd e:\webai_api_server
pip install -r requirements.txt
```

**Required**: Install **ODBC Driver 17 for SQL Server** if not installed:
- Download: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
- Or use Chocolatey: `choco install sql-server-odbc-driver`

### Step 2: Generate Encryption Key

```bash
python encryption.py
```

This will output a secure encryption key. Copy it and update `.env`:

```
ENCRYPTION_KEY=<paste-generated-key-here>
```

### Step 3: Create Database

Open **SQL Server Management Studio** and run:

```sql
CREATE DATABASE webai_automation;
GO

USE webai_automation;
GO
```

### Step 4: Test Database Connection

```bash
python
>>> from database import test_connection
>>> test_connection()
✅ Database connection successful!
```

### Step 5: Create Tables

```bash
python
>>> from database import init_db
>>> init_db()
✅ Database tables created successfully!
```

---

## 📊 Database Schema

### Entity-Relationship Diagram

```
users (id, username, email, api_key)
  ↓ (one-to-many)
automations (id, user_id, name, steps_json, is_template)
  ↓ (one-to-many)
automation_configs (id, automation_id, user_id, variables, encrypted_secrets)
  
automations → execution_history (track runs)
automations → scheduled_runs (cron jobs)
```

### Example Data Flow

**Recording**:
```
User records steps → Client sends to API 
→ Server saves to automations table
→ Steps stored as JSON in steps_json column
```

**Running**:
```
User requests execution → Server fetches automation
→ Gets user's config (variables, secrets)
→ Substitutes {{variables}} in steps
→ Sends to playback client
→ Saves execution result to execution_history
```

---

## 🔐 Security Features

### 1. Password Hashing
- Uses **bcrypt** (industry standard)
- Passwords never stored in plain text

### 2. Encrypted Credentials
- Uses **Fernet** symmetric encryption
- Encryption key stored in `.env` (never in DB)
- Even if DB is compromised, credentials are safe

### 3. API Key Authentication
- Each user gets unique API key
- Clients send `X-API-Key` header
- No password needed for API calls

### 4. Variable Substitution
**Template Step** (in DB):
```json
{"action": "type", "value": "{{irctc_username}}"}
```

**User Config**:
```json
{"irctc_username": "alice@email.com"}
```

**Runtime Result**:
```json
{"action": "type", "value": "alice@email.com"}
```

---

## 🎯 Key Additions Explained

### 1. Encrypted Credentials
**Why**: Protect sensitive data (passwords, API keys)

**How**:
```python
# Storing
secrets = {"password": "mypass123"}
encrypted = credential_manager.encrypt_secrets(secrets)
config.encrypted_secrets = encrypted  # Save "gAAAB..." to DB

# Retrieving
decrypted = credential_manager.decrypt_secrets(config.encrypted_secrets)
password = decrypted['password']  # Now we have "mypass123"
```

### 2. Execution History
**Why**: Debugging + Analytics

**Use Cases**:
- "Why did my automation fail at 3 AM?"
- "How long does this usually take?"
- "Show me data extracted last week"

**Data Stored**:
- Start/end time, duration
- Success/failure status
- Error messages
- Extracted data (if any)

### 3. Template System
**Why**: Reusability

**Flow**:
```
User A creates "Amazon Login" automation
→ Marks as template (is_template=True)
→ User B searches templates
→ Clones it
→ Customizes with their own credentials
```

### 4. Scheduled Runs
**Why**: Recurring automations

**Example**:
```
-Cron: "0 9 * * *" (Daily at 9 AM)
- Automation: "Check train availability"
- Server runs it automatically
- Stores result in execution_history
```

### 5. Variable Substitution
**Why**: Same automation, different values

**Example**:
```
Step: {"action": "wait", "value": "{{user_wait_time}}"}

User A config: {"user_wait_time": 5}  → Waits 5 seconds
User B config: {"user_wait_time": 2}  → Waits 2 seconds
```

---

## 🔧 What's Next

I'll create the remaining files:

1. **crud.py** - Database operations (create user, save automation, etc.)
2. **main.py** - FastAPI server with all API endpoints
3. **utils.py** - Variable substitution logic
4. **init_db.py** - Database initialization script

Then I'll modify the client (recorder/playback) to use the API instead of files.

---

## 📝 Connection String Details

Your `.env` file uses:

```
DATABASE_URL=mssql+pyodbc://sa:mariselvam@sweet\\MSSQL/webai_automation?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes
```

**Breakdown**:
- `mssql+pyodbc://` - SQLAlchemy driver
- `sa:mariselvam` - Username:Password
- `sweet\\MSSQL` - Server\Instance (escaped backslash)
- `/webai_automation` - Database name
- `driver=ODBC+Driver+17+for+SQL+Server` - ODBC driver
- `TrustServerCertificate=yes` - Bypass SSL validation (local dev OK)

---

## ❓ Common Issues

### Issue: "pyodbc.InterfaceError: ('IM002', ...)"
**Solution**: Install ODBC Driver 17 for SQL Server

### Issue: "Cannot open database 'webai_automation'"
**Solution**: Run `CREATE DATABASE webai_automation;` in SSMS

### Issue: "Login failed for user 'sa'"
**Solution**: Check password in `.env` matches SQL Server

### Issue: "Encryption key error"
**Solution**: Run `python encryption.py` to generate new key

---

Ready to continue with the remaining files!
