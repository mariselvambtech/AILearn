# Server Restart Instructions

## 1. Stop the API Server
In the terminal running `python run.py` (e:\webai_api_server):
- Press `Ctrl+C` to stop the server

## 2. Start the API Server
```powershell
python run.py
```

Wait for:
- ✅ Database connection successful!
- INFO: Application startup complete

## 3. Test Execution Record Creation
```powershell
python test_full_flow.py
```

Expected output:
- Status: 201
- ✅ Created execution ID: X
- ✅ Sent 3 logs
- ✅ Retrieved 3 logs

## 4. Test Client Logging
```powershell
cd ..\webai_playwright_python
python run_from_database.py
```

Enter automation ID: 1

Expected to see:
- 📊 Creating execution record...
- ✅ Execution record created (ID: X)
- 🎉 SUCCESS!
- 📤 Sent X logs to database

## 5. Verify in Database
Check:
- `execution_history` - should have new record with today's UTC time
- `execution_logs` - should have logs for that execution_id

---

**Note:** Times will be in UTC. To convert to IST, add 5:30.
