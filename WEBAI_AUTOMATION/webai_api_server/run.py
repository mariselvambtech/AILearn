"""
Proper server startup script
Run this instead of main.py directly

Note: Emojis were removed from the startup print statements to prevent
UnicodeEncodeError on Windows terminals (cp1252 encoding).
"""
import uvicorn

if __name__ == "__main__":
    print("="*60)
    print("Starting WebAI API Server")
    print("="*60)
    print("Server: http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    print("Health: http://localhost:8000/health")
    print("="*60)
    print()
    
    uvicorn.run(
        "main:app",  # Import path to the app
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on file changes
        log_level="info"
    )
