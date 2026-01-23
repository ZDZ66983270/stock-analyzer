"""
全量下载历史行情数据到下载库(MarketDataDaily)
- 保存原始数据，不做ETL清洗
- 支持去重检查
"""
import sys
sys.path.insert(0, 'backend')

from data_fetcher_base import DataFetcher
from utils.symbol_utils import normalize_symbol_db
from database import engine
from sqlmodel import Session, select
from models import Watchlist, MarketDataDaily
from symbols_config import get_all_indices, get_symbol_info
import time
import pandas as pd
from datetime import datetime

print("🚀 开始全量下载历史行情数据到下载库...")
print("=" * 70)

fetcher = DataFetcher()
success_count = 0
fail_count = 0
total_records = 0
failed_symbols = []

def get_db_data_info(symbol: str, market: str):
    """查询数据库中该标的数据的范围和行数"""
    db_symbol = normalize_symbol_db(symbol, market)
    with Session(engine) as session:
        # 统计总数、最早日期、最晚日期
        from sqlalchemy import func
        res = session.exec(
            select(
                func.count(MarketDataDaily.id),
                func.min(MarketDataDaily.timestamp),
                func.max(MarketDataDaily.timestamp)
            ).where(
                MarketDataDaily.symbol == db_symbol,
                MarketDataDaily.market == market
            )
        ).first()
        return res # (count, min_ts, max_ts)

def save_raw_data_to_db(df: pd.DataFrame, symbol: str, market: str) -> int:
    """保存原始DataFrame到MarketDataDaily (支持静默查重)"""
    if df is None or df.empty:
        return 0
    
    count = 0
    db_symbol = normalize_symbol_db(symbol, market)
    
    with Session(engine) as session:
        # 为了加速，我们可以先获取该标的所有已有的日期集合
        existing_days = set(session.exec(
            select(MarketDataDaily.timestamp).where(
                MarketDataDaily.symbol == db_symbol,
                MarketDataDaily.market == market
            )
        ).all())

        for _, row in df.iterrows():
            # Data Cleaning for Open/High/Low
            # For Funds/Indices, Open/High/Low might be NaN. Fill with Close if so.
            close_val = float(row.get('收盘', row.get('close', row.get('Close', 0))))
            if pd.isna(close_val): close_val = 0.0

            def get_val(keys, default=0.0):
                for k in keys:
                    if k in row and not pd.isna(row.get(k)):
                        return float(row.get(k))
                return default

            open_val = get_val(['开盘', 'open', 'Open'], default=close_val)
            high_val = get_val(['最高', 'high', 'High'], default=close_val)
            low_val = get_val(['最低', 'low', 'Low'], default=close_val)

            try:
                date_value = str(row.get('时间', row.get('date', row.get('Date', ''))))
                if not date_value or date_value in existing_days:
                    continue
                
                record = MarketDataDaily(
                    symbol=db_symbol,
                    market=market,
                    timestamp=date_value,
                    open=open_val,
                    high=high_val,
                    low=low_val,
                    close=close_val,
                    volume=int(row.get('成交量', row.get('volume', row.get('Volume', 0)))),
                    turnover=float(row.get('成交额', row.get('turnover', 0))) if row.get('成交额', row.get('turnover')) else 0,
                    updated_at=datetime.now()
                )
                
                session.add(record)
                count += 1
            except Exception: continue
        
        if count > 0:
            session.commit()
    return count

# ==================================================================
# 1. 下载所有指数的历史数据
# ==================================================================
print("\n📊 第一步：下载指数历史数据")
print("-" * 70)

indices = get_all_indices()
print(f"共 {len(indices)} 个指数\n")

