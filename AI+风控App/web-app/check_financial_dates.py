
import sqlite3
import pandas as pd
import os

def main():
    db_path = 'backend/database.db'
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT 
        w.market as '市场',
        w.symbol as '代码',
        w.name as '名称',
        COUNT(f.id) as '财报数量',
        MIN(f.as_of_date) as '最早财报日期',
        MAX(f.as_of_date) as '最新财报日期',
        GROUP_CONCAT(SUBSTR(f.as_of_date, 1, 4), ', ') as '年份列表'
    FROM watchlist w
    JOIN financialfundamentals f ON w.symbol = f.symbol
    GROUP BY w.market, w.symbol, w.name
    ORDER BY w.market, w.symbol;
    """
    
    try:
        df = pd.read_sql_query(query, conn)
        
        # Formatting
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        pd.set_option('display.unicode.east_asian_width', True) 
        
        print("\n" + "="*120)
        print("📊 个股财报日期检查报告")
        print("="*120)
        print(df.to_string(index=False))
        print("="*120)
        
        # Summary by market
        print("\n📈 市场财报状态摘要:")
        for market in ['CN', 'HK', 'US']:
            market_df = df[df['市场'] == market]
            if len(market_df) == 0: continue
            
            latest_dates = market_df['最新财报日期'].max()
            print(f"\n{market} 市场 ({len(market_df)} 个有财报的资产):")
            print(f"  - 最新财报日期范围: {market_df['最新财报日期'].min()} 到 {market_df['最新财报日期'].max()}")
            print(f"  - 平均财报数量: {market_df['财报数量'].mean():.1f} 份")

    except Exception as e:
        print(f"❌ 查询错误: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
