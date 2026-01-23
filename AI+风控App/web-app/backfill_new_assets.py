#!/usr/bin/env python3
"""
新增标的历史数据回填脚本
通过 RawMarketData -> ETL 流水线补全 10 年历史
"""
import sys
import os
import json
import time
import yfinance as yf
from datetime import datetime
from sqlmodel import Session

sys.path.append(os.path.join(os.getcwd(), 'backend'))
from database import engine
from models import RawMarketData, Watchlist, Index
from etl_service import ETLService
from sqlmodel import select

# 新增标的清单 (通过sync脚本识别)
NEW_ASSETS = [
    {"symbol": "IBIT", "market": "US", "name": "iShares比特币信托"},
    {"symbol": "06099.HK", "market": "HK", "name": "招商证券"},
    {"symbol": "03110.HK", "market": "HK", "name": "3110"},  
    {"symbol": "03437.HK", "market": "HK", "name": "博时央企红利"},
    {"symbol": "03447.HK", "market": "HK", "name": "南方亚太房托"},
    {"symbol": "HSCC", "market": "HK", "name": "红筹指数"},
    {"symbol": "HSCE", "market": "HK", "name": "国企指数"},
]

def get_yfinance_symbol(symbol: str, market: str) -> str:
    """符号转换为 yfinance 格式"""
    s = symbol.strip().upper()
    
    if market == "US":
        return s
    elif market == "HK":
        # HK stocks: 去掉前导0, 至少保留 4 位
        if s.endswith('.HK'):
            code = s.replace('.HK', '')
            if code.isdigit():
                return f"{int(code):04d}.HK"
        elif s.isdigit():
            return f"{int(s):04d}.HK"
        # HK indices
        if s == "HSI": return "^HSI"
        if s == "HSTECH": return "^HSTECH"
        if s == "HSCC": return "^HSCC"  # 红筹指数
        if s == "HSCE": return "^HSCE"  # 国企指数
        return s
    elif market == "CN":
        # A-share stocks
        if s.startswith("6"):
            return f"{s}.SS"
        if s.startswith("0") or s.startswith("3"):
            return f"{s}.SZ"
    
    return s

def backfill_new_assets():
    print("🚀 开始补全新增标的的历史数据...")
    print(f"📋 共 {len(NEW_ASSETS)} 个新标的\n")
    
    success_count = 0
    fail_count = 0
    
    for idx, asset in enumerate(NEW_ASSETS, 1):
        symbol = asset["symbol"]
        market = asset["market"]
        name = asset["name"]
        
        print(f"[{idx}/{len(NEW_ASSETS)}] {symbol} ({name}) - {market}")
        
        try:
            # 1. 转换符号
            yf_symbol = get_yfinance_symbol(symbol, market)
            print(f"  📡 yfinance symbol: {yf_symbol}")
            
            # 2. 获取 10 年历史数据
            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(period="10y", interval="1d", auto_adjust=True)
            
            if df.empty:
                print(f"  ⚠️  yfinance 没有返回数据")
                fail_count += 1
                continue
            
            print(f"  ✅ 获取到 {len(df)} 条记录")
            
            # 3. 格式化数据
            df = df.reset_index()
            df = df.rename(columns={
                'Date': 'timestamp',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            # 时间戳转字符串
            df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            records = df.to_dict(orient='records')
            
            # 4. 构造 Payload
            payload = {
                "symbol": symbol,
                "market": market,
                "source": "yfinance_backfill",
                "data": records
            }
            
            # 5. 存入 RawMarketData
            with Session(engine) as session:
                raw_record = RawMarketData(
                    symbol=symbol,
                    market=market,
                    source="yfinance",
                    period="1d",
                    fetch_time=datetime.now(),
                    payload=json.dumps(payload),
                    processed=False
                )
                session.add(raw_record)
                session.commit()
                session.refresh(raw_record)
                raw_id = raw_record.id
            
            print(f"  💾 Raw ID: {raw_id}")
            
            # 6. 触发 ETL
            print(f"  ⚡ 触发 ETL...")
            ETLService.process_raw_data(raw_id)
            print(f"  ✅ {symbol} 补全完成\n")
            
            success_count += 1
            
        except Exception as e:
            print(f"  ❌ 错误: {e}\n")
            fail_count += 1
        
        time.sleep(1)  # 避免频控
    
    print("=" * 60)
    print(f"🏁 补全完成: 成功 {success_count}, 失败 {fail_count}")
    print("=" * 60)

if __name__ == "__main__":
    backfill_new_assets()