for idx, symbol in enumerate(indices, 1):
    try:
        info = get_symbol_info(symbol)
        name = info.get("name", symbol)
        market = info.get("market", "US")
        
        # --- 增量下载决策 (Pre-check) ---
        db_count, min_ts, max_ts = get_db_data_info(symbol, market)
        
        # 默认回溯到 2015
        target_start = '20150101'
        
        # 决策：
        # 1. 如果已有记录且比较完整（比如最近两天有更新），且历史也够深（2015附近），则只做日常同步（过去 7 天以防节假日）
        today_str = datetime.now().strftime('%Y%m%d')
        if db_count > 0 and max_ts and max_ts >= datetime.now().strftime('%Y-%m-%d'):
             # 已经是最新，且历史也覆盖了
             if min_ts and min_ts.replace('-', '') <= target_start:
                 print(f"ℹ️ 已达深度且为最新 (共 {db_count} 条)")
                 success_count += 1
                 continue
        
        # 2. 如果 max_ts 较旧，或者没有数据，则确定 fetch 范围
        fetch_start = target_start
        if db_count > 100: # 如果已经有一定的历史了
             # 我们主要关心两个方向：向前补历史，向后补更新
             # 这里简化逻辑：如果历史不够深，依然从 2015 开始拉全量（接口通常支持，查重会过滤）
             # 如果历史够深但日期没更新，从 max_ts 开始拉
             if min_ts and min_ts.replace('-', '') <= target_start:
                 fetch_start = max_ts.replace('-', '') if max_ts else target_start
        
        # 获取数据
        df = None
        if market == 'CN':
            df = fetcher.fetch_cn_daily_data(symbol, start_date=fetch_start)
        elif market == 'HK':
            df = fetcher.fetch_hk_daily_data(symbol, start_date=fetch_start)
        elif market == 'US':
            # US 接口目前主要支持 period
            df = fetcher.fetch_us_daily_data(symbol, period='10y' if db_count < 500 else '1mo')
        
        if df is not None and not df.empty:
            saved = save_raw_data_to_db(df, symbol, market)
            if saved > 0:
                print(f"✅ 同步完成 (新增 {saved} 条)")
            else:
                print(f"ℹ️ 数据已存在")
            success_count += 1
            total_records += saved
        else:
            print(f"❌ 获取失败 (无数据)")
            fail_count += 1
            failed_symbols.append(f"{name} ({symbol})")
        
        time.sleep(0.3)  # 避免请求过快
        
    except Exception as e:
        print(f"❌ {e}")
        fail_count += 1
        failed_symbols.append(f"{name} ({symbol})")

# ==================================================================
# 2. 下载自选股的历史数据
# ==================================================================
print("\n" + "=" * 70)
print("📈 第二步：下载自选股历史数据")
print("-" * 70)

with Session(engine) as session:
    watchlist = list(session.exec(select(Watchlist)).all())
    print(f"共 {len(watchlist)} 只自选股\n")
    
    for idx, item in enumerate(watchlist, 1):
        try:
            # --- 增量下载决策 (Pre-check) ---
            db_count, min_ts, max_ts = get_db_data_info(item.symbol, item.market)
            target_start = '20150101'
            
            if db_count > 0 and max_ts and max_ts >= datetime.now().strftime('%Y-%m-%d'):
                 if min_ts and min_ts.replace('-', '') <= target_start:
                     print(f"ℹ️ 已达深度且为最新")
                     success_count += 1
                     continue
            
            fetch_start = target_start
            if db_count > 100:
                 if min_ts and min_ts.replace('-', '') <= target_start:
                     fetch_start = max_ts.replace('-', '') if max_ts else target_start

            # 从 Canonical ID 提取纯代码
            code = item.symbol.split(':')[-1] if ':' in item.symbol else item.symbol
            
            # 获取数据
            df = None
            if item.market == 'CN':
                df = fetcher.fetch_cn_daily_data(code, start_date=fetch_start)
            elif item.market == 'HK':
                df = fetcher.fetch_hk_daily_data(code, start_date=fetch_start)
            elif item.market == 'US':
                df = fetcher.fetch_us_daily_data(code, period='10y' if db_count < 500 else '1mo')
            
            if df is not None and not df.empty:
                saved = save_raw_data_to_db(df, item.symbol, item.market)
                if saved > 0:
                    print(f"✅ 同步完成 (新增 {saved} 条)")
                    success_count += 1
                else:
                    print(f"ℹ️ 无需更新")
                    success_count += 1
                total_records += saved
            else:
                print(f"❌ 获取失败 (无数据)")
                fail_count += 1
                failed_symbols.append(f"{item.name} ({item.symbol})")
            
            time.sleep(0.3)
            
        except Exception as e:
            print(f"❌ {e}")
            fail_count += 1
            failed_symbols.append(f"{item.name} ({item.symbol})")

# ==================================================================
# 3. 总结报告
# ==================================================================
print("\n" + "=" * 70)
print("📋 下载完成统计")
print("=" * 70)
print(f"✅ 成功: {success_count} 个")
print(f"📊 总记录: {total_records} 条")
print(f"❌ 失败: {fail_count} 个")

if failed_symbols:
    print(f"\n⚠️  失败列表:")
    for sym in failed_symbols:
        print(f"   - {sym}")

print("\n" + "=" * 70)
print("🎉 原始数据已保存到下载库 (MarketDataDaily)")
print("💡 下一步：检查数据质量，确认无误后再执行ETL清洗")
print("=" * 70)
