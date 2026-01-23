from backend.database import engine
from sqlalchemy import text

def migrate():
    print("🚀 Migrating DB: Adding 'eps' column to 'financialfundamentals'...")
    try:
        with engine.connect() as conn:
            # Check if column exists first? 
            # SQLite doesn't support IF NOT EXISTS in ADD COLUMN directly cleanly in all versions/drivers usually?
            # Easiest way: Try adding, catch error if it exists.
            
            try:
                conn.execute(text("ALTER TABLE financialfundamentals ADD COLUMN eps FLOAT"))
                print("✅ Column 'eps' added successfully.")
            except Exception as e:
                if 'duplicate column name' in str(e).lower():
                    print("⚠️ Column 'eps' already exists.")
                else:
                    print(f"❌ Migration failed: {e}")
                    raise e
                    
            conn.commit()
            
    except Exception as e:
        print(f"❌ Engine connection error: {e}")

if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    migrate()
