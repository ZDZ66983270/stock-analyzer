#!/usr/bin/env python3
"""
导出财务数据和行情数据到 CSV
"""
import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from database import engine
from sqlmodel import Session, select
from models import FinancialFundamentals, MarketDataDaily
import pandas as pd
from datetime import datetime

# 确保输出目录存在
os.makedirs('outports', exist_ok=True)

print("🚀 开始导出数据...")
print("=" * 80)

# 1. 导出财务数据
print("\n📊 导出 FinancialFundamentals 表...")
with Session(engine) as session:
    stmt = select(FinancialFundamentals).order_by(
        FinancialFundamentals.symbol,
        FinancialFundamentals.as_of_date.desc()
    )
    financials = session.exec(stmt).all()
    
    if financials:
        # 转换为字典列表
        data = []
        for record in financials:
            data.append({
                'symbol': record.symbol,
                'as_of_date': record.as_of_date,
                'revenue_ttm': record.revenue_ttm,
                'net_income_ttm': record.net_income_ttm,
                'operating_cashflow_ttm': record.operating_cashflow_ttm,
                'free_cashflow_ttm': record.free_cashflow_ttm,
                'total_assets': record.total_assets,
                'total_liabilities': record.total_liabilities,
                'total_debt': record.total_debt,
                'cash_and_equivalents': record.cash_and_equivalents,
                'net_debt': record.net_debt,
                'debt_to_equity': record.debt_to_equity,
                'interest_coverage': record.interest_coverage,
                'current_ratio': record.current_ratio,
                'dividend_yield': record.dividend_yield,
                'payout_ratio': record.payout_ratio,
                'buyback_ratio': record.buyback_ratio,
                'data_source': record.data_source,
                'currency': record.currency,
                'created_at': record.created_at
            })
        
        df = pd.DataFrame(data)
        output_path = 'outports/financial_fundamentals.csv'
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        print(f"   ✅ 导出成功: {output_path}")
        print(f"   记录数: {len(df)}")
        print(f"   标的数: {df['symbol'].nunique()}")
        print(f"   列数: {len(df.columns)}")
    else:
        print("   ⚠️  表为空")

# 2. 导出行情数据（仅包含有EPS的记录）
print("\n📈 导出 MarketDataDaily 表（含EPS）...")
with Session(engine) as session:
    # 只导出有EPS的记录
    stmt = select(MarketDataDaily).where(
        MarketDataDaily.eps.isnot(None)
    ).order_by(
        MarketDataDaily.symbol,
        MarketDataDaily.timestamp.desc()
    )
    market_data = session.exec(stmt).all()
    
    if market_data:
        # 转换为字典列表
        data = []
        for record in market_data:
            data.append({
                'symbol': record.symbol,
                'market': record.market,
                'timestamp': record.timestamp,
                'open': record.open,
                'high': record.high,
                'low': record.low,
                'close': record.close,
                'volume': record.volume,
                'turnover': record.turnover,
                'change': record.change,
                'pct_change': record.pct_change,
                'prev_close': record.prev_close,
                'pe': record.pe,
                'pb': record.pb,
                'ps': record.ps,
                'dividend_yield': record.dividend_yield,
                'eps': record.eps,
                'market_cap': record.market_cap,
                'updated_at': record.updated_at
            })
        
        df = pd.DataFrame(data)
        output_path = 'outports/market_data_daily_with_eps.csv'
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        print(f"   ✅ 导出成功: {output_path}")
        print(f"   记录数: {len(df)}")
        print(f"   标的数: {df['symbol'].nunique()}")
        print(f"   列数: {len(df.columns)}")
    else:
        print("   ⚠️  无EPS数据")

print("\n" + "=" * 80)
print("🏁 导出完成!")
print("=" * 80)
