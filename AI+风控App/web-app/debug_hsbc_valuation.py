
import sys
import os
from sqlmodel import Session, select
from datetime import datetime

# Ensure backend can be imported
base_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(base_dir, 'backend')
if base_dir not in sys.path: sys.path.append(base_dir)
if backend_dir not in sys.path: sys.path.append(backend_dir)

from database import engine
from models import FinancialFundamentals, MarketDataDaily, ForexRate
from valuation_calculator import get_shares_outstanding, get_dynamic_fx_rate, normalize_code, SYMBOLS_CONFIG

def explain_hsbc():
    symbol = "HK:STOCK:00005"
    market = "HK"
    
    print(f"🔍 Starting Valuation Breakdown for {symbol}...\n")
    
    with Session(engine) as session:
        # 1. Fetch Latest Price
        stmt_price = select(MarketDataDaily).where(MarketDataDaily.symbol == symbol).order_by(MarketDataDaily.timestamp.desc()).limit(1)
        price_rec = session.exec(stmt_price).first()
        if not price_rec:
            print("❌ No Market Data found.")
            return
            
        close_price = price_rec.close
        as_of_date = price_rec.timestamp[:10]
        print(f"1. Market Data (Snapshot at {price_rec.timestamp})")
        print(f"   - Close Price: {close_price} HKD")
        print(f"   - As of Date:  {as_of_date}")
        print("-" * 40)

        # 2. Fetch Financials
        stmt_fin = select(FinancialFundamentals).where(
            FinancialFundamentals.symbol == symbol
        ).order_by(FinancialFundamentals.as_of_date.desc()).limit(8)
        
        financials = session.exec(stmt_fin).all()
        print(f"2. Financial Data (Last {len(financials)} records)")
        
        valid_financials = [f for f in financials if f.as_of_date <= as_of_date]
        latest_fin = valid_financials[0]
        
        print(f"   - Latest Report Date: {latest_fin.as_of_date} ({latest_fin.report_type})")
        print(f"   - Reporting Currency: {latest_fin.currency}")
        
        # 3. Calculate TTM Net Income
        print("\n3. Net Income (TTM) Calculation")
        ttm_income = None
        
        if latest_fin.report_type == 'quarterly':
            qs = [f for f in valid_financials if f.report_type == 'quarterly']
            qs_top4 = qs[:4]
            print(f"   - Strategy: Summing last 4 Quarterly 'Net Income Common'")
            
            running_sum = 0
            for i, q in enumerate(qs_top4):
                val = q.net_income_common_ttm or 0
                print(f"     Q{i+1}: {q.as_of_date} | Income: {val:,.2f} {q.currency}")
                running_sum += val
                
            ttm_income = running_sum
            print(f"   = Total Net Income (TTM): {ttm_income:,.2f} {latest_fin.currency}")
            
        else:
            ttm_income = latest_fin.net_income_common_ttm or latest_fin.net_income_ttm
            print(f"   - Strategy: Using Annual Value directly: {ttm_income:,.2f}")

        # 4. Shares & FX
        print("\n4. Denominator & FX")
        
        # Shares
        shares = latest_fin.shares_diluted
        source = "Financials Report"
        if not shares:
            shares = get_shares_outstanding(symbol, market)
            source = "External/Fallback (MarketCap Method)"
            
        print(f"   - Shares Outstanding: {shares:,.0f} ({source})")
        
        # FX
        market_currency = "HKD" # HK stock
        fin_currency = latest_fin.currency # USD likely
        fx_rate = get_dynamic_fx_rate(session, fin_currency, market_currency, as_of_date)
        print(f"   - FX Rate ({fin_currency} -> {market_currency}): {fx_rate:.4f}")
        
        # 5. Final Calculation
        print("\n5. Final EPS & PE Calculation")
        
        # EPS (Raw)
        raw_eps = ttm_income / shares
        print(f"   - Raw EPS ({fin_currency}): {ttm_income:,.0f} / {shares:,.0f} = {raw_eps:.4f}")
        
        # EPS (Converted)
        eps_hkd = raw_eps * fx_rate
        print(f"   - EPS ({market_currency}): {raw_eps:.4f} * {fx_rate:.4f} = {eps_hkd:.4f}")
        
        # PE
        pe = close_price / eps_hkd
        print(f"   - PE Ratio: {close_price:.2f} / {eps_hkd:.4f} = {pe:.2f}")

if __name__ == "__main__":
    explain_hsbc()
