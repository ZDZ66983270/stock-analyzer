from sqlmodel import create_engine, text, SQLModel
import os

# Ensure we're connecting to the right DB
base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "database.db")
sqlite_url = f"sqlite:///{db_path}"

engine = create_engine(sqlite_url)

def drop_legacy_table():
    print(f"Connecting to {db_path}...")
    try:
        with engine.connect() as conn:
            # Check if table exists
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='marketdata'"))
            if result.fetchone():
                print("Table 'marketdata' found. Dropping...")
                conn.execute(text("DROP TABLE marketdata"))
                conn.commit()
                print("Table 'marketdata' successfully dropped.")
            else:
                print("Table 'marketdata' does not exist.")
    except Exception as e:
        print(f"Error dropping table: {e}")

if __name__ == "__main__":
    drop_legacy_table()
