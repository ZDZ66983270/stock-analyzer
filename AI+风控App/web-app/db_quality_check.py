#!/usr/bin/env python3
"""
Database Quality Assurance & PE Verification Script
---------------------------------------------------
1. Data Coverage Scan: Verifies history length and financial report counts.
2. PE Fill Check: Checks completeness of PE ratios in market data.
3. Yahoo Verification: Compares System PE vs Yahoo Real-time PE.
"""
import sys
import os
import time
import pandas as pd
import yfinance as yf
from datetime import datetime
from sqlmodel import Session, select, func

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from database import engine
from models import Watchlist, MarketDataDaily, FinancialFundamentals
from symbol_utils import get_yfinance_symbol

def check_data_coverage():
    print("\n🔍 1. Data Coverage Scan (History & Financials)")
    print("-" * 110)
    print(f"{'Symbol':<18} | {'Mkt':<4} | {'History Range':<22} | {'Days':<6} | {'Fin(Ann)':<8} | {'Fin(Qtr)':<8} | {'Status'}")
    print("-" * 110)

    with Session(engine) as session:
        all_assets = session.exec(select(Watchlist).order_by(Watchlist.market, Watchlist.symbol)).all()
        
        for asset in all_assets:
            # Market Data Stats
            mkt_stats = session.exec(
                select(
                    func.min(MarketDataDaily.timestamp),
                    func.max(MarketDataDaily.timestamp),
                    func.count(MarketDataDaily.id)
                ).where(MarketDataDaily.symbol == asset.symbol)
            ).first()
            
            min_date, max_date, mkt_count = mkt_stats
            
            # Date Parsing Fix for SQLite
            if isinstance(min_date, str):
                try: min_dt = datetime.strptime(min_date, '%Y-%m-%d %H:%M:%S')
                except: min_dt = datetime.strptime(min_date[:10], '%Y-%m-%d')
            else: min_dt = min_date
            
            if isinstance(max_date, str):
                try: max_dt = datetime.strptime(max_date, '%Y-%m-%d %H:%M:%S')
                except: max_dt = datetime.strptime(max_date[:10], '%Y-%m-%d')
            else: max_dt = max_date

            history_str = "No Data"
            duration_years = 0
            if min_dt and max_dt:
                history_str = f"{min_dt.strftime('%Y-%m')} -> {max_dt.strftime('%Y-%m')}"
                duration_years = (max_dt - min_dt).days / 365.25
            
            # Financial Stats
            ann_count = session.exec(
                select(func.count(FinancialFundamentals.id))
                .where(FinancialFundamentals.symbol == asset.symbol)
                .where(FinancialFundamentals.report_type == 'annual')
            ).one()
            
            qtr_count = session.exec(
                select(func.count(FinancialFundamentals.id))
                .where(FinancialFundamentals.symbol == asset.symbol)
                .where(FinancialFundamentals.report_type == 'quarterly')
            ).one()
            
            # Status Logic
            status = "✅"
            if mkt_count < 100: status = "⚠️ New/Empty"
            elif ':STOCK:' in asset.symbol and (ann_count < 3 or qtr_count < 4): status = "⚠️ Low Fin"
            
            print(f"{asset.symbol:<18} | {asset.market:<4} | {history_str:<22} | {mkt_count:<6} | {ann_count:<8} | {qtr_count:<8} | {status}")

def check_pe_integrity():
    print("\n🔍 2. PE Fill Check (Stocks Only)")
    print("-" * 80)
    print(f"{'Symbol':<18} | {'Mkt':<4} | {'Total Days':<10} | {'PE Covered':<10} | {'Missing %':<10} | {'Status'}")
    print("-" * 80)

    with Session(engine) as session:
        # Filter for STOCKS only
        all_assets = session.exec(select(Watchlist).order_by(Watchlist.market, Watchlist.symbol)).all()
        stocks = [a for a in all_assets if ':STOCK:' in a.symbol or (':ETF:' not in a.symbol and 'CRYPTO' not in a.symbol)]
        
        for stock in stocks:
            total = session.exec(select(func.count(MarketDataDaily.id)).where(MarketDataDaily.symbol == stock.symbol)).one()
            pe_count = session.exec(select(func.count(MarketDataDaily.id))
                                    .where(MarketDataDaily.symbol == stock.symbol)
                                    .where(MarketDataDaily.pe != None)).one()
            
            missing_pct = 100
            if total > 0:
                missing_pct = (total - pe_count) / total * 100
            
            status = "✅"
            if total == 0: status = "⚪️ No Data"
            elif missing_pct > 50: status = "❌ Critical"
            elif missing_pct > 10: status = "⚠️ Low Fill"
            
            print(f"{stock.symbol:<18} | {stock.market:<4} | {total:<10} | {pe_count:<10} | {missing_pct:>9.1f}% | {status}")

def verify_pe_vs_yahoo():
    print("\n⚖️  3. PE Verification (vs Yahoo Finance - Live)")
    print("-" * 80)
    print(f"{'Symbol':<18} | {'Mkt':<4} | {'Sys PE':<8} | {'YF PE':<8} | {'Diff %':<8} | {'Status'}")
    print("-" * 80)
    
    with Session(engine) as session:
        all_assets = session.exec(select(Watchlist).order_by(Watchlist.market, Watchlist.symbol)).all()
        stocks = [a for a in all_assets if ':STOCK:' in a.symbol or (':ETF:' not in a.symbol and 'CRYPTO' not in a.symbol)]
        
        for stock in stocks:
            # 1. System PE
            latest_daily = session.exec(select(MarketDataDaily).where(MarketDataDaily.symbol == stock.symbol).order_by(MarketDataDaily.timestamp.desc()).limit(1)).first()
            sys_pe = latest_daily.pe if latest_daily else None
            
            # 2. Yahoo PE (Live)
            # 从 Canonical ID 提取纯代码
            code = stock.symbol.split(':')[-1] if ':' in stock.symbol else stock.symbol
            yf_sym = get_yfinance_symbol(code, stock.market)
            yf_pe = None
            try:
                ticker = yf.Ticker(yf_sym)
                yf_pe = ticker.info.get('trailingPE')
            except: pass
            
            # 3. Compare
            diff_str = "N/A"
            status = "❓"
            
            if sys_pe and yf_pe:
                diff = abs(sys_pe - yf_pe) / yf_pe * 100
                diff_str = f"{diff:.1f}%"
                if diff < 10: status = "✅"
                elif diff < 20: status = "⚠️"
                else: status = "❌"
            elif sys_pe is None and yf_pe is None: status = "⚪️ Both Null"
            elif sys_pe is None: status = "🚫 Sys Null"
            elif yf_pe is None: status = "🚫 YF Null"
            
            sys_label = f"{sys_pe:.2f}" if sys_pe else "None"
            yf_label = f"{yf_pe:.2f}" if yf_pe else "None"
            
            print(f"{stock.symbol:<18} | {stock.market:<4} | {sys_label:<8} | {yf_label:<8} | {diff_str:<8} | {status}")

def main():
    check_data_coverage()
    check_pe_integrity()
    verify_pe_vs_yahoo()
    print("\n✅ Quality Assurance Complete.")

if __name__ == "__main__":
    main()
