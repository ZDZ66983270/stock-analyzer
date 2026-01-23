
import akshare as ak
import pandas as pd
import time

def get_cn_quarterly_data(symbol, periods=8):
    """
    Fetches quarterly data for a specific A-share symbol using ak.stock_yjbb_em.
    Since stock_yjbb_em returns all stocks for a date, this is slow but accurate.
    """
    # Generate list of quarter ends
    # Starting from a recent date, go back 'periods' quarters
    # For simulation, let's try 2024Q3, 2024Q2, 2024Q1, 2023Q4, 2023Q3 ...
    
    dates = [
        "20250930", "20250630", "20250331",
        "20241231", "20240930", "20240630", "20240331",
        "20231231", "20230930"
    ]
    
    results = {}
    
    print(f"📊 Fetching quarterly data for {symbol} (checking {len(dates)} periods)...")
    
    # Clean symbol for matching (e.g. 601919)
    simple_symbol = symbol.split(':')[-1] if ':' in symbol else symbol
    
    for d in dates:
        print(f"   Fetching {d}...", end="", flush=True)
        try:
            df = ak.stock_yjbb_em(date=d)
            if df is not None and not df.empty:
                # Filter for symbol
                # Columns usually: 股票代码, 股票简称, 净利润-净利润 ...
                row = df[df['股票代码'] == simple_symbol]
                if not row.empty:
                    net_profit = row.iloc[0]['净利润-净利润']
                    results[d] = net_profit
                    print(f" ✅ Profit: {net_profit/1e8:.2f} 亿")
                else:
                    print(f" ⚠️ Symbol not found")
            else:
                print(f" ⚠️ No data for date")
        except Exception as e:
            print(f" ❌ Error: {e}")
            
        # Rate limit slightly
        time.sleep(0.5)
        
    return pd.Series(results).sort_index()

def calculate_ttm(series_ytd, debug=True):
    """
    Calculates TTM Net Profit assuming the input series is Cumulative YTD (Year-to-Date).
    
    Formula:
    TTM = Current_YTD + (Prev_Year_Annual - Prev_Year_Same_Period_YTD)
    
    If Current is Q4 (Annual), TTM = Current_Annual
    """
    if series_ytd.empty:
        return None
        
    # Get latest available date
    latest_date_str = series_ytd.index[-1]
    latest_val = series_ytd.iloc[-1]
    
    year = int(latest_date_str[:4])
    month = int(latest_date_str[4:6])
    
    if debug:
        print(f"\n🧮 Calculating TTM for {latest_date_str}...")
    
    # Case 1: Latest is Q4 (Annual Report) -> TTM is the value itself
    if month == 12:
        if debug: print(f"   Latest is Q4 (Annual). TTM = {latest_val/1e8:.2f} 亿")
        return latest_val, latest_date_str
        
    # Case 2: Latest is Q1, Q2, Q3 -> Need Previous Year Data
    prev_year = year - 1
    prev_annual_date = f"{prev_year}1231"
    prev_same_period_date = f"{prev_year}{month:02d}{latest_date_str[6:]}"
    
    if prev_annual_date not in series_ytd or prev_same_period_date not in series_ytd:
        if debug: print(f"   ❌ Missing historical data for TTM calc. Need {prev_annual_date} and {prev_same_period_date}")
        return None, latest_date_str
        
    prev_annual_val = series_ytd[prev_annual_date]
    prev_same_period_val = series_ytd[prev_same_period_date]
    
    # TTM Formula
    ttm = latest_val + (prev_annual_val - prev_same_period_val)
    
    if debug:
        print(f"   Formula: Current_YTD ({latest_date_str}) + [Prev_Annual ({prev_annual_date}) - Prev_Same_YTD ({prev_same_period_date})]")
        print(f"   Val: {latest_val/1e8:.2f} + [{prev_annual_val/1e8:.2f} - {prev_same_period_val/1e8:.2f}]")
        print(f"   TTM = {ttm/1e8:.2f} 亿")
        
    return ttm, latest_date_str

def main():
    symbol = "601919" # COSCO Shipping
    name = "中远海控"
    
    # 1. Fetch History
    # We need enough history to find (Prev_Year_Annual) and (Prev_Year_Same_Period)
    # If latest is 2024-09-30, we need 2023-12-31 and 2023-09-30.
    
    history_ytd = get_cn_quarterly_data(symbol)
    
    print("\n📈 Historical YTD Net Profit (from ak.stock_yjbb_em):")
    print(history_ytd)
    
    if history_ytd.empty:
        print("❌ No data fetched.")
        return

    # 2. Calculate TTM
    ttm_val, ttm_date = calculate_ttm(history_ytd)
    
    # 3. Get Latest Annual for Comparison
    # Find the latest Q4 in the history
    q4_dates = [d for d in history_ytd.index if d.endswith('1231')]
    if not q4_dates:
        print("❌ No annual reports found in history.")
        return
        
    latest_annual_date = q4_dates[-1]
    latest_annual_val = history_ytd[latest_annual_date]
    
    # 4. Compare
    print("\n" + "="*50)
    print(f"⚖️  COMPARISON: {name} ({symbol})")
    print("="*50)
    print(f"Latest Annual ({latest_annual_date}): {latest_annual_val/1e8:.2f} 亿")
    
    if ttm_val is not None:
        print(f"Calculated TTM ({ttm_date}):   {ttm_val/1e8:.2f} 亿")
        diff = ttm_val - latest_annual_val
        diff_pct = (diff / latest_annual_val) * 100
        print("-" * 50)
        print(f"Difference: {diff/1e8:+.2f} 亿 ({diff_pct:+.2f}%)")
    else:
        print("⚠️ Could not calculate TTM due to missing data.")

if __name__ == "__main__":
    main()
