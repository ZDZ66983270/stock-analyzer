
    # --- Refactor: New Async-Compatible Methods ---

    def get_db_snapshot(self, symbol: str, market: str):
        """
        Rule 3 & 4: Pure DB Read + Freshness Check.
        Returns: (data_dict, needs_update_bool)
        """
        from market_schedule import MarketSchedule
        from datetime import datetime
        
        # We need a session. Assuming engine exists.
        from sqlmodel import Session, select
        from models import MarketData
        
        with Session(self.engine) as session:
            latest_db = session.exec(
                select(MarketData)
                .where(MarketData.symbol == symbol)
                .where(MarketData.period == '1d') # Standardize on 1d for snapshot
                .order_by(MarketData.date.desc())
                .limit(1)
            ).first()
            
            if not latest_db:
                return None, True # No data -> Needs update
            
            # Check Stale
            last_time = latest_db.updated_at if latest_db.updated_at else datetime.now()
            
            is_stale = MarketSchedule.is_stale(last_time, market, ttl_seconds=60)
            
            # Convert to dict
            data = {
                "symbol": latest_db.symbol,
                "price": latest_db.close,
                "change": latest_db.change,
                "pct_change": latest_db.pct_change,
                "volume": latest_db.volume,
                "market": market,
                "date": latest_db.date,
                "pe": latest_db.pe,
                "dividend_yield": latest_db.dividend_yield,
                "open": latest_db.open,
                "high": latest_db.high,
                "low": latest_db.low,
                "prev_close": latest_db.prev_close
            }
            return data, is_stale

    def sync_market_data(self, symbol: str, market: str):
        """
        Rule 4: API Fetch -> Write DB.
        Should be called by Background Task.
        """
        # Call the existing logic (which I updated to write-through)
        # But force_refresh=True to ensure we hit API
        self.fetch_latest_data(symbol, market, force_refresh=True)
