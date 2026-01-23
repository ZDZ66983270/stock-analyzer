#!/usr/bin/env python3
"""
手工下载30天历史数据 - 简化版
直接使用yfinance下载，然后调用run_etl处理
"""
import sys
sys.path.append('backend')

import yfinance as yf
from database import engine
from sqlmodel import Session, select
from models import Watchlist
import subprocess
import time

def convert_to_yfinance_symbol(symbol: str, market: str) -> str:
    """转换为yfinance格式"""
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

def download_and_save(symbol: str, market: str, days: int = 30):
    """下载数据并保存为CSV，然后调用run_etl处理"""
    yf_symbol = convert_to_yfinance_symbol(symbol, market)
    
    print(f"\n{'='*60}")
    print(f"下载 {symbol} ({market}) -> {yf_symbol}")
    print(f"{'='*60}")
    
    try:
        # 下载数据
        ticker = yf.Ticker(yf_symbol)
        df = ticker.history(period=f"{days}d", auto_adjust=True)
        
        if df.empty:
            print(f"⚠️  无数据")
            return False
        
        # 保存为CSV
        csv_file = f"/tmp/{symbol.replace('.', '_')}_{market}_history.csv"
        df.to_csv(csv_file)
        print(f"✅ 已下载 {len(df)} 条记录")
        print(f"📁 保存至: {csv_file}")
        
        # 调用run_etl处理
        print(f"🔄 执行ETL处理...")
        result = subprocess.run(
            ["python3", "run_etl.py", "--symbol", symbol, "--market", market, "--file", csv_file],
            cwd="/Users/zhangzy/My Docs/Privates/22-AI编程/AI+风控App/web-app",
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ ETL处理成功")
            return True
        else:
            print(f"❌ ETL处理失败:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def main():
    print("=" * 80)
    print("📊 手工下载30天历史数据")
    print("=" * 80)
    
    # 获取所有watchlist
    with Session(engine) as session:
        watchlist = list(session.exec(select(Watchlist)).all())
    
    if not watchlist:
        print("⚠️  Watchlist为空")
        return
    
    print(f"\n共 {len(watchlist)} 个标的\n")
    
    success_count = 0
    fail_count = 0
    
    for idx, item in enumerate(watchlist, 1):
        print(f"\n[{idx}/{len(watchlist)}] {item.name}")
        
        if download_and_save(item.symbol, item.market, days=30):
            success_count += 1
        else:
            fail_count += 1
        
        # 避免请求过快
        time.sleep(1)
    
    # 总结
    print("\n" + "=" * 80)
    print("📋 下载完成统计")
    print("=" * 80)
    print(f"✅ 成功: {success_count} 个")
    print(f"❌ 失败: {fail_count} 个")
    print("=" * 80)

if __name__ == "__main__":
    main()
