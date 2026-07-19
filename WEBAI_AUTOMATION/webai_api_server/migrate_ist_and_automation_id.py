"""
Database Migration: Add IST timezone support and automation_id to logs
"""
from database import get_db
from sqlalchemy import text

def migrate_database():
    """Apply database schema improvements"""
    db = next(get_db())
    
    try:
        print("🔄 Starting database migration...")
        print("=" * 60)
        
        # ===== PART 1: Add IST Computed Columns =====
        print("\n1️⃣ Adding IST timezone computed columns...")
        
        # execution_history - started_at_ist
        sql = """
        ALTER TABLE execution_history
        ADD started_at_ist AS DATEADD(MINUTE, 330, started_at)
        """
        db.execute(text(sql))
        print("   ✅ Added started_at_ist to execution_history")
        
        # execution_history - completed_at_ist  
        sql = """
        ALTER TABLE execution_history
        ADD completed_at_ist AS DATEADD(MINUTE, 330, completed_at)
        """
        db.execute(text(sql))
        print("   ✅ Added completed_at_ist to execution_history")
        
        # execution_logs - timestamp_ist
        sql = """
        ALTER TABLE execution_logs
        ADD timestamp_ist AS DATEADD(MINUTE, 330, timestamp)
        """
        db.execute(text(sql))
        print("   ✅ Added timestamp_ist to execution_logs")
        
        # ===== PART 2: Add automation_id to execution_logs =====
        print("\n2️⃣ Adding automation_id column to execution_logs...")
        
        # Add column (nullable first)
        sql = """
        ALTER TABLE execution_logs
        ADD automation_id INT
        """
        db.execute(text(sql))
        print("   ✅ Added automation_id column")
        
        # Populate from execution_history
        sql = """
        UPDATE l
        SET l.automation_id = e.automation_id
        FROM execution_logs l
        JOIN execution_history e ON l.execution_id = e.id
        """
        db.execute(text(sql))
        print("   ✅ Populated automation_id from execution_history")
        
        # Make NOT NULL
        sql = """
        ALTER TABLE execution_logs
        ALTER COLUMN automation_id INT NOT NULL
        """
        db.execute(text(sql))
        print("   ✅ Made automation_id NOT NULL")
        
        # Add index
        sql = """
        CREATE INDEX ix_execution_logs_automation_id 
        ON execution_logs(automation_id)
        """
        db.execute(text(sql))
        print("   ✅ Created index on automation_id")
        
        # Add foreign key
        sql = """
        ALTER TABLE execution_logs
        ADD CONSTRAINT fk_execution_logs_automation
        FOREIGN KEY (automation_id) REFERENCES automations(id)
        """
        db.execute(text(sql))
        print("   ✅ Added foreign key constraint")
        
        # Commit all changes
        db.commit()
        
        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("\n📊 Changes:")
        print("   • IST columns: started_at_ist, completed_at_ist, timestamp_ist")
        print("   • New column: execution_logs.automation_id")
        print("   • New index: ix_execution_logs_automation_id")
        print("\n💡 Usage:")
        print("   SELECT automation_id, timestamp_ist, message")
        print("   FROM execution_logs")
        print("   WHERE automation_id = 1")
        print("   ORDER BY timestamp_ist DESC")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_database()
