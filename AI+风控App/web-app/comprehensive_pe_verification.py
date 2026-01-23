#!/usr/bin/env python3
"""
全面的 PE 验证脚本 - 对比 VERA 数据库与 Yahoo Finance 官方数据
"""
import sys
sys.path.append('backend')
from sqlmodel import Session, select
from backend.database import engine
from backend.models import MarketDataDaily, FinancialFundamentals
from backend.symbols_config import get_yfinance_symbol
import yfinance as yf
from datetime import datetime

def verify_stock_pe(symbol, market, name):
    """验证单个股票的 PE 计算"""
    print(f"\n{'='*80}")
    print(f"验证: {name} ({symbol})")
    print(f"{'='*80}\n")
    
    # 1. 获取 Yahoo Finance 官方数据
    yf_symbol = get_yfinance_symbol(symbol, market)
    try:
        ticker = yf.Ticker(yf_symbol)
        info = ticker.info
        
        yf_price = info.get('currentPrice') or info.get('regularMarketPreviousClose')
        yf_pe = info.get('trailingPE')
        yf_eps = info.get('trailingEps')
        
        print(f"📊 Yahoo Finance 官方数据:")
        print(f"  价格: ${yf_price:.2f}" if yf_price else "  价格: N/A")
        print(f"  Trailing PE: {yf_pe:.2f}" if yf_pe else "  Trailing PE: N/A")
        print(f"  Trailing EPS: {yf_eps:.2f}" if yf_eps else "  Trailing EPS: N/A")
        
        if yf_price and yf_eps:
            calculated_pe = yf_price / yf_eps
            print(f"  验证: {yf_price:.2f} / {yf_eps:.2f} = {calculated_pe:.2f} ✅")
    except Exception as e:
        print(f"⚠️  无法获取 Yahoo Finance 数据: {e}")
        yf_price = yf_pe = yf_eps = None
    
    # 2. 获取 VERA 数据库数据
    with Session(engine) as session:
        # 最新日线数据
        latest_daily = session.exec(
            select(MarketDataDaily)
            .where(MarketDataDaily.symbol == symbol)
            .order_by(MarketDataDaily.timestamp.desc())
            .limit(1)
        ).first()
        
        if not latest_daily:
            print(f"\n❌ 数据库中没有 {symbol} 的日线数据")
            return
        
        print(f"\n💾 VERA 数据库 (最新日线):")
        print(f"  日期: {latest_daily.timestamp}")
        print(f"  收盘价: ${latest_daily.close:.2f}")
        print(f"  数据库 PE: {latest_daily.pe:.2f}" if latest_daily.pe else "  数据库 PE: N/A")
        print(f"  数据库 EPS: {latest_daily.eps:.2f}" if latest_daily.eps else "  数据库 EPS: N/A")
        
        if latest_daily.pe and latest_daily.eps:
            recalc_pe = latest_daily.close / latest_daily.eps
            print(f"  验证: {latest_daily.close:.2f} / {latest_daily.eps:.2f} = {recalc_pe:.2f}")
        
        # 财报数据
        financials = session.exec(
            select(FinancialFundamentals)
            .where(FinancialFundamentals.symbol == symbol)
            .order_by(FinancialFundamentals.as_of_date.desc())
        ).all()
        
        if not financials:
            print(f"\n❌ 数据库中没有 {symbol} 的财报数据")
            return
        
        # 计算 TTM EPS
        quarterly = [f for f in financials if f.report_type == 'quarterly']
        annual = [f for f in financials if f.report_type == 'annual']
        
        print(f"\n📈 财报数据:")
        print(f"  季度报告: {len(quarterly)} 条")
        print(f"  年度报告: {len(annual)} 条")
        
        if len(quarterly) >= 4:
            print(f"\n  最近4个季度:")
            ttm_eps = 0
            ttm_income = 0
            for i, q in enumerate(quarterly[:4]):
                print(f"    Q{4-i} ({q.as_of_date}): EPS {q.eps_ttm:.2f}, 净利润 {q.net_income_ttm/1e9:.2f}亿")
                ttm_eps += q.eps_ttm if q.eps_ttm else 0
                ttm_income += q.net_income_ttm if q.net_income_ttm else 0
            
            print(f"\n  ✅ 正确的 TTM EPS (4季度总和): {ttm_eps:.2f}")
            print(f"  ✅ 正确的 TTM 净利润: {ttm_income/1e9:.2f}亿")
            
            if latest_daily.close:
                correct_pe = latest_daily.close / ttm_eps
                print(f"  ✅ 正确的 PE 应该是: {latest_daily.close:.2f} / {ttm_eps:.2f} = {correct_pe:.2f}")
                
                # 对比
                print(f"\n🔍 对比分析:")
                if latest_daily.pe:
                    diff_pct = abs(latest_daily.pe - correct_pe) / correct_pe * 100
                    status = "✅" if diff_pct < 5 else "❌"
                    print(f"  数据库 PE: {latest_daily.pe:.2f}")
                    print(f"  正确 PE: {correct_pe:.2f}")
                    print(f"  偏差: {diff_pct:.2f}% {status}")
                
                if yf_pe:
                    diff_vs_yf = abs(correct_pe - yf_pe) / yf_pe * 100
                    status = "✅" if diff_vs_yf < 5 else "⚠️"
                    print(f"\n  VERA 正确 PE vs Yahoo PE:")
                    print(f"  VERA: {correct_pe:.2f}")
                    print(f"  Yahoo: {yf_pe:.2f}")
                    print(f"  偏差: {diff_vs_yf:.2f}% {status}")
        
        elif annual:
            latest_annual = annual[0]
            print(f"\n  最新年报 ({latest_annual.as_of_date}):")
            print(f"    EPS: {latest_annual.eps_ttm:.2f}")
            print(f"    净利润: {latest_annual.net_income_ttm/1e9:.2f}亿")

def main():
    """验证所有关键股票"""
    stocks = [
        ("US:STOCK:MSFT", "US", "微软"),
        ("US:STOCK:TSLA", "US", "特斯拉"),
        ("US:STOCK:AAPL", "US", "苹果"),
        ("HK:STOCK:00700", "HK", "腾讯"),
        ("CN:STOCK:600030", "CN", "中信证券"),
    ]
    
    print("\n" + "="*80)
    print("PE 计算全面验证报告")
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    for symbol, market, name in stocks:
        verify_stock_pe(symbol, market, name)
    
    print(f"\n{'='*80}")
    print("验证完成")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
