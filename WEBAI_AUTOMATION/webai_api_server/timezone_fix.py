# Timezone Fix for Database Models
# 
# PROBLEM: Database stores UTC times, but user wants IST (UTC+5:30)
# 
# SOLUTION: Update models.py to use IST timezone

from datetime import datetime, timezone, timedelta

# Define IST timezone
IST = timezone(timedelta(hours=5, minutes=30))

def get_ist_now():
    """
    Get the current time in Indian Standard Time (IST).
    
    This helper is used to consistently generate IST timestamps (UTC+5:30) 
    across the application where necessary.
    """
    return datetime.now(IST)

# Usage in models.py:
# Replace: datetime.utcnow
# With: lambda: datetime.now(timezone(timedelta(hours=5, minutes=30)))
#
# Or import pytz and use: pytz.timezone('Asia/Kolkata')

print("IST Timezone Helper Created")
print(f"Current IST time: {get_ist_now()}")
print(f"Current UTC time: {datetime.utcnow()}")
