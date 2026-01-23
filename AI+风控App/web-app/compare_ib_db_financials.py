import sys
from ib_insync import *
import xml.etree.ElementTree as ET
from sqlmodel import Session, select
from backend.database import engine
from backend.models import FinancialFundamentals
import pandas as pd
from datetime import datetime

def compare_financials():
    symbol = "TSLA"
    canonical_id = "US:STOCK:TSLA"
    
    print(f"⚖️  Starting Comparison for {symbol} (Last 3 Years)...")

    # 1. Fetch from DB (Yahoo/FMP)
    print("\n📦 Fetching from Database...")
    db_data = []
    with Session(engine) as session:
        statement = select(FinancialFundamentals).where(
            FinancialFundamentals.symbol == canonical_id
        ).order_by(FinancialFundamentals.as_of_date.desc())
        results = session.exec(statement).all()
        
        for r in results:
            if r.report_type == 'quarterly': # Focus on quarterly for EPS accuracy
                # EPS is often net_income / shares, or hidden? 
                # Our model doesn't explicitly store 'eps'. We might need to look at net_income.
                # Use revenue_ttm for revenue comparison.
                # Wait, our model has `net_income_ttm` and `revenue_ttm`.
                # For direct quarterly comparison, we need raw quarterly numbers, but our DB stores TTM usually?
                # Actually `fetch_financials.py` stores whatever Yahoo gives.
                # Yahoo `quarterly_financials` column IS quarterly period data usually. 
                # Let's check `revenue_ttm` naming - it might be a misnomer in our model if it stores quarterly point data with report_type='quarterly'.
                # Let's assume for 'quarterly' type, it's the point data.
                db_data.append({
                    'source': 'DB (Yahoo)',
                    'date': str(r.as_of_date),
                    'revenue': r.revenue_ttm,  # Assuming this holds the quarterly value
                    'net_income': r.net_income_ttm
                })
    
    df_db = pd.DataFrame(db_data)
    if not df_db.empty:
        print(df_db.head())
    else:
        print("⚠️ No DB data found.")

    # 2. Fetch from IB
    print("\n🌊 Fetching from IB (ReportsFinSummary)...")
    ib_data = []
    
    ib = IB()
    try:
        ib.connect('127.0.0.1', 7497, clientId=7)
    except Exception as e:
        print(f"❌ IB Connection failed: {e}")
        return

    stock = Stock(symbol, 'SMART', 'USD')
    xml_data = ib.reqFundamentalData(stock, 'ReportsFinSummary')
    ib.disconnect()

    if xml_data:
        try:
            root = ET.fromstring(xml_data)
            # Parse EPS
            # Path: FinancialSummary -> EPSs -> EPS -> (period)
            # EPS tag usually has 'period' attribute
            # Let's inspect XML structure dynamically or rely on observation:
            # Usually: <EPS period="2023-09-30">0.53</EPS>
            
            # Let's look for Income Statement data
            # ReportsFinSummary usually has <TotalRevenues> and <EPS> with period attributes.
            
            def parse_series(tag_name, label):
                series = []
                # Namespace handling might be needed if XML has xmlns
                # Try finding all tags with name
                for node in root.iter(tag_name):
                     # Usually the parent node is the series container, children are periods?
                     # No, widely varies. Let's try to find children with period.
                     pass
                
                # Direct approach based on common IB XML
                # <TotalRevenues> <TotalRevenue period="2024-12-31">...</TotalRevenue> ... </TotalRevenues>
                # Using xpath .//TotalRevenue
                
                nodes = root.findall(f".//{tag_name}") 
                for node in nodes:
                    date = node.get('EndDate', '') or node.get('period', '')
                    val = node.text
                    if date and val:
                        try:
                            # IB Revenue often in Millions? Or standard?
                            # Usually standard units or indicated by 'mapItem'
                            v_float = float(val)
                            series.append({'date': date, label: v_float})
                        except: pass
                return series

            # Re-inspect 'ReportsFinSummary' from previous output?
            # User output showed: Children: ['EPSs', 'TotalRevenues']
            # So we look inside EPSs -> likely <EPS> children
            # Inside TotalRevenues -> likely <TotalRevenue> children
            
            # 1. Revenue
            rev_nodes = root.findall("./TotalRevenues/TotalRevenue")
            for node in rev_nodes:
                 date = node.get('EndDate')
                 val = node.text
                 if date and val:
                     ib_data.append({'source': 'IB', 'date': date, 'revenue': float(val), 'type': 'revenue'})

            # 2. EPS
            eps_nodes = root.findall("./EPSs/EPS")
            for node in eps_nodes:
                 date = node.get('EndDate')
                 val = node.text
                 if date and val:
                     # Check if we already have this date in ib_data, or append?
                     # Let's consolidate later.
                     ib_data.append({'source': 'IB', 'date': date, 'eps': float(val), 'type': 'eps'})
                     
        except Exception as e:
            print(f"❌ XML Parsing error: {e}")
            print(xml_data[:500])
    
    # 3. Align and Compare
    print("\n" + "="*60)
    print(f"📊 {symbol} Comparison (Last 3 Years)")
    print("="*60)
    print(f"{'Date':<12} | {'DB Revenue':<15} | {'IB Revenue':<15} | {'Diff %':<8} | {'DB NetInc/Share?':<16} | {'IB EPS':<10}")
    print("-" * 90)
    
    # Process IB data into dict by date
    ib_map = {}
    for item in ib_data:
        d = item['date']
        if d not in ib_map: ib_map[d] = {}
        if 'revenue' in item: ib_map[d]['revenue'] = item['revenue']
        if 'eps' in item: ib_map[d]['eps'] = item['eps']
        
    dates = sorted(list(set([d['date'] for d in db_data] + list(ib_map.keys()))), reverse=True)
    
    current_year = datetime.now().year
    
    for d in dates:
        # Filter last 3 years
        try:
            dy = int(d.split('-')[0])
            if dy < (current_year - 3): continue
        except: continue
        
        # Get DB values
        db_rev = next((x['revenue'] for x in db_data if x['date'] == d), None)
        db_ni = next((x['net_income'] for x in db_data if x['date'] == d), None)
        
        # Get IB values
        ib_rev = ib_map.get(d, {}).get('revenue')
        ib_eps = ib_map.get(d, {}).get('eps')
        
        # Comparison logic
        # Revenue: DB is usually raw. IB is usually Millions?
        # Let's guess scaling. DB from Yahoo is usually raw bytes.
        # IB might be Millions.
        
        rev_str_db = f"{db_rev/1e9:.2f}B" if db_rev else "-"
        rev_str_ib = f"{ib_rev:.2f}M?" if ib_rev else "-" # IB unit generic?
        
        # Calculate diff if both exist
        diff_str = "-"
        if db_rev and ib_rev:
             # Try matching scaling
             # If IB is million, multiply by 1e6
             ib_rev_scaled = ib_rev * 1e6 
             pct = abs(db_rev - ib_rev_scaled) / db_rev * 100
             diff_str = f"{pct:.1f}%"
             
             if pct > 50: # Maybe IB is in actual units?
                  pct2 = abs(db_rev - ib_rev) / db_rev * 100
                  if pct2 < 1: 
                      diff_str = f"{pct2:.1f}%"
                      rev_str_ib = f"{ib_rev/1e9:.2f}B" # It was raw

        # EPS vs Net Income
        # DB doesn't have EPS stored explicitly in FinancialFundamentals (only Net Income TTM).
        # We can loosely check if Net Income direction matches EPS.
        ni_str = f"{db_ni/1e9:.2f}B" if db_ni else "-"
        eps_str = f"{ib_eps:.2f}" if ib_eps else "-"
        
        print(f"{d:<12} | {rev_str_db:<15} | {rev_str_ib:<15} | {diff_str:<8} | {ni_str:<16} | {eps_str:<10}")

if __name__ == "__main__":
    sys.path.insert(0, ".")
    compare_financials()
