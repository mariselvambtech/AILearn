"""
Database Migration: Create hitl_learned_memory table with IST timezone computed column.
"""
from database import get_db, engine, Base
import models
from sqlalchemy import text


def migrate_hitl_memory():
    """
    Apply migration to create hitl_learned_memory table non-destructively
    and add created_at_ist computed column for SQL Server.
    """
    print("🔄 Ensuring hitl_learned_memory table exists...")
    Base.metadata.create_all(bind=engine, tables=[models.HITLMemory.__table__])

    db = next(get_db())
    try:
        # Check if created_at_ist column exists (for MSSQL)
        check_sql = """
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'hitl_learned_memory' AND COLUMN_NAME = 'created_at_ist'
        """
        res = db.execute(text(check_sql)).fetchone()
        if not res:
            try:
                alter_sql = """
                ALTER TABLE hitl_learned_memory
                ADD created_at_ist AS DATEADD(MINUTE, 330, created_at)
                """
                db.execute(text(alter_sql))
                db.commit()
                print("   ✅ Added created_at_ist computed column to hitl_learned_memory")
            except Exception as e:
                print(f"   ℹ️ Notice on computed column: {e}")
        else:
            print("   ✅ created_at_ist column already exists")
    except Exception as e:
        print(f"   ℹ️ Migration check note: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    migrate_hitl_memory()
