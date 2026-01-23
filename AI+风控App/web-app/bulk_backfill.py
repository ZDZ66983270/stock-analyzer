#!/usr/bin/env python3
"""
批量下载指定股票的全量历史数据

用法：
python3 bulk_backfill.py --symbol 01810.HK --years 5
python3 bulk_backfill.py --all --days 365
"""
import sys
import argparse
import sys
import argparse
import os

# Add backend to sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend'))
if backend_path not in sys.path:
    sys.path.append(backend_path)

from database import engine
from sqlmodel import Session, select
from models import Watchlist

import yfinance as yf
import json
from datetime import datetime
import pandas as pd
from models import RawMarketData
from etl_service import ETLService
from symbol_utils import get_yahoo_symbol

def backfill_symbol(symbol, market, days=None):
    """为单个股票下载历史数据"""
    print(f"\n{'='*60}")
    print(f"下载 {symbol} ({market}) 历史数据")
    print(f"{'='*60}")
    
    # 1. 转换符号
    pure_code = symbol.split(':')[-1] if ':' in symbol else symbol
    yf_symbol = get_yahoo_symbol(pure_code, market)
    
    # 2. 确定天数
    period = "max"
    if days:
        if days <= 5: period = "5d"
        elif days <= 30: period = "1mo"
        elif days <= 365: period = "1y"
        elif days <= 365 * 2: period = "2y"
        elif days <= 365 * 5: period = "5y"
        elif days <= 365 * 10: period = "10y"
    
    print(f"📡 正在从 yfinance 获取 {yf_symbol} ({period})...")
    
    try:
        ticker = yf.Ticker(yf_symbol)
        df = ticker.history(period=period, auto_adjust=True)
        
        if df.empty:
            print(f"❌ 失败: yfinance 未返回任何数据")
            return {'success': False, 'message': 'No data'}
            
        print(f"✅ 获取到 {len(df)} 条记录")
        
        # 3. 格式化数据并保存到 Raw
        df_reset = df.reset_index()
        rename_map = {
            'Date': 'timestamp', 'Datetime': 'timestamp',
            'Open': 'open', 'High': 'high', 'Low': 'low', 
            'Close': 'close', 'Volume': 'volume'
        }
        df_reset = df_reset.rename(columns=rename_map)
        
        if 'timestamp' in df_reset.columns:
            df_reset['timestamp'] = pd.to_datetime(df_reset['timestamp']).dt.strftime('%Y-%m-%d')
            
        records = df_reset.to_dict(orient='records')
        payload = {
            "symbol": symbol, "market": market, "source": "yfinance_bulk",
            "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data": records
        }
        
        with Session(engine) as session:
            raw = RawMarketData(
                symbol=symbol, market=market, source="yfinance",
                period="1d", payload=json.dumps(payload), processed=False
            )
            session.add(raw)
            session.commit()
            raw_id = raw.id
            
        print(f"⚡ 正在触发 ETL 处理 (ID: {raw_id})...")
        ETLService.process_raw_data(raw_id)
        print(f"✨ {symbol} 补全完成")
        
        return {'success': True, 'records_fetched': len(df)}
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        return {'success': False, 'message': str(e)}

def main():
    parser = argparse.ArgumentParser(description='批量下载历史数据')
    parser.add_argument('--symbol', help='指定股票代码')
    parser.add_argument('--market', help='市场 (CN/HK/US)')
    parser.add_argument('--days', type=int, help='下载天数（不指定=全量）')
    parser.add_argument('--years', type=int, help='下载年数（转换为days）')
    parser.add_argument('--all', action='store_true', help='下载所有watchlist')
    
    args = parser.parse_args()
    
    # 计算days
    days = args.days
    if args.years:
        days = args.years * 365
    
    if args.all:
        # 下载所有watchlist
        print("\n下载所有watchlist的历史数据")
        with Session(engine) as session:
            items = session.exec(select(Watchlist)).all()
            
            print(f"共{len(items)}个标的")
            for item in items:
                backfill_symbol(item.symbol, item.market, days)
    
    elif args.symbol and args.market:
        # 下载单个
        backfill_symbol(args.symbol, args.market, days)
    
    else:
        parser.print_help()
        print("\n示例：")
        print("  # 下载01810.HK的全量数据")
        print("  python3 bulk_backfill.py --symbol 01810.HK --market HK")
        print("")
        print("  # 下载所有watchlist最近1年数据")
        print("  python3 bulk_backfill.py --all --years 1")
        print("")
        print("  # 下载所有watchlist全量数据（不限制天数）")
        print("  python3 bulk_backfill.py --all")

if __name__ == "__main__":
    main()
