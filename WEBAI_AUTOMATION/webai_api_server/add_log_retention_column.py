"""
Add missing log_retention_days column to automation_configs table
"""
from database import get_db
from sqlalchemy import text

def add_log_retention_column():
    """
    Apply a schema migration to add the `log_retention_days` column.
    
    Adds the column to the `automation_configs` table with a default value of 7,
    enabling the log cleanup policy defined in `log_crud.py`.
    """
    db = next(get_db())
    
    try:
        # Add column with default value
        sql = """
        ALTER TABLE automation_configs
        ADD log_retention_days INT NOT NULL DEFAULT 7
        """
        
        db.execute(text(sql))
        db.commit()
        
        print("✅ Successfully added log_retention_days column to automation_configs")
        print("   Default value: 7 days")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_log_retention_column()
