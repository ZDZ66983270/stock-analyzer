
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
        COUNT(m.id) as '行情记录数',
        MIN(date(m.timestamp)) as '开始日期',
        MAX(date(m.timestamp)) as '结束日期',
        COUNT(m.pe) as 'PE记录',
        COUNT(m.pb) as 'PB记录',
        COUNT(m.dividend_yield) as '股息率记录'
    FROM watchlist w
    LEFT JOIN marketdatadaily m ON w.symbol = m.symbol
    GROUP BY w.market, w.symbol, w.name
    ORDER BY w.market, w.symbol;
    """
    
    try:
        df = pd.read_sql_query(query, conn)
        
        # Formatting
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        pd.set_option('display.unicode.east_asian_width', True) # Align Chinese characters
        
        print("\n" + "="*120)
        print("📊 全资产数据完整性检查报告")
        print("="*120)
        print(df.to_string(index=False))
        print("="*120)
        print(f"✅ 总计资产: {len(df)} 个")
        print("="*120)
        
        # Add Detailed Analysis in Chinese
        print("\n📈 市场与资产类型数据状态摘要:")
        
        # Extract asset type from symbol (assuming format MARKET:TYPE:CODE)
        def get_asset_type(symbol):
            parts = symbol.split(':')
            if len(parts) >= 2:
                return parts[1]
            return 'UNKNOWN'

        df['类型'] = df['代码'].apply(get_asset_type)
        
        for market in ['CN', 'HK', 'US', 'WORLD']:
            market_df = df[df['市场'] == market]
            if len(market_df) == 0: continue
            
            print(f"\n{market} 市场:")
            
            # Group by Type
            for asset_type in ['STOCK', 'ETF', 'INDEX', 'CRYPTO']:
                type_df = market_df[market_df['类型'] == asset_type].copy()
                count = len(type_df)
                if count == 0: continue
                
                pe_ok = len(type_df[type_df['PE记录'] > 0])
                pb_ok = len(type_df[type_df['PB记录'] > 0])
                div_ok = len(type_df[type_df['股息率记录'] > 0])
                
                # Historical Data Stats
                avg_rows = type_df['行情记录数'].mean()
                
                # Calculate duration in years
                def calc_years(row):
                    try:
                        start = pd.to_datetime(row['开始日期'])
                        end = pd.to_datetime(row['结束日期'])
                        return (end - start).days / 365.25
                    except:
                        return 0
                
                type_df['年限'] = type_df.apply(calc_years, axis=1)
                avg_years = type_df['年限'].mean()
                min_years = type_df['年限'].min()
                max_years = type_df['年限'].max()
                
                type_name = {
                    'STOCK': '个股',
                    'ETF': 'ETF',
                    'INDEX': '指数',
                    'CRYPTO': '加密货币'
                }.get(asset_type, asset_type)
                
                print(f"  🔹 {type_name} ({count} 个):")
                print(f"    - 历史行情  : 平均 {avg_years:.1f} 年 (范围 {min_years:.1f}-{max_years:.1f} 年), 平均 {int(avg_rows)} 条")
                print(f"    - PE 覆盖率 : {pe_ok}/{count} ({pe_ok/count*100:.1f}%)")
                print(f"    - 股息率覆盖率: {div_ok}/{count} ({div_ok/count*100:.1f}%)")
                
                # Add context/validation tips based on expectations
                if market == 'CN' and asset_type == 'STOCK':
                     if pe_ok < count or div_ok < count:
                         print("    ⚠️  警告: A股个股缺失估值数据")
                elif market == 'HK' and asset_type == 'STOCK':
                     if div_ok < count:
                         print("    ⚠️  警告: 港股个股缺失股息率")
                elif market == 'US' and asset_type == 'STOCK':
                     if pe_ok < count:
                         print("    ⚠️  警告: 美股个股缺失PE数据")

        print("\n" + "="*120)
        
    except Exception as e:
        print(f"❌ 查错误: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
