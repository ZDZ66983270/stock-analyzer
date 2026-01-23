"""
全量下载历史行情数据
- 所有指数（CN, HK, US）
- 自选股列表中的个股
- 尽可能长的日线数据
"""
import sys
sys.path.insert(0, 'backend')

from data_fetcher import DataFetcher, normalize_symbol_db
from database import engine
from sqlmodel import Session, select
from models import Watchlist, MarketDataDaily
from symbols_config import get_all_indices, get_symbol_info
import time
import pandas as pd
from datetime import datetime

print("🚀 开始全量下载历史行情数据...")
print("=" * 60)

fetcher = DataFetcher()

success_count = 0
fail_count = 0
total_records = 0
failed_symbols = []

def save_dataframe_to_db(df: pd.DataFrame, symbol: str, market: str) -> int:
    """
    将DataFrame保存到MarketDataDaily表
    返回保存的记录数
    """
    if df is None or df.empty:
        return 0
    
    count = 0
    db_symbol = normalize_symbol_db(symbol, market)
    
    with Session(engine) as session:
        for _, row in df.iterrows():
            try:
                # 创建记录
                record = MarketDataDaily(
                    symbol=db_symbol,
                    market=market,
                    date=str(row.get('时间', row.get('date', ''))),
                    open=float(row.get('开盘', row.get('open', 0))),
                    high=float(row.get('最高', row.get('high', 0))),
                    low=float(row.get('最低', row.get('low', 0))),
                    close=float(row.get('收盘', row.get('close', 0))),
                    volume=int(row.get('成交量', row.get('volume', 0))),
                    turnover=float(row.get('成交额', row.get('turnover', 0))) if row.get('成交额') or row.get('turnover') else 0,
                    change=float(row.get('涨跌额', 0)) if row.get('涨跌额') else 0,
                    pct_change=float(row.get('涨跌幅', 0)) if row.get('涨跌幅') else 0,
                    updated_at=datetime.now()
                )
                
                session.add(record)
                count += 1
                
            except Exception as e:
                print(f"      ⚠️  跳过一条记录: {e}")
                continue
        
        session.commit()
    
    return count

# ============================================
# 1. 下载所有指数的历史数据
# ============================================
print("\n📊 第一步：下载指数历史数据")
print("-" * 60)

indices = get_all_indices()
print(f"共 {len(indices)} 个指数需要下载\n")

for idx, symbol in enumerate(indices, 1):
    try:
        info = get_symbol_info(symbol)
        name = info.get("name", symbol)
        market = info.get("market", "US")
        
        print(f"[{idx}/{len(indices)}] {name} ({symbol}, {market})...")
        
        # 获取数据
        df = None
        if market == 'CN':
            df = fetcher.fetch_cn_daily_data(symbol)
        elif market == 'HK':
            df = fetcher.fetch_hk_daily_data(symbol)
        elif market == 'US':
            df = fetcher.fetch_us_daily_data(symbol)
        
        if df is not None and not df.empty:
            saved = save_dataframe_to_db(df, symbol, market)
            print(f"   ✅ 成功保存 {saved} 条记录")
            success_count += 1
            total_records += saved
        else:
            print(f"   ❌ 无数据")
            fail_count += 1
            failed_symbols.append(f"{name} ({symbol})")
        
        time.sleep(0.5) # 避免请求过快
        
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        fail_count += 1
        failed_symbols.append(f"{name} ({symbol})")

# ============================================
# 2. 下载自选股的历史数据
# ============================================
print("\n" + "=" * 60)
print("📈 第二步：下载自选股历史数据")
print("-" * 60)

with Session(engine) as session:
    watchlist = list(session.exec(select(Watchlist)).all())
    print(f"共 {len(watchlist)} 只自选股需要下载\n")
    
    for idx, item in enumerate(watchlist, 1):
        try:
            print(f"[{idx}/{len(watchlist)}] {item.name} ({item.symbol}, {item.market})...")
            
            # 获取数据
            df = None
            if item.market == 'CN':
                df = fetcher.fetch_cn_daily_data(item.symbol)
            elif item.market == 'HK':
                df = fetcher.fetch_hk_daily_data(item.symbol)
            elif item.market == 'US':
                df = fetcher.fetch_us_daily_data(item.symbol)
            
            if df is not None and not df.empty:
                saved = save_dataframe_to_db(df, item.symbol, item.market)
                print(f"   ✅ 成功保存 {saved} 条记录")
                success_count += 1
                total_records += saved
            else:
                print(f"   ❌ 无数据")
                fail_count += 1
                failed_symbols.append(f"{item.name} ({item.symbol})")
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"   ❌ 错误: {e}")
            fail_count += 1
            failed_symbols.append(f"{item.name} ({item.symbol})")

# ============================================
# 3. 总结报告
# ============================================
print("\n" + "=" * 60)
print("📋 下载完成统计")
print("=" * 60)
print(f"✅ 成功: {success_count} 个标的")
print(f"📊 总记录数: {total_records} 条")
print(f"❌ 失败: {fail_count} 个标的")

if failed_symbols:
    print(f"\n⚠️  失败列表:")
    for sym in failed_symbols:
        print(f"   - {sym}")

print("\n🎉 全量下载完成！数据已保存到 MarketDataDaily 表")
print("💡 提示：现在可以运行 sync-indices 来更新 MarketSnapshot 表")
