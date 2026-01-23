#!/usr/bin/env python3
"""
PE 计算偏差验证脚本
对比三种 PE 计算方式，确认偏差来源：
1. Yahoo 官方 PE (trailingPE)
2. 用 Yahoo EPS 重算 (price / trailingEps)
3. VERA 当前计算 (close / vera_ttm_eps)
"""
import sys
sys.path.append('backend')

import yfinance as yf
from database import engine
from sqlmodel import Session, select
from models import MarketDataDaily, FinancialFundamentals, Watchlist
from datetime import datetime

def verify_pe_calculation(symbol_code, canonical_id):
    """验证单个股票的 PE 计算"""
    print(f"\n{'='*80}")
    print(f"验证股票: {symbol_code} ({canonical_id})")
    print(f"{'='*80}")
    
    # 1. 从 Yahoo 获取数据
    ticker = yf.Ticker(symbol_code)
    info = ticker.info
    
    price_yahoo = info.get('regularMarketPrice') or info.get('currentPrice')
    trailing_pe_yahoo = info.get('trailingPE')
    trailing_eps_yahoo = info.get('trailingEps')
    
    print(f"\n📊 Yahoo Finance 数据:")
    print(f"  当前价格: {price_yahoo}")
    print(f"  Trailing PE (官方): {trailing_pe_yahoo}")
    print(f"  Trailing EPS: {trailing_eps_yahoo}")
    
    # 2. 用 Yahoo EPS 重算 PE
    if price_yahoo and trailing_eps_yahoo:
        pe_from_eps = price_yahoo / trailing_eps_yahoo
        print(f"\n🔢 用 Yahoo EPS 重算:")
        print(f"  PE = {price_yahoo} / {trailing_eps_yahoo} = {pe_from_eps:.2f}")
        
        if trailing_pe_yahoo:
            diff_pct = abs(pe_from_eps - trailing_pe_yahoo) / trailing_pe_yahoo * 100
            print(f"  与官方 PE 差异: {diff_pct:.2f}%")
    else:
        pe_from_eps = None
        print(f"\n⚠️ 无法用 Yahoo EPS 重算（缺少价格或 EPS）")
    
    # 3. 从 VERA 数据库获取数据
    with Session(engine) as session:
        # 获取最新行情
        latest_market = session.exec(
            select(MarketDataDaily)
            .where(MarketDataDaily.symbol == canonical_id)
            .order_by(MarketDataDaily.timestamp.desc())
            .limit(1)
        ).first()
        
        # 获取最新财报
        latest_financial = session.exec(
            select(FinancialFundamentals)
            .where(FinancialFundamentals.symbol == canonical_id)
            .order_by(FinancialFundamentals.as_of_date.desc())
            .limit(1)
        ).first()
        
        if latest_market:
            print(f"\n💾 VERA 数据库:")
            print(f"  最新收盘价: {latest_market.close} ({latest_market.timestamp})")
            print(f"  数据库中的 PE: {latest_market.pe}")
            print(f"  数据库中的 EPS: {latest_market.eps}")
            
            if latest_financial:
                print(f"\n  最新财报 ({latest_financial.as_of_date}):")
                print(f"    Net Income TTM: {latest_financial.net_income_ttm}")
                print(f"    EPS TTM: {latest_financial.eps_ttm}")
                print(f"    Data Source: {latest_financial.data_source}")
                
                # 用 VERA 的 EPS 重算 PE
                if latest_market.eps:
                    pe_vera = latest_market.close / latest_market.eps
                    print(f"\n🔢 用 VERA EPS 重算:")
                    print(f"  PE = {latest_market.close} / {latest_market.eps} = {pe_vera:.2f}")
                    
                    if trailing_pe_yahoo:
                        diff_pct = abs(pe_vera - trailing_pe_yahoo) / trailing_pe_yahoo * 100
                        print(f"  与 Yahoo 官方 PE 差异: {diff_pct:.2f}%")
        else:
            print(f"\n⚠️ VERA 数据库中未找到行情数据")
    
    # 4. 对比总结
    print(f"\n{'='*80}")
    print(f"📈 对比总结:")
    print(f"{'='*80}")
    print(f"  Yahoo 官方 PE:        {trailing_pe_yahoo:.2f if trailing_pe_yahoo else 'N/A'}")
    print(f"  Yahoo EPS 重算 PE:    {pe_from_eps:.2f if pe_from_eps else 'N/A'}")
    print(f"  VERA 数据库 PE:       {latest_market.pe:.2f if latest_market and latest_market.pe else 'N/A'}")
    
    if trailing_pe_yahoo and pe_from_eps:
        diff = abs(trailing_pe_yahoo - pe_from_eps) / trailing_pe_yahoo * 100
        status = "✅ 一致" if diff < 1 else "⚠️ 有偏差"
        print(f"\n  Yahoo 官方 vs EPS重算: {status} (差异 {diff:.2f}%)")
    
    if trailing_pe_yahoo and latest_market and latest_market.pe:
        diff = abs(trailing_pe_yahoo - latest_market.pe) / trailing_pe_yahoo * 100
        status = "✅ 一致" if diff < 10 else "❌ 偏差较大"
        print(f"  Yahoo 官方 vs VERA:    {status} (差异 {diff:.2f}%)")

