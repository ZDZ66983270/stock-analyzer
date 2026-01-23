"""检查美股的 PE/PB 数据"""
import sys
sys.path.append('backend')

from backend.database import engine
from sqlalchemy import text
from sqlmodel import Session

def check_us_stocks_valuation():
    print("=" * 80)
    print("📊 检查美股 PE/PB 数据")
    print("=" * 80)
    
    with Session(engine) as session:
        # 1. 检查 MarketSnapshot 中的美股数据
        print("\n1️⃣ MarketSnapshot 表中的美股数据:")
        print("-" * 80)
        
        result = session.exec(text("""
            SELECT symbol, price, pe, pb, dividend_yield, timestamp
            FROM marketsnapshot
            WHERE market = 'US' AND symbol LIKE 'US:STOCK:%'
            ORDER BY symbol
        """)).all()
        
        if result:
            print(f"\n找到 {len(result)} 只美股:")
            for row in result:
                symbol, price, pe, pb, div_yield, timestamp = row
                pe_str = f"{pe:.2f}" if pe else "N/A"
                pb_str = f"{pb:.2f}" if pb else "N/A"
                div_str = f"{div_yield:.2f}%" if div_yield else "N/A"
                print(f"  {symbol:20} 价格:{price:8.2f} PE:{pe_str:8} PB:{pb_str:8} 股息:{div_str:8} ({timestamp})")
        else:
            print("  ❌ 没有找到美股数据")
        
        # 2. 检查 MarketDataDaily 中最新的美股数据
        print("\n2️⃣ MarketDataDaily 表中的最新美股数据:")
        print("-" * 80)
        
        result = session.exec(text("""
            SELECT symbol, close, pe, pb, dividend_yield, timestamp
            FROM marketdatadaily
            WHERE market = 'US' AND symbol LIKE 'US:STOCK:%'
            AND timestamp >= '2026-01-08'
            ORDER BY symbol, timestamp DESC
        """)).all()
        
        if result:
            print(f"\n找到 {len(result)} 条最新记录:")
            current_symbol = None
            for row in result:
                symbol, close, pe, pb, div_yield, timestamp = row
                # 只显示每个股票的最新一条
                if symbol != current_symbol:
                    current_symbol = symbol
                    pe_str = f"{pe:.2f}" if pe else "N/A"
                    pb_str = f"{pb:.2f}" if pb else "N/A"
                    div_str = f"{div_yield:.2f}%" if div_yield else "N/A"
                    print(f"  {symbol:20} 收盘:{close:8.2f} PE:{pe_str:8} PB:{pb_str:8} 股息:{div_str:8} ({timestamp})")
        else:
            print("  ❌ 没有找到最新美股数据")
        
        # 3. 统计有 PE/PB 数据的美股数量
        print("\n3️⃣ 统计分析:")
        print("-" * 80)
        
        stats = session.exec(text("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN pe IS NOT NULL THEN 1 ELSE 0 END) as has_pe,
                SUM(CASE WHEN pb IS NOT NULL THEN 1 ELSE 0 END) as has_pb,
                SUM(CASE WHEN dividend_yield IS NOT NULL THEN 1 ELSE 0 END) as has_div
            FROM marketsnapshot
            WHERE market = 'US' AND symbol LIKE 'US:STOCK:%'
        """)).first()
        
        if stats:
            total, has_pe, has_pb, has_div = stats
            print(f"\n  总美股数: {total}")
            print(f"  有 PE 数据: {has_pe} ({has_pe/total*100 if total > 0 else 0:.0f}%)")
            print(f"  有 PB 数据: {has_pb} ({has_pb/total*100 if total > 0 else 0:.0f}%)")
            print(f"  有股息率数据: {has_div} ({has_div/total*100 if total > 0 else 0:.0f}%)")
        
        # 4. 检查 yfinance 能否获取 PE/PB
        print("\n4️⃣ 测试 yfinance 获取 PE/PB:")
        print("-" * 80)
        
        import yfinance as yf
        
        test_symbols = ['AAPL', 'MSFT', 'NVDA']
        for symbol in test_symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                pe = info.get('trailingPE') or info.get('forwardPE')
                pb = info.get('priceToBook')
                div_yield = info.get('dividendYield')
                
                print(f"\n  {symbol}:")
                print(f"    PE: {pe:.2f}" if pe else "    PE: N/A")
                print(f"    PB: {pb:.2f}" if pb else "    PB: N/A")
                print(f"    股息率: {div_yield*100:.2f}%" if div_yield else "    股息率: N/A")
            except Exception as e:
                print(f"  {symbol}: ❌ 错误 - {e}")

if __name__ == "__main__":
    check_us_stocks_valuation()
