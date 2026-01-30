import sys
import sqlite3
import os

# Check the default path inside container
DB_PATH = os.getenv("DB_PATH", "/app/data/dexkeeper.db")

def check_health():
    if not os.path.exists(DB_PATH):
        print(f"Healthcheck failed: Database not found at {DB_PATH}")
        sys.exit(1)
        
    try:
        # Read-only check
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, timeout=5)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM settings LIMIT 1;")
        row = cursor.fetchone()
        conn.close()
        
        if row:
            print("Healthcheck passed")
            sys.exit(0)
        else:
            print("Healthcheck failed: No data returned from settings")
            sys.exit(1)
            
    except Exception as e:
        print(f"Healthcheck failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_health()
