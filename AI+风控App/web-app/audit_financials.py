
from sqlmodel import Session, select, func
from backend.database import engine
from backend.models import FinancialFundamentals, Watchlist

def audit_financials():
    with Session(engine) as session:
        # Get all stocks
        all_items = session.exec(select(Watchlist)).all()
        stocks = [x for x in all_items if ':STOCK:' in x.symbol]
        print(f"Auditing {len(stocks)} Stocks...\n")
        
        print(f"{'Symbol':<15} {'Name':<15} {'Total Reports':<10} {'With EPS':<10} {'With Div':<10} {'Latest Date':<12} {'Latest Type':<10} {'Latest Div':<10}")
        print("-" * 100)
        
        for stock in stocks:
            reports = session.exec(select(FinancialFundamentals).where(
                FinancialFundamentals.symbol == stock.symbol
            ).order_by(FinancialFundamentals.as_of_date.desc())).all()
            
            total = len(reports)
            w_eps = sum(1 for r in reports if r.eps is not None)
            w_div = sum(1 for r in reports if r.dividend_amount is not None and r.dividend_amount > 0)
            
            latest_date = "-"
            latest_type = "-"
            latest_div = "-"
            
            if reports:
                latest = reports[0]
                latest_date = str(latest.as_of_date)
                latest_type = latest.report_type or "?"
                latest_div = str(latest.dividend_amount) if latest.dividend_amount is not None else "None"
            
            print(f"{stock.symbol:<15} {stock.name[:15]:<15} {total:<10} {w_eps:<10} {w_div:<10} {latest_date:<12} {latest_type:<10} {latest_div:<10}")

if __name__ == "__main__":
    audit_financials()
