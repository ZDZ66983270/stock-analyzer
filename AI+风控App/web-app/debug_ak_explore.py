
import akshare as ak

def explore_ak():
    print("🔍 Searching for 'lrb' (profit) or 'financial' functions...")
    
    candidates = []
    for attr in dir(ak):
        if 'stock' in attr and ('lrb' in attr or 'profit' in attr or 'financial' in attr):
            candidates.append(attr)
            
    # Filter for promising ones
    print(f"Found {len(candidates)} candidates. Top 20:")
    for c in sorted(candidates)[:20]:
        print(f" - {c}")
        
    # Check help for a fewer promising ones
    targets = ['stock_lrb_em', 'stock_profit_sheet_by_report_em', 'stock_financial_report_sina']
    for t in targets:
        if hasattr(ak, t):
            print(f"\n📘 Help for {t}:")
            try:
                # Print first few lines of docstring
                doc = getattr(ak, t).__doc__
                if doc:
                    print('\n'.join(doc.split('\n')[:10]))
                else:
                    print("No docstring.")
            except:
                print("Error reading doc string.")

if __name__ == "__main__":
    explore_ak()
