
import sys
import os
from sqlmodel import Session, select, func
import pandas as pd

# Add backend to path
sys.path.append('backend')
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.database import engine
from backend.models import Watchlist, MarketDataDaily, FinancialFundamentals
from backend.symbol_utils import parse_canonical_id

def inspect_us_pe():
    with Session(engine) as session:
        # Get all US stocks
        stocks = session.exec(select(Watchlist).where(Watchlist.market == "US")).all()
        # Filter for STOCK type (optional, based on naming convention checking)
        target_stocks = [s.symbol for s in stocks if ':STOCK:' in s.symbol]
        
        print(f"📊 Inspecting PE Data for {len(target_stocks)} US Stocks...")
        
        results = []
        
        for symbol in target_stocks:
            # 1. Get Latest Market Data
            stmt_mkt = select(MarketDataDaily).where(MarketDataDaily.symbol == symbol).order_by(MarketDataDaily.timestamp.desc()).limit(1)
            mkt = session.exec(stmt_mkt).first()
            
            if not mkt:
                results.append({"Symbol": symbol, "Status": "No Market Data"})
                continue
                
            # 2. Get Recent Financials (Last 4)
            stmt_fin = select(FinancialFundamentals).where(FinancialFundamentals.symbol == symbol).order_by(FinancialFundamentals.as_of_date.desc()).limit(4)
            fins = session.exec(stmt_fin).all()
            
            fin_str = ""
            ttm_sum = 0
            for f in fins:
                fin_str += f"[{f.as_of_date} ({f.report_type}): {f.eps}] "
                if f.eps:
                    ttm_sum += f.eps
            
            pe_calc = float('inf')
            if mkt.close and ttm_sum > 0:
                pe_calc = mkt.close / ttm_sum
            
            results.append({
                "Symbol": symbol,
                "Date": str(mkt.timestamp)[:10] if mkt else "N/A",  # Added Date
                "Close": mkt.close,
                "PE_DB": mkt.pe_ttm,
                "EPS_DB": mkt.eps,
                "Recent_EPS_Recs": fin_str,
                "Calc_TTM_EPS": round(ttm_sum, 4),
                "Calc_PE_TTM": round(pe_calc, 2)
            })
            
    # Display
    df = pd.DataFrame(results)
    if not df.empty:
        # Reorder columns
        cols = ["Symbol", "Date", "Close", "PE_DB", "EPS_DB", "Calc_PE_TTM", "Calc_TTM_EPS", "Recent_EPS_Recs"] # Added Date
        # Filter existing columns
        cols = [c for c in cols if c in df.columns]
        
        print("\n" + "="*120)
        print(" 🇺🇸 US Stock PE Inspection")
        print("="*120)
        # Use simple printing for readability
        for _, row in df.iterrows():
            print(f"Symbol: {row['Symbol']} ({row['Date']})") # Added Date
            print(f"  Close: {row['Close']} | PE (DB): {row['PE_DB']} | EPS (DB): {row['EPS_DB']}")
            print(f"  Calculated (Rolling 4Q): TTM EPS={row['Calc_TTM_EPS']} -> PE={row['Calc_PE_TTM']}")
            print(f"  Financials: {row['Recent_EPS_Recs']}")
            print("-" * 60)
    else:
        print("No data found.")

if __name__ == "__main__":
    inspect_us_pe()
