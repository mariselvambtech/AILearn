"""
Test error logging with stacktrace capture
Forces an error scenario to verify stacktrace is logged properly
"""
import sys
import os

# Add parent directory to path to import from run_from_database
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock the environment to trigger an error
def test_error_logging():
    """Test that errors are logged with full stacktraces"""
    
    # Import after path setup
    import run_from_database
    
    # Save original API_URL
    original_url = run_from_database.API_URL
    
    try:
        # Set invalid API URL to trigger error
        run_from_database.API_URL = "http://invalid-url-that-does-not-exist:9999"
        
        print("Testing error logging with invalid API URL...")
        print("="*60)
        
        # Try to fetch automation (should fail and log stacktrace)
        result = run_from_database.fetch_automation_from_api(1, run_from_database.API_KEY)
        
        print("\n" + "="*60)
        print("Error should have been logged to buffer with stacktrace")
        print(f"Log buffer contains {len(run_from_database.logs_buffer)} entries")
        
        if run_from_database.logs_buffer:
            last_log = run_from_database.logs_buffer[-1]
            print(f"\nLast log entry:")
            print(f"  Level: {last_log['level']}")
            print(f"  Message: {last_log['message']}")
            print(f"  Has stacktrace: {'stacktrace' in last_log.get('metadata', {})}")
            
            if 'stacktrace' in last_log.get('metadata', {}):
                print(f"\n✅ SUCCESS: Stacktrace captured!")
                print(f"  Stacktrace preview: {last_log['metadata']['stacktrace'][:200]}...")
            else:
                print(f"\n❌ FAIL: No stacktrace in metadata")
        
    finally:
        # Restore original URL
        run_from_database.API_URL = original_url

if __name__ == "__main__":
    test_error_logging()
