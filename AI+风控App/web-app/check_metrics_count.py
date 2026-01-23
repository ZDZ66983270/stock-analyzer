
import sqlite3
import pandas as pd

conn = sqlite3.connect('backend/database.db')
query = """
SELECT 
    symbol, 
    COUNT(pe) as pe_count, 
    COUNT(dividend_yield) as dy_count, 
    COUNT(*) as total,
    (COUNT(pe) * 100.0 / COUNT(*)) as pe_pct
FROM marketdatadaily 
GROUP BY symbol
ORDER BY marketdata_daily.symbol
"""

try:
    df = pd.read_sql_query(query, conn)
    print(df.to_string(index=False))
except Exception as e:
    # Fallback if alias issue
    query = """
    SELECT 
        symbol, 
        COUNT(pe) as pe_count, 
        COUNT(dividend_yield) as dy_count, 
        COUNT(*) as total
    FROM marketdatadaily 
    GROUP BY symbol
    ORDER BY symbol
    """
    df = pd.read_sql_query(query, conn)
    print(df.to_string(index=False))

conn.close()
