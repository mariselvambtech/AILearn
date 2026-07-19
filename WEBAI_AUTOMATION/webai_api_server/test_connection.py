"""
Direct connection test with detailed error output
"""
import os
import urllib.parse
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print(f"Raw DATABASE_URL: {DATABASE_URL}")

# Try direct ODBC connection
connection_url = f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(DATABASE_URL)}"
print(f"\nEncoded SQLAlchemy URL: {connection_url[:100]}...")

try:
    engine = create_engine(connection_url, echo=False)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT DB_NAME(), @@VERSION"))
        row = result.fetchone()
        print(f"\n✅ SUCCESS!")
        print(f"   Database: {row[0]}")
        print(f"   Version: {row[1][:80]}...")
except Exception as e:
    print(f"\n❌ FAILED:")
    print(f"   Error type: {type(e).__name__}")
    print(f"   Error message: {str(e)}")
    
    # Try alternative format
    print("\n\nTrying alternative connection string...")
    alt_url = "mssql+pyodbc://sa:mariselvam@sweet\\MSSQL/webai_automation?driver=ODBC+Driver+17+for+SQL+Server"
    print(f"Alternative URL: {alt_url}")
    
    try:
        engine2 = create_engine(alt_url, echo=False)
        with engine2.connect() as conn:
            result = conn.execute(text("SELECT DB_NAME()"))
            print(f"✅ Alternative format works! Database: {result.scalar()}")
    except Exception as e2:
        print(f"❌ Alternative also failed: {e2}")
