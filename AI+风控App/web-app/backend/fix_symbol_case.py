import sqlite3

def fix_case():
    db_path = "database.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    tables = ['marketdatadaily', 'marketdataminute', 'watchlist', 'assetanalysishistory']
    
    try:
        for table in tables:
            print(f"Fixing {table}...")
            # SQLite doesn't have UPPER() function? It does.
            cursor.execute(f"UPDATE {table} SET symbol = UPPER(symbol)")
            print(f"Updated {cursor.rowcount} rows in {table}")
            
        conn.commit()
        print("Symbol case standardization complete.")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_case()
