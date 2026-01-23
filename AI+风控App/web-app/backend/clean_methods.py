
    def to_akshare_us_symbol(self, s: str, for_minute: bool = False) -> str:
        """
        Convert potentially messy symbol to AkShare US format.
        Input: 'MSFT', '105.MSFT', 'MSFT.OQ'
        Output: '105.msft' (minute) or '105.MSFT' (daily)
        """
        s = s.upper() # Ensure upper first for comparisons
        # Clean suffix
        s_clean = s
        if s.endswith(".OQ") or s.endswith(".N") or s.endswith(".K"):
            s_clean = s.split('.')[0]
        
        s = s_clean
        prefix = "105." 
        
        # Already has prefix?
        if s.startswith("105.") or s.startswith("106."):
            if for_minute:
                return s.lower()
            return s.split(".")[1].upper()

        if s == "TSM": return "106.tsm" if for_minute else "TSM"
        
        if for_minute:
            return f"{prefix}{s.lower()}"
        else:
            return s

    def fetch_yahoo_indicators(self, symbol: str) -> dict:
        """
        Fetch supplementary indicators (PE, Dividend, etc.) and real-time quote from Yahoo Finance.
        Useful when AkShare lacks this specific metadata (like TTM Dividend Yield).
        """
        import yfinance as yf
        try:
            # Convert symbol to Yahoo format
            yf_symbol = symbol
            if symbol.endswith('.sh'):
                yf_symbol = symbol.replace('.sh', '.SS')
            elif symbol.endswith('.sz'):
                yf_symbol = symbol.replace('.sz', '.SZ')
            elif symbol.endswith('.hk'):
                try:
                    code = symbol.replace('.hk', '')
                    yf_symbol = f"{int(code):04d}.HK"
                except:
                    yf_symbol = symbol
            elif symbol.startswith('105.') or symbol.startswith('106.'):
                # US Stock
                yf_symbol = symbol.split('.')[-1].upper()
            else:
                 # Clean US suffix like .OQ, .N for Yahoo
                 if symbol.endswith(".OQ") or symbol.endswith(".N"):
                     yf_symbol = symbol.split('.')[0]
            
            self.logger.info(f"Fetching Yahoo indicators for {yf_symbol}...")
            ticker = yf.Ticker(yf_symbol)
            info = ticker.info
            
            if not info:
                return {}
            
            return {
                "pe": info.get("trailingPE") or info.get("forwardPE"),
                "dividend_yield": info.get("dividendYield"),
                "market_cap": info.get("marketCap"),
                "prev_close": info.get("previousClose"),
                "currentPrice": info.get("currentPrice"), 
                "longName": info.get("longName")
            }
        except Exception as e:
            self.logger.error(f"Yahoo Fetch Failed: {e}")
            return {}

    # --- Refactor: New Async-Compatible Methods ---

    def get_db_snapshot(self, symbol: str, market: str):
        """
        Rule 3 & 4: Pure DB Read + Freshness Check.
        Returns: (data_dict, needs_update_bool)
        """
        from market_schedule import MarketSchedule
        from datetime import datetime, timedelta
        from sqlmodel import Session, select
        from models import MarketData
        
        with Session(self.engine) as session:
            latest_db = session.exec(
                select(MarketData)
                .where(MarketData.symbol == symbol)
                .where(MarketData.period == '1d') 
                .order_by(MarketData.date.desc())
                .limit(1)
            ).first()
            
            if not latest_db:
                return None, True 
            
            # Check Stale
            last_time = latest_db.updated_at if latest_db.updated_at else datetime.now() - timedelta(days=1)
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
        self.fetch_latest_data(symbol, market, force_refresh=True)

# Standalone run
if __name__ == "__main__":
    pass
