
import yfinance as yf
import pandas as pd

def test_tsla_metrics():
    symbol = "TSLA"
    print(f"📉 Fetching data for {symbol}...")
    
    ticker = yf.Ticker(symbol)
    
    # 1. Fetch Quarterly Data
    print("\nFetching Quarterly Financials...")
    q_fin = ticker.quarterly_financials
    if q_fin.empty:
        print("❌ Quarterly financials not found.")
        return

    # Extract Net Income
    # Row name usually 'Net Income' or 'Net Income Common Stockholders'
    try:
        if 'Net Income' in q_fin.index:
            q_net_income = q_fin.loc['Net Income']
        elif 'Net Income Common Stockholders' in q_fin.index:
            q_net_income = q_fin.loc['Net Income Common Stockholders']
        else:
            print("❌ Net Income row not found in quarterly data.")
            print("Available rows:", q_fin.index.tolist())
            return
            
        # Sort by date descending (just to be safe, though yfinance usually is)
        q_net_income = q_net_income.sort_index(ascending=False)
        
        # Take last 4 quarters
        last_4_quarters = q_net_income.head(4)
        
        print("\n📋 Recent 4 Quarters Net Income:")
        for date, val in last_4_quarters.items():
            print(f"  - {date.date()}: {val/1e9:.2f} B")
            
        if len(last_4_quarters) < 4:
            print("⚠️ Less than 4 quarters of data available.")
        
        ttm_net_income = last_4_quarters.sum()
        print(f"💡 Calculated TTM Net Income (Sum of last 4 quarters): {ttm_net_income/1e9:.2f} B")
        
        # Determine the date range for TTM
        ttm_end_date = last_4_quarters.index[0].date()
        ttm_start_date = last_4_quarters.index[-1].date()
        print(f"   (Period: {ttm_start_date} to {ttm_end_date})")

    except Exception as e:
        print(f"❌ Error processing quarterly data: {e}")
        return

    # 2. Fetch Annual Data
    print("\nFetching Annual Financials...")
    a_fin = ticker.financials
    if a_fin.empty:
        print("❌ Annual financials not found.")
        return
        
    try:
        if 'Net Income' in a_fin.index:
            a_net_income = a_fin.loc['Net Income']
        else:
            a_net_income = a_fin.loc['Net Income Common Stockholders']
            
        a_net_income = a_net_income.sort_index(ascending=False)
        latest_annual = a_net_income.head(1)
        latest_annual_val = latest_annual.iloc[0]
        latest_annual_date = latest_annual.index[0].date()
        
        print(f"📘 Latest Annual Report ({latest_annual_date}): {latest_annual_val/1e9:.2f} B")
        
    except Exception as e:
        print(f"❌ Error processing annual data: {e}")
        return

    # 3. Comparison
    print("\n" + "="*50)
    print("⚖️  COMPARISON")
    print("="*50)
    print(f"Latest Annual ({latest_annual_date}): {latest_annual_val/1e9:.2f} B")
    print(f"Calculated TTM ({ttm_end_date}):   {ttm_net_income/1e9:.2f} B")
    
    diff = ttm_net_income - latest_annual_val
    diff_pct = (diff / latest_annual_val) * 100
    
    print("-" * 50)
    print(f"Difference: {diff/1e9:+.2f} B ({diff_pct:+.2f}%)")
    
    if ttm_end_date > latest_annual_date:
         print(f"✅ TTM reflects more recent data (up to {ttm_end_date}) than Annual ({latest_annual_date}).")
    else:
         print(f"ℹ️ TTM and Annual cover similar periods.")

if __name__ == "__main__":
    test_tsla_metrics()
