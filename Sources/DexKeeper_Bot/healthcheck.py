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
        # Read-only check - passes if table exists regardless of content
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, timeout=5)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM settings;")
        count = cursor.fetchone()[0]
        conn.close()
        
        # Table exists and query succeeded (count >= 0 is always True)
        print(f"Healthcheck passed (settings table has {count} entries)")
        sys.exit(0)
            
    except Exception as e:
        print(f"Healthcheck failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_health()
