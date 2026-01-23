#!/usr/bin/env python3
"""
最终 PE 验证报告
验证所有市场的 PE 计算准确性
"""
import sys
sys.path.append('backend')
from sqlmodel import Session, select
from backend.database import engine
from backend.models import MarketDataDaily
from backend.symbols_config import get_yfinance_symbol
import yfinance as yf

stocks = [
    # 美股
    ("US:STOCK:MSFT", "US", "微软"),
    ("US:STOCK:AAPL", "US", "苹果"),
    ("US:STOCK:TSLA", "US", "特斯拉"),
    # 港股
    ("HK:STOCK:00700", "HK", "腾讯控股"),
    ("HK:STOCK:09988", "HK", "阿里巴巴-W"),
    # A股
    ("CN:STOCK:600030", "CN", "中信证券"),
]

print("="*100)
print("最终 PE 验证报告")
print("="*100)
print(f"\n{'股票':<20} {'VERA PE':<12} {'Yahoo PE':<12} {'偏差':<10} {'状态':<8}")
print("-"*100)

results = []

with Session(engine) as session:
    for symbol, market, name in stocks:
        # 获取 VERA 数据
        daily = session.exec(
            select(MarketDataDaily)
            .where(MarketDataDaily.symbol == symbol)
            .order_by(MarketDataDaily.timestamp.desc())
            .limit(1)
        ).first()
        
        if not daily or not daily.pe:
            print(f"{name:<20} {'N/A':<12} {'N/A':<12} {'N/A':<10} {'❌':<8}")
            continue
        
        vera_pe = daily.pe
        
        # 获取 Yahoo 数据
        try:
            yf_symbol = get_yfinance_symbol(symbol, market)
            ticker = yf.Ticker(yf_symbol)
            yahoo_pe = ticker.info.get('trailingPE')
            
            if yahoo_pe:
                diff_pct = abs(vera_pe - yahoo_pe) / yahoo_pe * 100
                status = "✅" if diff_pct < 5 else "⚠️" if diff_pct < 10 else "❌"
                
                print(f"{name:<20} {vera_pe:<12.2f} {yahoo_pe:<12.2f} {diff_pct:<10.1f}% {status:<8}")
                
                results.append({
                    'name': name,
                    'vera_pe': vera_pe,
                    'yahoo_pe': yahoo_pe,
                    'diff': diff_pct,
                    'ok': diff_pct < 10
                })
            else:
                print(f"{name:<20} {vera_pe:<12.2f} {'N/A':<12} {'N/A':<10} {'⚠️':<8}")
        except Exception as e:
            print(f"{name:<20} {vera_pe:<12.2f} {'Error':<12} {'N/A':<10} {'❌':<8}")

print("\n" + "="*100)
print("总结")
print("="*100)

if results:
    ok_count = sum(1 for r in results if r['ok'])
    total = len(results)
    
    # 计算统计指标
    diffs = sorted([r['diff'] for r in results])
    min_diff = min(diffs)
    max_diff = max(diffs)
    median_diff = diffs[len(diffs)//2] if len(diffs) % 2 == 1 else (diffs[len(diffs)//2-1] + diffs[len(diffs)//2]) / 2
    
    print(f"\n通过率: {ok_count}/{total} ({ok_count/total*100:.1f}%)")
    print(f"\n偏差统计:")
    print(f"  最小偏差: {min_diff:.2f}%")
    print(f"  中位数偏差: {median_diff:.2f}%")
    print(f"  最大偏差: {max_diff:.2f}%")
    
    print(f"\n按市场统计:")
    for market_name in ["美股", "港股", "A股"]:
        market_results = [r for r in results if any(market_name in r['name'] for r in results)]
        if market_results:
            market_ok = sum(1 for r in market_results if r['ok'])
            market_total = len(market_results)
            print(f"  {market_name}: {market_ok}/{market_total} 通过")

print("\n✅ PE 验证完成！")
