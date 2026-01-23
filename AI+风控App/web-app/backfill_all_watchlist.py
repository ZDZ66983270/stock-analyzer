#!/usr/bin/env python3
"""
批量回填历史数据 - 使用DataFetcher V2
为所有watchlist股票下载30天历史数据
"""
import sys
sys.path.append('backend')

import yfinance as yf
import logging
from datetime import datetime
from database import engine
from sqlmodel import Session, select
from models import Watchlist, RawMarketData
from etl_service import ETLService
import json
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def convert_to_yfinance_symbol(symbol: str, market: str) -> str:
    """转换为yfinance格式"""
    # 从 Canonical ID 提取纯代码 (US:STOCK:AAPL -> AAPL)
    if ':' in symbol:
        symbol = symbol.split(':')[-1]
    
    s = symbol.strip().upper()
    if "." in s:
        return s
    
    if market == "US":
        return s
    elif market == "HK":
        if s.isdigit():
            return f"{int(s):05d}.HK"
        if s == "HSI":
            return "^HSI"
        if s == "HSTECH":
            return "^HSTECH"
        return f"{s}.HK"
    elif market == "CN":
        if s.startswith("6"):
            return f"{s}.SS"
        if s.startswith("0") or s.startswith("3"):
            return f"{s}.SZ"
        if s.startswith("4") or s.startswith("8"):
            return f"{s}.BJ"
    
    return s

def backfill_symbol(symbol: str, market: str, days: int = 30):
    """为单个股票回填历史数据"""
    yf_symbol = convert_to_yfinance_symbol(symbol, market)
    
    logger.info(f"📥 Fetching {symbol} ({market}) -> {yf_symbol}, {days} days")
    
    try:
        # 使用yfinance获取历史数据
        ticker = yf.Ticker(yf_symbol)
        df = ticker.history(period=f"{days}d", auto_adjust=True)
        
        if df.empty:
            logger.warning(f"⚠️  No data returned for {symbol}")
            return 0
        
        # 准备数据
        df_reset = df.reset_index()
        rename_map = {
            'Date': 'timestamp', 'Datetime': 'timestamp',
            'Open': 'open', 'High': 'high', 'Low': 'low',
            'Close': 'close', 'Volume': 'volume'
        }
        df_reset = df_reset.rename(columns=rename_map)
        
        # 转换时间戳为字符串
        if 'timestamp' in df_reset.columns:
            df_reset['timestamp'] = df_reset['timestamp'].dt.strftime('%Y-%m-%d')
        
        records = df_reset.to_dict(orient='records')
        
        # 保存到RawMarketData
        payload = {
            "symbol": symbol,
            "market": market,
            "source": "yfinance",
            "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data": records
        }
        
        with Session(engine) as session:
            raw = RawMarketData(
                symbol=symbol,
                market=market,
                source="yfinance",
                period=f"{days}d",
                payload=json.dumps(payload),
                processed=False
            )
            session.add(raw)
            session.commit()
            raw_id = raw.id
        
        # 触发ETL处理
        logger.info(f"   🔄 Processing ETL for raw_id={raw_id}")
        ETLService.process_raw_data(raw_id)
        
        logger.info(f"   ✅ Success: {len(records)} records")
        return len(records)
        
    except Exception as e:
        logger.error(f"   ❌ Error: {e}")
        return 0

def main():
    print("=" * 80)
    print("📊 批量回填历史数据")
    print("=" * 80)
    
    # 获取所有watchlist
    with Session(engine) as session:
        watchlist = list(session.exec(select(Watchlist)).all())
    
    if not watchlist:
        print("⚠️  Watchlist为空")
        return
    
    print(f"\n共 {len(watchlist)} 个标的\n")
    
    total_records = 0
    success_count = 0
    fail_count = 0
    
    for idx, item in enumerate(watchlist, 1):
        print(f"\n[{idx}/{len(watchlist)}] {item.name} ({item.symbol}, {item.market})")
        
        records = backfill_symbol(item.symbol, item.market, days=30)
        
        if records > 0:
            success_count += 1
            total_records += records
        else:
            fail_count += 1
        
        # 避免请求过快
        time.sleep(0.5)
    
    # 总结
    print("\n" + "=" * 80)
    print("📋 回填完成统计")
    print("=" * 80)
    print(f"✅ 成功: {success_count} 个")
    print(f"📊 总记录: {total_records} 条")
    print(f"❌ 失败: {fail_count} 个")
    print("=" * 80)

if __name__ == "__main__":
    main()
