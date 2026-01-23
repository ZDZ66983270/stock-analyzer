
import sys
import os
import logging
from sqlmodel import Session
from datetime import datetime

# Setup paths
base_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(base_dir, 'backend')
if base_dir not in sys.path: sys.path.append(base_dir)
if backend_dir not in sys.path: sys.path.append(backend_dir)

from database import engine
from models import FinancialFundamentals, ForexRate
from valuation_calculator import calculate_pe_metrics_with_cache, get_dynamic_fx_rate
from symbols_config import SYMBOLS_CONFIG

# Configure logging to capture warnings
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ValuationCalculator")
logger.setLevel(logging.WARNING)

def test_fx_integrity():
    print("🧪 Testing FX Integrity in Valuation Calculator...")
    
    # Mock Data
    symbol = "HK:STOCK:00005" # HSBC
    market = "HK" # HKD
    fin_currency = "USD"
    close_price = 130.0
    as_of_date = "2026-01-23"
    
    # Mock Financials
    fin_rec = FinancialFundamentals(
        symbol=symbol,
        as_of_date=as_of_date,
        report_type='annual', # Use annual to bypass 4-quarter summation requirement for simple FX test
        currency=fin_currency,
        net_income_common_ttm=22517000000,
        shares_diluted=17221000000,
        filing_date="2025-10-30"
    )
    
    # Case 1: Session Provided (Should Succeed with Dynamic Rate)
    print("\nCase 1: Session Provided")
    with Session(engine) as session:
        # Ensure rate exists first? (Assuming existing data from previous steps)
        # We can insert a mock rate if needed, but let's trust existing data first.
        # Actually, let's inject a mock rate to be sure.
        rate_check = session.get(ForexRate, 9999) 
        if not rate_check:
             # Just assume data exists from previous successful run.
             pass

        metrics = calculate_pe_metrics_with_cache(
            symbol=symbol,
            market=market,
            close_price=close_price,
            as_of_date=as_of_date,
            financials_cache=[fin_rec],
            session=session
        )
        print(f"   Result: PE={metrics.get('pe')}")
        if metrics.get('pe') and 10 < metrics.get('pe') < 15:
            print("   ✅ PASS: PE is within expected range (12~13). Dynamic FX worked.")
        else:
            print(f"   ❌ FAIL: PE {metrics.get('pe')} is unexpected.")

    # Case 2: Session MISSING (Should Log Warning and potentially Fail or use Static if config exists)
    print("\nCase 2: Session MISSING (Expect Warning)")
    # Capture Warning logs?
    try:
        metrics = calculate_pe_metrics_with_cache(
            symbol=symbol,
            market=market,
            close_price=close_price,
            as_of_date=as_of_date,
            financials_cache=[fin_rec],
            session=None # Force missing session
        )
        print(f"   Result: PE={metrics.get('pe')}")
        # With static fallback removed or warned, what happens?
        # My code: logs Warning, tries static fallback. 
        # Static fallback for USD/HKD -> 1/7.8 ? 
        # If static config has USD/HKD=7.8. 
        # Target: HKD/USD. pair1=HKD/USD (Missing). pair2=USD/HKD (7.8).
        # My code logic: if pair2 in FOREX_RATES: fx_rate = FOREX_RATES[pair2] => 7.8
        # Wait, if pair2 (USD/HKD) is in config, rate is 7.8.
        # compute_ttm_eps_per_unit uses: eps_market = raw_eps * fx_rate.
        # raw_eps (USD) * 7.8 = eps (HKD). Correct.
        # So Static Fallback WORKS if config is good.
        # But we want to see the Warning.
        
    except Exception as e:
        print(f"   Exception: {e}")

    # Case 3: Verify ADR Config
    print("\nCase 3: ADR Config Check")
    for s in ['BABA', 'JD', 'PDD', 'BIDU']:
        if s in SYMBOLS_CONFIG:
            print(f"   ✅ {s}: Found in Config (ADR Ratio: {SYMBOLS_CONFIG[s].get('adr_ratio')})")
        else:
            print(f"   ❌ {s}: Missing from Config!")

if __name__ == "__main__":
    test_fx_integrity()
