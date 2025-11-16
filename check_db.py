"""
Quick script to check what's in the logs.db database
"""
import sqlite3
import json

db_path = "logs.db"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get table info
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("Tables in database:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Check activity_logs table
    if ('activity_logs',) in tables:
        print("\n" + "="*60)
        print("Activity Logs Table")
        print("="*60)
        
        cursor.execute("SELECT COUNT(*) FROM activity_logs")
        count = cursor.fetchone()[0]
        print(f"\nTotal records: {count}")
        
        if count > 0:
            cursor.execute("SELECT * FROM activity_logs LIMIT 10")
            rows = cursor.fetchall()
            
            # Get column names
            cursor.execute("PRAGMA table_info(activity_logs)")
            columns = [col[1] for col in cursor.fetchall()]
            
            print(f"\nColumns: {', '.join(columns)}")
            print("\nRecent entries:")
            for row in rows:
                print(f"\n  ID: {row[0]}")
                print(f"  Timestamp: {row[1]}")
                print(f"  Agent: {row[2]}")
                print(f"  Action: {row[3]}")
                print(f"  Severity: {row[4]}")
                print(f"  Message: {row[5]}")
                if row[6]:  # data column
                    print(f"  Data: {row[6][:100]}..." if len(str(row[6])) > 100 else f"  Data: {row[6]}")
    
    conn.close()
    print("\n" + "="*60)
    print("✓ Database verification complete!")
    print("="*60)
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
