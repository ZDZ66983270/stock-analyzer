import sqlite3

def migrate():
    db_path = "database.db"
    print(f"Connecting to {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check existing columns to avoid error
        cursor.execute("PRAGMA table_info(marketdataminute)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'change' not in columns:
            print("Adding 'change' column...")
            cursor.execute("ALTER TABLE marketdataminute ADD COLUMN change FLOAT")
        else:
            print("'change' column already exists.")
            
        if 'pct_change' not in columns:
            print("Adding 'pct_change' column...")
            cursor.execute("ALTER TABLE marketdataminute ADD COLUMN pct_change FLOAT")
        else:
            print("'pct_change' column already exists.")
            
        conn.commit()
        print("Migration successful.")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
