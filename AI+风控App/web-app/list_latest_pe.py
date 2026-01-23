#!/usr/bin/env python3
import sys
from sqlalchemy import select, func, desc
from sqlmodel import Session
from backend.database import engine
from backend.models import MarketDataDaily, Watchlist

def main():
    with Session(engine) as session:
        # Get list of stock symbols (exclude indices, ETFs, etc.)
        stock_symbols = session.exec(
            select(Watchlist.symbol).where(
                Watchlist.market.in_(["US", "HK", "CN"]),
                ~Watchlist.symbol.contains(":INDEX:"),
                ~Watchlist.symbol.contains(":ETF:"),
                ~Watchlist.symbol.contains(":CRYPTO:"),
                ~Watchlist.symbol.contains(":TRUST:"),
                ~Watchlist.symbol.contains(":FUND:")
            )
        ).scalars().all()
        print("symbol,latest_date,pe,pe_ttm")
        for sym in stock_symbols:
            # latest record per symbol
            # Get latest timestamp for this symbol
            latest_ts = session.exec(
                select(func.max(MarketDataDaily.timestamp)).where(MarketDataDaily.symbol == sym)
            ).scalar_one_or_none()
            if not latest_ts:
                continue
            # Fetch PE and PE_TTM for the latest record
            row = session.exec(
                select(MarketDataDaily.pe, MarketDataDaily.pe_ttm).where(
                    MarketDataDaily.symbol == sym,
                    MarketDataDaily.timestamp == latest_ts
                )
            ).first()
            pe, pe_ttm = row if row else (None, None)
            print(f"{sym},{latest_ts},{pe if pe is not None else ''},{pe_ttm if pe_ttm is not None else ''}")

if __name__ == "__main__":
    main()
