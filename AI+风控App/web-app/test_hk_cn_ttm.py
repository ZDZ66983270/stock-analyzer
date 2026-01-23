
import yfinance as yf
import pandas as pd

def analyze_stock(symbol, name):
    print("\n" + "#"*60)
    print(f"📊 Analyzing {name} ({symbol})")
    print("#"*60)
    
    ticker = yf.Ticker(symbol)
    
    # --- 1. Quarterly Data (for TTM) ---
    print(f"📉 Fetching Quarterly Financials for {symbol}...")
    try:
        q_fin = ticker.quarterly_financials
        if q_fin.empty:
            print(f"❌ Quarterly financials not found for {symbol}")
            return
            
        # Find Net Income row
        q_net_income = None
        for key in ['Net Income', 'Net Income Common Stockholders', 'Net Income From Continuing And Discontinued Operation']:
            if key in q_fin.index:
                q_net_income = q_fin.loc[key]
                print(f"   (Using field: '{key}')")
                break
        
        if q_net_income is None:
            print(f"❌ Net Income row not found. Available: {q_fin.index.tolist()[:5]}...")
            return

        # Sort and take last 4
        q_net_income = q_net_income.sort_index(ascending=False)
        last_4_quarters = q_net_income.head(4)
        
        print("\n📋 Recent 4 Quarters Net Income:")
        for date, val in last_4_quarters.items():
            print(f"  - {date.date()}: {val/1e9:.2f} B")
            
        if len(last_4_quarters) < 4:
            print("⚠️ Less than 4 quarters of data available. TTM may be inaccurate.")
            
        ttm_net_income = last_4_quarters.sum()
        ttm_end_date = last_4_quarters.index[0].date()
        print(f"💡 Calculated TTM Net Income: {ttm_net_income/1e9:.2f} B")

    except Exception as e:
        print(f"❌ Error processing quarterly data: {e}")
        return

    # --- 2. Annual Data ---
    print(f"\n📘 Fetching Annual Financials for {symbol}...")
    try:
        a_fin = ticker.financials
        if a_fin.empty:
            print(f"❌ Annual financials not found for {symbol}")
            return

        a_net_income = None
        for key in ['Net Income', 'Net Income Common Stockholders', 'Net Income From Continuing And Discontinued Operation']:
            if key in a_fin.index:
                a_net_income = a_fin.loc[key]
                break
        
        if a_net_income is None:
            print("❌ Net Income row not found in annual data.")
            return

        a_net_income = a_net_income.sort_index(ascending=False)
        latest_annual = a_net_income.head(1)
        latest_annual_val = latest_annual.iloc[0]
        latest_annual_date = latest_annual.index[0].date()
        
        print(f"   Latest Annual Report ({latest_annual_date}): {latest_annual_val/1e9:.2f} B")

    except Exception as e:
        print(f"❌ Error processing annual data: {e}")
        return

    # --- 3. Comparison ---
    print("\n⚖️  COMPARISON")
    print(f"Latest Annual ({latest_annual_date}): {latest_annual_val/1e9:.2f} B")
    print(f"Calculated TTM ({ttm_end_date}):   {ttm_net_income/1e9:.2f} B")
    
    diff = ttm_net_income - latest_annual_val
    diff_pct = (diff / latest_annual_val) * 100 if latest_annual_val != 0 else 0
    
    print("-" * 40)
    print(f"Difference: {diff/1e9:+.2f} B ({diff_pct:+.2f}%)")


def main():
    targets = [
        ("9988.HK", "Alibaba (港股)"),
        ("601919.SS", "COSCO Shipping (A股)")
    ]
    
    for symbol, name in targets:
        analyze_stock(symbol, name)

if __name__ == "__main__":
    main()