def main():
    """验证所有 Watchlist 中的个股"""
    
    # 从数据库加载所有个股
    with Session(engine) as session:
        stocks = session.exec(
            select(Watchlist)
            .where(Watchlist.symbol.like('%STOCK%'))
            .order_by(Watchlist.market, Watchlist.symbol)
        ).all()
    
    if not stocks:
        print("❌ 未找到任何个股")
        return
    
    print("="*80)
    print("PE 计算偏差验证报告 - 全量个股测试")
    print("="*80)
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试股票数: {len(stocks)} 只")
    
    # 准备测试数据
    test_stocks = []
    for stock in stocks:
        # 从 Canonical ID 提取原始代码
        parts = stock.symbol.split(':')
        if len(parts) == 3:
            market = parts[0]
            code = parts[2]
            
            # 转换为 Yahoo Symbol
            from symbols_config import get_yfinance_symbol
            yahoo_symbol = get_yfinance_symbol(code, market)
            
            test_stocks.append((yahoo_symbol, stock.symbol, stock.name or code))
    
    # 统计结果
    results = {
        'perfect': [],      # 偏差 < 1%
        'excellent': [],    # 偏差 < 5%
        'good': [],         # 偏差 < 10%
        'poor': [],         # 偏差 >= 10%
        'no_data': [],      # 无数据
    }
    
    for yahoo_symbol, canonical_id, name in test_stocks:
        try:
            # 简化验证，只记录关键指标
            ticker = yf.Ticker(yahoo_symbol)
            info = ticker.info
            
            trailing_pe_yahoo = info.get('trailingPE')
            
            # 从 VERA 获取 PE
            with Session(engine) as session:
                latest_market = session.exec(
                    select(MarketDataDaily)
                    .where(MarketDataDaily.symbol == canonical_id)
                    .order_by(MarketDataDaily.timestamp.desc())
                    .limit(1)
                ).first()
                
                vera_pe = latest_market.pe if latest_market else None
            
            # 分类
            if not trailing_pe_yahoo or not vera_pe:
                results['no_data'].append((name, canonical_id))
            else:
                diff_pct = abs(trailing_pe_yahoo - vera_pe) / trailing_pe_yahoo * 100
                if diff_pct < 1:
                    results['perfect'].append((name, canonical_id, diff_pct))
                elif diff_pct < 5:
                    results['excellent'].append((name, canonical_id, diff_pct))
                elif diff_pct < 10:
                    results['good'].append((name, canonical_id, diff_pct))
                else:
                    results['poor'].append((name, canonical_id, diff_pct))
                    
        except Exception as e:
            results['no_data'].append((name, canonical_id))
    
    # 打印汇总报告
    print(f"\n{'='*80}")
    print("📊 验证结果汇总")
    print(f"{'='*80}")
    
    print(f"\n✅ 完美 (偏差 < 1%): {len(results['perfect'])} 只")
    for name, symbol, diff in results['perfect']:
        print(f"   {symbol:<30} {name:<20} {diff:.2f}%")
    
    print(f"\n✅ 优秀 (偏差 < 5%): {len(results['excellent'])} 只")
    for name, symbol, diff in results['excellent']:
        print(f"   {symbol:<30} {name:<20} {diff:.2f}%")
    
    print(f"\n⚠️ 良好 (偏差 < 10%): {len(results['good'])} 只")
    for name, symbol, diff in results['good']:
        print(f"   {symbol:<30} {name:<20} {diff:.2f}%")
    
    print(f"\n❌ 偏差较大 (偏差 >= 10%): {len(results['poor'])} 只")
    for name, symbol, diff in results['poor']:
        print(f"   {symbol:<30} {name:<20} {diff:.2f}%")
    
    print(f"\n⚪️ 无数据: {len(results['no_data'])} 只")
    for name, symbol in results['no_data']:
        print(f"   {symbol:<30} {name}")
    
    # 总体统计
    total_tested = len(results['perfect']) + len(results['excellent']) + len(results['good']) + len(results['poor'])
    if total_tested > 0:
        accuracy_rate = (len(results['perfect']) + len(results['excellent'])) / total_tested * 100
        print(f"\n{'='*80}")
        print(f"总体准确率 (偏差 < 5%): {accuracy_rate:.1f}%")
        print(f"{'='*80}")


if __name__ == "__main__":
    main()
