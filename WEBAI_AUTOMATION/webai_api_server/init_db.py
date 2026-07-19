"""
Database initialization and verification script
Run this to create all tables in the database
"""
import sys
from database import test_connection, init_db, engine
from sqlalchemy import text

def main():
    """
    Execute the database initialization workflow.
    
    This workflow consists of three steps:
    1. Testing the ODBC connection to the SQL Server via `test_connection()`.
    2. Verifying that the connected database is indeed `webai_automation`.
    3. Creating all tables defined in `models.py` by calling `init_db()`.
    
    Returns:
        bool: True if initialization was fully successful, False otherwise.
    """
    print("="*60)
    print("WebAI Database Initialization")
    print("="*60)
    
    # Step 1: Test connection
    print("\n[Step 1/3] Testing database connection...")
    if not test_connection():
        print("❌ Connection failed. Check your .env DATABASE_URL")
        return False
    
    # Step 2: Verify database exists
    print("\n[Step 2/3] Verifying 'webai_automation' database exists...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT DB_NAME()"))
            db_name = result.scalar()
            print(f"✅ Connected to database: {db_name}")
            
            if db_name.lower() != 'webai_automation':
                print(f"⚠️ WARNING: Connected to '{db_name}', expected 'webai_automation'")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Step 3: Create tables
    print("\n[Step 3/3] Creating database tables...")
    try:
        init_db()
        
        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
            """))
            tables = [row[0] for row in result]
            
            print(f"\n✅ {len(tables)} tables created successfully:")
            for table in tables:
                print(f"   - {table}")
            
            expected_tables = ['users', 'automations', 'automation_configs', 'execution_history', 'scheduled_runs']
            missing = [t for t in expected_tables if t not in tables]
            if missing:
                print(f"\n⚠️ WARNING: Missing tables: {missing}")
            else:
                print("\n✅ All required tables created!")
                
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False
    
    print("\n" + "="*60)
    print("✅ Database initialization complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. I'll create the FastAPI server files (crud.py, main.py)")
    print("2. Then we'll start the API server")
    print("3. Finally, modify the client to use the API")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
