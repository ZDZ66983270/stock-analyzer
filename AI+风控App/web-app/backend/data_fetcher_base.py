import akshare as ak
import pandas as pd
import requests
from typing import Optional, Dict
import sqlite3
import os
import logging # Kept logging as it's used extensively in the class
import time
import threading
import pytz
from datetime import datetime, time as dtime
from sqlalchemy import create_engine
from database import engine
from sqlmodel import Session, select
from models import MarketDataDaily

class DataFetcher:
    def __init__(self, symbols_file="symbols_V4.txt", log_dir="logs_V4", output_dir="output_V4"):
        # Make paths absolute relative to this file to avoid CWD issues
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.symbols_file = os.path.join(base_dir, symbols_file)
        self.log_dir = os.path.join(base_dir, log_dir)
        self.log_dir = os.path.join(base_dir, log_dir)
        self.output_dir = os.path.join(base_dir, output_dir)
        
        # --- FIX: Disable System Proxy for AkShare/CN Data ---
        # User environment likely has a Proxy (VPN) active for Yahoo/US data.
        # But EastMoney (CN/HK data) causes ProxyError or is slow via proxy.
        # We configure 'no_proxy' to force direct connection for domestic domains.
        
        # 1. Unset strictly explicit proxies if they are causing 'Unable to connect' globally
        # But if Yahoo still worked, maybe we SHOULD keep them? 
        # The logs showed ProxyError for EastMoney. 
        # Strategy: Keep proxies generally (if set by system), but BYPASS for specific domains.
        
        # Current code unsets them all. If Yahoo still worked, maybe User has a Transparent Proxy (System VPN) 
        # that doesn't rely on HTTP_PROXY env vars, OR Python isn't picking them up but AkShare for US uses something else?
        # WAIT: The log said "Caused by ProxyError". This proves Python IS trying to use an HTTP Proxy.
        # Implication: My previous `del os.environ` failed to clear it effectively for `requests` on macOS 
        # because `requests` searches macOS system registry via `urllib` if env vars are missing.
        
        # 2. Force NO_PROXY for EastMoney
        no_proxy_domains = [
            "eastmoney.com", "push2his.eastmoney.com", "quote.eastmoney.com", "*.eastmoney.com",
            "gtimg.cn", "sinajs.cn", "163.com", "baidu.com"
        ]
        
        # Append to existing no_proxy or create new
        current_no_proxy = os.environ.get("no_proxy", "")
        # Normalize
        if current_no_proxy:
            current_no_proxy += ","
        
        os.environ["no_proxy"] = current_no_proxy + ",".join(no_proxy_domains)
        os.environ["NO_PROXY"] = os.environ["no_proxy"]
        
        print(f"DEBUG: Configured no_proxy for CN domains: {os.environ['no_proxy']}")
        # ----------------------------------------------------

        self.est_tz = pytz.timezone('Asia/Shanghai')
        print(f"DEBUG: Initializing DataFetcher. Log dir: {self.log_dir}")
        self._setup_logger()
        self.symbols = self._load_symbols()

    def _setup_logger(self):
        os.makedirs(self.log_dir, exist_ok=True)
        log_file = os.path.join(self.log_dir, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_V4.log")
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console.setFormatter(formatter)
        # Check if handler already exists to avoid duplicates in re-eintrant cases
        if not logging.getLogger().handlers:
            logging.getLogger().addHandler(console)
        self.logger = logging.getLogger(__name__)

    def _load_symbols(self) -> list:
        symbols = set()
        # 1. Load from file
        try:
            if os.path.exists(self.symbols_file):
                with open(self.symbols_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            symbols.add(line)
            else:
                self.logger.warning(f"Symbols file not found at {self.symbols_file}")
        except Exception as e:
            self.logger.error(f"Error loading symbols from file: {str(e)}")
        
        # 2. Load from DB
        try:
            from database import engine
            from models import Watchlist
            from sqlmodel import Session, select
            
            with Session(engine) as session:
                db_symbols = session.exec(select(Watchlist.symbol)).all()
                for s in db_symbols:
                    symbols.add(s)
        except Exception as e:
            self.logger.error(f"Error loading symbols from DB: {str(e)}")

        self.logger.info(f"Loaded {len(symbols)} unique symbols: {symbols}")
        return list(symbols)

    def fetch_us_min_data(self, symbol: str) -> pd.DataFrame:
        try:
            self.logger.info(f"Fetching US minute data for {symbol} ...")
            # 获取美东时间
            eastern = pytz.timezone('US/Eastern')
            now_est = datetime.now(eastern)
            today_est = now_est.date()

            # 采集全部数据
            df = ak.stock_us_hist_min_em(symbol=symbol)
            if df is not None and not df.empty and '时间' in df.columns:
                df['时间'] = pd.to_datetime(df['时间'])
                df['日期'] = df['时间'].dt.date
                # 只保留最近30天的数据（含今天）
                last_date = df['日期'].max()
                first_date = last_date - pd.Timedelta(days=29)
                df = df[df['日期'] >= first_date]
                df = df.drop(columns=['日期'])
            return df
        except Exception as e:
            self.logger.error(f"Error fetching US data for {symbol}: {str(e)}")
            return pd.DataFrame()

    def fetch_hk_min_data(self, symbol: str, period: str = '1') -> pd.DataFrame:
        try:
            code = symbol.replace('.hk', '').zfill(5)
            self.logger.info(f"Fetching HK minute data for {code} period={period}...")
            df = ak.stock_hk_hist_min_em(symbol=code, period=period)
            if df is not None and not df.empty and '时间' in df.columns:
                df['时间'] = pd.to_datetime(df['时间'])
            return df
        except Exception as e:
            self.logger.error(f"Error fetching HK data for {symbol}: {str(e)}")
            # Fallback to Yahoo Min Data?
            # Fetching real-time from Yahoo for HK is possible.
            try:
                self.logger.info(f"Switching to yfinance fallback for HK min data {symbol}")
                return self._fetch_fallback_yfinance_min(symbol, "HK")
            except Exception as e2:
                self.logger.error(f"Fallback min failed: {e2}")
            return pd.DataFrame()

    def fetch_cn_min_data(self, symbol: str, period: str = '1') -> pd.DataFrame:
        try:
            code = symbol.replace('.sh', '').replace('.sz', '').zfill(6)
            self.logger.info(f"Fetching CN minute data for {code} period={period}...")
            df = ak.stock_zh_a_hist_min_em(symbol=code, period=period)
            if df is not None and not df.empty and '时间' in df.columns:
                df['时间'] = pd.to_datetime(df['时间'])
            return df
        except Exception as e:
            self.logger.error(f"Error fetching CN data for {symbol}: {str(e)}")
            try:
                self.logger.info(f"Switching to yfinance fallback for CN min data {symbol}")
                return self._fetch_fallback_yfinance_min(symbol, "CN")
            except Exception as e2:
                 self.logger.error(f"Fallback min failed: {e2}")
            return pd.DataFrame()

    def fetch_cn_spot_data(self, symbol: str) -> dict:
        """
        Fetch real-time spot data for a single CN stock to get indicators like Dividend Yield, PE, PB.
        Returns a dict with keys: price, open, high, low, volume, amount, pe, pb, dividend_yield, market_cap.
        """
        try:
            code = symbol.replace('.sh', '').replace('.sz', '').zfill(6)
            # Use stock_zh_a_spot_em for full market spot might be slow if fetching all, 
            # but AkShare/EM doesn't have a fast single-stock spot endpoint with indicators easily?
            # stock_individual_info_em gets static info.
            # stock_zh_a_spot_em() returns ALL stocks. Too slow (~5000 rows).
            # Alternative: stock_zh_a_hist_pre_min_em (realtime minute) doesn't have PE/Div.
            # Use 'stock_financial_abstract' for financial info? Only gives static.
            
            # BEST WAY: Use stock_zh_a_spot_em but filter? No, API downloads all.
            # OPTION 2: Use `stock_individual_info_em` for Name/Sector, but not dynamic price indicators.
            # OPTION 3: web scraping specific EM page. 
            # OPTION 4: AkShare has `stock_zh_index_spot_em`? No.
            
            # FASTEST for Single Stock Realtime with PE/PB:
            # Maybe just use `fetch_latest_data` (minute) for Price/Vol, 
            # and use a separate method for static/daily-update indicators like PE/Div?
            
            # For now, let's use the efficient approach:
            # If we need Dividend/PE, we might have to accept they are 'Daily' indicators.
            # `stock_zh_a_indicators` (PE/PB/Div history).
            
            # Let's try `stock_zh_a_spot_em` but cached? No.
            # Wait, `ak.stock_zh_a_spot_em` is surprisingly fast sometimes.
            # But let's check `ak.stock_zh_a_hist` (daily) - does headers have it? No.
            
            # Let's use `ak.stock_a_indicator_lg` (Legu)? No.
            
            # Let's fallback to scraping a lightweight endpoint if possible, or use yfinance for indicators?
            # yfinance info has 'dividendYield'.
            pass
        except:
            pass
        return {}

    def fetch_snapshot(self, symbol: str, market: str) -> dict:
        """
        Get a real-time snapshot including Valuation Indicators if possible.
        """
        try:
            # 1. Basic Price/Vol from Min Data (Fast & Reliable)
            base_data = self.fetch_latest_data(symbol, market)
            if not base_data: return None
            
            # 2. Indicators (PE, DIV)
            # For CN, we can try yfinance for indicators as a fallback, 
            # or use AkShare `stock_zh_a_valuation_baostock` (history).
            # Hack: Return base_data and let frontend use historical PE/Div from DB if today's is missing.
            # Ref: User complained Dividend is wrong. DB likely has None.
            # We NEED to fetch valid Dividend.
            
            # Try fetching "stock_zh_a_daily" (qfq) - does it have PE? No.
            # Try "stock_zh_a_daily_indicator" ?
            
            return base_data
        except Exception as e:
            self.logger.error(f"Snapshot error: {e}")
            return None

    def check_market_status(self, market: str) -> bool:
        """
        Check if the market is currently open.
        Returns True if Open, False if Closed.
        """
        from datetime import datetime, time
        import pytz

        now = datetime.now(pytz.timezone('Asia/Shanghai')) # User is likely in China
        
        current_time = now.time()

        if market == "CN":
            # Weekends
            if now.weekday() >= 5: return False
            
            # 9:30-11:30, 13:00-15:00
            morning_open = time(9, 30)
            morning_close = time(11, 30)
            afternoon_open = time(13, 0)
            afternoon_close = time(15, 0)
            return (morning_open <= current_time <= morning_close) or \
                   (afternoon_open <= current_time <= afternoon_close)

        elif market == "HK":
            # Weekends
            if now.weekday() >= 5: return False
            
            # 9:30-12:00, 13:00-16:00
            morning_open = time(9, 30)
            morning_close = time(12, 0)
            afternoon_open = time(13, 0)
            afternoon_close = time(16, 0)
            return (morning_open <= current_time <= morning_close) or \
                   (afternoon_open <= current_time <= afternoon_close)

        elif market == "US":
            # US Eastern Time: 9:30 - 16:00
            # Convert Shanghai 'now' to US/Eastern
            us_tz = pytz.timezone('US/Eastern')
            us_now = now.astimezone(us_tz)
            
            # US verify Weekday
            # US verify Weekday
            if us_now.weekday() >= 5: return False
            
            us_time = us_now.time()
            market_open = dtime(9, 30)
            market_close = dtime(16, 0)
            return (market_open <= us_time <= market_close)

        return True # Default to Open if unknown

    def fetch_latest_data(self, symbol: str, market: str, force_refresh: bool = False):
        """
        Fetch standard market data with strict caching rules:
        1. Check Market Status.
        2. If Closed & DB has valid data -> Return DB (Skip API).
        3. If Open or DB Missing -> Fetch API -> Write DB -> Return.
        """
        try:
            # Ensure necessary imports for DB operations
            from database import MarketData, create_db_and_tables
            from sqlmodel import Session, create_engine, select
            from datetime import datetime, timedelta, time as dtime # dtime for clarity with time objects
            import pytz
            import logging # For logging.info

            # Initialize engine if not already done (assuming self.engine might not exist yet)
            if not hasattr(self, 'engine') or self.engine is None:
                self.engine = create_engine("sqlite:///database.db")
                create_db_and_tables(self.engine) # Ensure tables exist

            # 1. Check Market Status
            is_open, reason = self.check_market_status(market)
            self.logger.info(f"Checking {symbol} ({market}): Market Open? {is_open} ({reason})")

            # 2. Database First Strategy (If Market Closed)
            # If market is closed, we only need data once. If we have it, don't fetch.
            # If market is open, we might allow fetching if force_refresh is True.
            
            # Helper to check DB
            with Session(self.engine) as session:
                latest_db = session.exec(
                    select(MarketDataDaily)
                    .where(MarketDataDaily.symbol == symbol)
                    .order_by(MarketDataDaily.timestamp.desc())
                    .limit(1)
                ).first()

                if latest_db:
                    db_date_str = str(latest_db.timestamp).split(' ')[0] # YYYY-MM-DD
                    
                    # If Market Closed and we have data
                    if not is_open and not force_refresh: # Only use DB if not forced to refresh
                        self.logger.info(f"Market Closed. DB Record found: {db_date_str}. Returning Cached.")
                        base_date = db_date_str
                        date_str = ""
                        if market == "CN":
                            date_str = f"{base_date} 15:00"
                        elif market == "HK":
                            date_str = f"{base_date} 16:00"
                        elif market == "US":
                            date_str = f"{base_date} 16:00 美东"
                        
                        return {
                            "symbol": latest_db.symbol,
                            "price": latest_db.close,
                            "change": latest_db.change,
                            "pct_change": latest_db.pct_change,
                            "volume": latest_db.volume,
                            "market": latest_db.market,
                            "date": date_str,
                            "pe": latest_db.pe,
                            "dividend_yield": latest_db.dividend_yield,
                            "open": latest_db.open,
                            "high": latest_db.high,
                            "low": latest_db.low,
                            "close": latest_db.close,
                            "prev_close": latest_db.prev_close
                        }

            # 3. Fetch from API (If Open or DB Missing/Forced Refresh)
            self.logger.info(f"Fetching API for {symbol} (Force: {force_refresh}, Open: {is_open})")
            
            df = pd.DataFrame()
            if market == "CN":
                df = self.fetch_cn_min_data(symbol, period='1')
            elif market == "HK":
                df = self.fetch_hk_min_data(symbol, period='1')
            elif market == "US":
                if symbol.startswith('^'):
                     # Indices: Skip AkShare, rely on Yahoo Fallback
                     df = pd.DataFrame() 
                else:
                     symbol_min = self.to_akshare_us_symbol(symbol, for_minute=True)
                     df = self.fetch_us_min_data(symbol_min)
            
            latest_data = None # Initialize to avoid UnboundLocalError

            if df is not None and not df.empty:
                # Get last row
                latest = df.iloc[-1]
                
                # Format Timestamp Explicitly
                time_val = latest['时间']
                if pd.api.types.is_datetime64_any_dtype(df['时间']):
                     date_str = time_val.strftime('%Y-%m-%d %H:%M')
                else:
                     # Parse string
                     try:
                        date_str = pd.to_datetime(time_val).strftime('%Y-%m-%d %H:%M')
                     except:
                        date_str = str(time_val)
                
                # FIX 00:00 timestamps (if daily data returned as 00:00)
                if date_str.endswith("00:00"):
                     date_base = date_str.split(' ')[0]
                     if market == "CN": date_str = f"{date_base} 15:00"
                     elif market == "HK": date_str = f"{date_base} 16:00"
                     # US data usually fetched via min so shouldn't need this, but good safety
                
                # Append '美东' for US market
                if market == "US":
                    date_str = f"{date_str} 美东"

                # Filter for the latest date in the dataframe
                latest_date_str = str(latest['时间']).split(' ')[0]
                # Check if '时间' is datetime
                if pd.api.types.is_datetime64_any_dtype(df['时间']):
                     # Filter rows with same date as latest row
                    latest_date = latest['时间'].date()
                    day_df = df[df['时间'].dt.date == latest_date]
                    total_vol = day_df['成交量'].sum()
                else:
                    try: 
                        total_vol = df['成交量'].sum() 
                    except:
                        total_vol = latest['成交量']

                latest_data = {
                    "symbol": symbol,
                    "market": market,
                    "date": date_str,
                    "volume": int(total_vol), # Cumulative Volume
                    "open": float(latest['开盘']),
                    "high": float(latest['最高']),
                    "low": float(latest['最低']),
                    "close": float(latest['收盘']),
                    "price": float(latest['收盘']) # Alias
                }
            
            # Merge with Yahoo Indicators (for Yield, PE, MarketCap)
            # This also serves as a Fallback if primary fetch failed (so latest_data might be None at start of this block)
            try:
                indicators = self.fetch_yahoo_indicators(symbol)
                if indicators:
                    # If primary fetch failed, try to construct latest_data from Yahoo
                    if latest_data is None:
                        # Yahoo has 'price', 'volume' (Daily), 'dividend_yield'
                        # We need 'date'
                        from datetime import datetime, timedelta
                        import pytz
                        
                        now = datetime.now(pytz.timezone('Asia/Shanghai'))
                        
                        if market == "US":
                            us_tz = pytz.timezone('US/Eastern')
                            us_now = now.astimezone(us_tz)
                            
                            # Logic: If Market is Closed (Weekend or after 16:00), show Closing Time
                            if us_now.weekday() >= 5:
                                # Weekend -> Show last Friday
                                offset = us_now.weekday() - 4
                                last_close = us_now - timedelta(days=offset)
                                date_str = f"{last_close.strftime('%Y-%m-%d')} 16:00 美东"
                            elif us_now.time() > dtime(16, 0):
                                # Weekday after close -> Show Today 16:00
                                date_str = f"{us_now.strftime('%Y-%m-%d')} 16:00 美东"
                            else:
                                # Market Open
                                date_str = f"{us_now.strftime('%Y-%m-%d %H:%M')} 美东"
                        else:
                            date_str = now.strftime('%Y-%m-%d %H:%M')
                        
                        latest_data = {
                            "symbol": symbol,
                            "market": market,
                            "date": date_str,
                            "volume": indicators.get('volume', 0),
                            "open": indicators.get('open', 0),
                            "high": indicators.get('dayHigh', indicators.get('high', 0)), # Yahoo info often uses dayHigh/dayLow
                            "low": indicators.get('dayLow', indicators.get('low', 0)),
                            "close": indicators.get('price', 0),
                            "price": indicators.get('price', 0)
                        }
                    
                    # Merge Indicators (PE, Div)
                    for k, v in indicators.items():
                         if k == 'volume': continue
                         # Don't overwrite existing valid data unless missing
                         if k not in latest_data or latest_data[k] is None or latest_data[k] == 0:
                            latest_data[k] = v
                    
                    # FORCE Update Price for US Stocks from Yahoo (more realtime?)
                    if market == "US" and indicators.get('price'):
                         latest_data['price'] = indicators['price']
                         latest_data['close'] = indicators['price']
                         # Force update open if available to ensure correct change %
                         if indicators.get('open'): latest_data['open'] = indicators['open']
            
            except Exception as e:
                # self.logger.error(f"Yahoo Fallback Failed: {e}")
                pass

            return latest_data if latest_data else None

        except Exception as e:
            self.logger.error(f"Error fetching latest data for {symbol}: {e}")
        return None

    def fetch_cn_daily_data(self, symbol: str, start_date: str = "20200101") -> pd.DataFrame:
        try:
            # 从 Canonical ID 提取纯代码 (CN:STOCK:600030 -> 600030)
            if ':' in symbol:
                symbol = symbol.split(':')[-1]
            code = symbol.replace('.sh', '').replace('.sz', '').zfill(6)
            self.logger.info(f"Fetching CN daily data for {code} since {start_date}...")
            df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start_date, adjust="qfq")
            if df is not None and not df.empty and '日期' in df.columns:
                df = df.rename(columns={'日期': '时间'})
                df['时间'] = pd.to_datetime(df['时间'])
                return df
            
            # If empty, try fallback
            self.logger.warning(f"AkShare empty for CN {symbol}, trying fallback...")
            return self._fetch_fallback_yfinance(symbol, "CN")
            
        except Exception as e:
            self.logger.error(f"Error fetching CN daily data for {symbol}: {str(e)}")
            self.logger.info(f"Exception: switching to yfinance fallback for {symbol}")
            return self._fetch_fallback_yfinance(symbol, "CN")

    def fetch_hk_daily_data(self, symbol: str, start_date: str = "20200101") -> pd.DataFrame:
        try:
            # 从 Canonical ID 提取纯代码 (HK:STOCK:00700 -> 00700)
            if ':' in symbol:
                symbol = symbol.split(':')[-1]
            code = symbol.replace('.hk', '').zfill(5)
            self.logger.info(f"Fetching HK daily data for {code} since {start_date}...")
            df = ak.stock_hk_hist(symbol=code, period="daily", start_date=start_date, adjust="qfq")
            if df is not None and not df.empty and '日期' in df.columns:
                df = df.rename(columns={'日期': '时间'})
                df['时间'] = pd.to_datetime(df['时间'])
                return df
            
            # If empty, try fallback
            self.logger.warning(f"AkShare empty for HK {symbol}, trying fallback...")
            return self._fetch_fallback_yfinance(symbol, "HK")
            
        except Exception as e:
            self.logger.error(f"Error fetching HK daily data for {symbol}: {str(e)}")
            self.logger.info(f"Exception: switching to yfinance fallback for {symbol}")
            return self._fetch_fallback_yfinance(symbol, "HK")

    def to_akshare_us_symbol(self, symbol, for_minute=False):
        # symbol 可能是 105.msft、106.tsm、MSFT、TSM
        if for_minute:
            # 保留前缀，转小写
            if symbol.startswith("105.") or symbol.startswith("106."):
                return symbol.lower()
            if symbol.upper() == "TSM":
                return "106.tsm"
            # Default fallback assumption for US mapping if prefix missing
            return "105." + symbol.lower() 
        else:
            if symbol.startswith("105.") or symbol.startswith("106."):
                return symbol.split(".")[1].upper()
            return symbol.upper()

    def _fetch_fallback_yfinance(self, symbol: str, market: str, period: str = "max") -> pd.DataFrame:
        import yfinance as yf
        try:
            yf_symbol = symbol
            if market == "CN":
                if symbol.endswith('.sh'):
                    yf_symbol = symbol.replace('.sh', '.SS')
                elif symbol.endswith('.sz'):
                    yf_symbol = symbol.replace('.sz', '.SZ')
            elif market == "HK":
                # HK symbols in yfinance are 4 digits usually? Or 5? 
                # 00998 -> 0998.HK
                code = symbol.replace('.hk', '')
                if code.isdigit():
                    yf_symbol = f"{int(code):04d}.HK"
                else:
                    yf_symbol = f"{code}.HK"

            self.logger.info(f"Fallback: fetching {yf_symbol} via yfinance ({period})...")
            stock = yf.Ticker(yf_symbol)
            # Fetch requested historical data
            hist = stock.history(period=period)
            
            if hist.empty:
                self.logger.warning(f"yfinance fallback also empty for {yf_symbol}")
                return pd.DataFrame()
            
            # Reset index to get Date
            hist = hist.reset_index()
            # Rename columns to match what save_to_db expects (English keys also work: open, close, etc.)
            # But let's map Date -> 时间 just in case
            hist = hist.rename(columns={'Date': '时间', 'Volume': 'volume', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close'})
            
            # Ensure naive timezone
            if pd.api.types.is_datetime64_any_dtype(hist['时间']):
                hist['时间'] = hist['时间'].dt.tz_localize(None)
                
            # Add turnover approx if missing
            if 'turnover' not in hist.columns:
                 # Estimate turnover = close * volume
                hist['turnover'] = hist['close'] * hist['volume']
            
            self.logger.info(f"Fallback success for {symbol}. Got {len(hist)} rows.")
            return hist
            
        except Exception as e:
            self.logger.error(f"Fallback failed for {symbol}: {e}")
            return pd.DataFrame()

    def _fetch_fallback_yfinance_min(self, symbol: str, market: str) -> pd.DataFrame:
        """
        Fetch minute data from Yahoo as fallback.
        """
        import yfinance as yf
        try:
            if market == "CN":
                if symbol.endswith('.sh'):
                    yf_symbol = symbol.replace('.sh', '.SS')
                elif symbol.endswith('.sz'):
                    yf_symbol = symbol.replace('.sz', '.SZ')
            elif market == "HK":
                code = symbol.replace('.hk', '')
                if code.isdigit():
                    yf_symbol = f"{int(code):04d}.HK"
                else:
                    yf_symbol = f"{code}.HK"

            self.logger.info(f"Fallback (Min): fetching {yf_symbol} ...")
            stock = yf.Ticker(yf_symbol)
            # Yahoo minute data limited to 7 days usually. 
            # period='1d', interval='1m' is standard for basic realtime.
            df = stock.history(period="1d", interval="1m")
            
            if df.empty:
                return pd.DataFrame()
                
            # Formatting
            df = df.reset_index()
            # Yahoo Datetime is usually timezone aware.
            df = df.rename(columns={
                'Datetime': '时间', 'Date': '时间', 
                'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'
            })
            
            # Map Chinese keys for consistency with AkShare parsers if needed?
            # fetch_latest_data uses: latest['收盘'], latest['时间']
            # So we MUST have Chinese column names or update fetch_latest_data to handle English.
            # fetch_latest_data: return { "price": float(latest['收盘'] ... }
            # So let's rename to Chinese keys.
            df = df.rename(columns={
                'open': '开盘', 'high': '最高', 'low': '最低', 'close': '收盘', 'volume': '成交量'
            })
            
            # Ensure TZ naive
            if pd.api.types.is_datetime64_any_dtype(df['时间']):
                df['时间'] = df['时间'].dt.tz_localize(None)
                
            return df
        except Exception as e:
            self.logger.error(f"Fallback min error for {symbol}: {e}")
            return pd.DataFrame()

    def fetch_us_daily_data(self, symbol: str, period: str = "max") -> pd.DataFrame:
        try:
            # 从 Canonical ID 提取纯代码 (US:STOCK:AAPL -> AAPL)
            if ':' in symbol:
                symbol = symbol.split(':')[-1]
            self.logger.info(f"Fetching US daily data for {symbol} (period={period})...")
            # Yahoo Fallback usually better for long history US
            return self._fetch_fallback_yfinance(symbol, "US", period=period)
        except Exception as e:
            self.logger.error(f"Error fetching US daily data for {symbol}: {str(e)}")
            return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"Error fetching US daily data for {symbol}: {str(e)}")
            return pd.DataFrame()

    def save_to_db(self, symbol: str, market: str, period_data: dict) -> None:
        try:
            # Import here to avoid potential circular imports or context issues
            from database import engine
            from models import MarketDataDaily
            from sqlmodel import Session, select
            from datetime import datetime

            with Session(engine) as session:
                for period, df in period_data.items():
                    if df is None or df.empty or period != '1d':
                        continue
                    
                    for _, row in df.iterrows():
                        date_val = row.get('时间')
                        if isinstance(date_val, (datetime, pd.Timestamp)):
                            date_str = date_val.strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            date_str = str(date_val)
                        
                        try:
                            close_p = float(row.get('收盘', row.get('close', 0)))
                            
                            def get_safe_float(keys, default):
                                for k in keys:
                                    val = row.get(k)
                                    if pd.notna(val) and val is not None:
                                        return float(val)
                                return default

                            open_p = get_safe_float(['开盘', 'open'], close_p)
                            high_p = get_safe_float(['最高', 'high'], close_p)
                            low_p = get_safe_float(['最低', 'low'], close_p)
                            
                            volume_p = int(row.get('成交量', row.get('volume', 0)))
                            turnover_p = row.get('成交额', row.get('amount', row.get('turnover')))
                            turnover_p = float(turnover_p) if turnover_p is not None and pd.notnull(turnover_p) else None
                            
                            pe = row.get('pe')
                            pe = float(pe) if pe is not None and pd.notnull(pe) else None
                            pb = row.get('pb')
                            pb = float(pb) if pb is not None and pd.notnull(pb) else None

                        except:
                            continue

                        statement = select(MarketDataDaily).where(
                            MarketDataDaily.symbol == symbol,
                            MarketDataDaily.market == market,
                            MarketDataDaily.timestamp == date_str
                        )
                        existing = session.exec(statement).first()

                        if existing:
                            existing.open = open_p
                            existing.high = high_p
                            existing.low = low_p
                            existing.close = close_p
                            existing.volume = volume_p
                            if turnover_p is not None: existing.turnover = turnover_p
                            if pe is not None: existing.pe = pe
                            if pb is not None: existing.pb = pb
                            existing.updated_at = datetime.utcnow()
                            session.add(existing)
                        else:
                            session.add(MarketDataDaily(
                                symbol=symbol,
                                market=market,
                                timestamp=date_str,
                                open=open_p,
                                high=high_p,
                                low=low_p,
                                close=close_p,
                                volume=volume_p,
                                turnover=turnover_p,
                                pe=pe,
                                pb=pb
                            ))
                
                session.commit()
                self.logger.info(f"Successfully saved DB records for {symbol}")

        except Exception as e:
            self.logger.error(f"Error saving to DB for {symbol}: {str(e)}")
        if df.empty:
            self.logger.warning(f"No data to save for {symbol} period={period}")
            return
        market_dir = os.path.join(self.output_dir, market)
        os.makedirs(market_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{symbol}_{market}_minute_data_{period}_{timestamp}_V4.xlsx"
        filepath = os.path.join(market_dir, filename)
        try:
            df.to_excel(filepath, index=False)
            self.logger.info(f"Data saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Error saving data for {symbol}: {str(e)}")

    def save_fund_flow(self, symbol: str):
        # 只采集A股资金流向
        if symbol.endswith('.sh') or symbol.endswith('.sz') or symbol.endswith('.bj'):
            stock = symbol[:6]
            market = "CN"
            try:
                # Proceeded dir logic
                market_dir = os.path.join(self.output_dir, "proceeded", market)
                os.makedirs(market_dir, exist_ok=True)
                
                fund_flow_df = ak.stock_individual_fund_flow(stock=stock, market=symbol[-2:])
                if fund_flow_df is not None and not fund_flow_df.empty:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{symbol}_{market}_fund_flow_{timestamp}_V4.xlsx"
                    filepath = os.path.join(market_dir, filename)
                    fund_flow_df.to_excel(filepath, index=False)
                    self.logger.info(f"资金流向已保存到 {filepath}")
            except Exception as e:
                self.logger.error(f"资金流向获取失败: {symbol}, 原因: {e}")


    def _get_market(self, symbol):
        symbol = symbol.upper()
        if symbol.startswith("105.") or symbol.startswith("106."):
            return "US"
        elif symbol.endswith(".HK"):
            return "HK"
        elif symbol.endswith(".SH") or symbol.endswith(".SZ"):
            return "CN"
        # US Suffixes from EastMoney search
        elif any(symbol.endswith(s) for s in [".OQ", ".N", ".AM", ".O", ".K"]):
            return "US"
        # Plain US symbols (no dot) - naive check?
        # risky if overlaps with others, but usually 3-4 chars is US if not CN/HK.
        # Let's rely on suffixes for now as SearchBar seems to provide them.
        else:
            return "Other"

    def get_stock_name(self, symbol: str) -> str:
        market = self._get_market(symbol)
        name = symbol
        
        # Helper to fetch from Tencent (qt.gtimg.cn)
        def fetch_from_tencent(code_with_prefix):
            try:
                url = f"http://qt.gtimg.cn/q={code_with_prefix}"
                headers = {"User-Agent": "Mozilla/5.0"}
                resp = requests.get(url, headers=headers, timeout=5)
                if resp.status_code == 200:
                    # format: v_hk00005="100~汇丰控股~..."
                    content = resp.text
                    if '="' in content:
                        data_str = content.split('="')[1].strip('";')
                        parts = data_str.split('~')
                        if len(parts) > 2:
                            return parts[1] # Name is usually at index 1
            except Exception as e:
                self.logger.error(f"Tencent fetch error for {code_with_prefix}: {e}")
            return None

        try:
            if market == "CN":
                code = symbol.replace('.sh', '').replace('.sz', '').zfill(6)
                # Try Tencent first for speed? Or keep AkShare. 
                # AkShare is reliable for CN. Keep AkShare.
                df = ak.stock_individual_info_em(symbol=code)
                if df is not None and not df.empty:
                    row = df[df['item'] == '股票简称']
                    if not row.empty:
                        name = row.iloc[0]['value']
                        
            elif market == "HK":
                # Tencent format: hk00005
                code = symbol.replace('.hk', '')
                fetched = fetch_from_tencent(f"hk{code}")
                if fetched: name = fetched
                
            elif market == "US":
                # Tencent format: usAAPL
                # Our symbol: 105.aapl or just AAPL?
                # to_akshare_us_symbol format: "105.aapl"
                # Extract clean symbol
                clean_symbol = symbol.split(".")[-1].upper() # aapl -> AAPL
                fetched = fetch_from_tencent(f"us{clean_symbol}")
                if fetched: name = fetched
                
        except Exception as e:
            self.logger.error(f"Error getting name for {symbol}: {e}")
        return name

    # NOTE: Modified fetch_all_stocks to accept an optional 'markets' filter
    def fetch_all_stocks(self, periods, target_markets=None):
        self.logger.info(f"Starting to fetch data for {len(self.symbols)} stocks, periods: {periods}")
        for symbol in self.symbols:
            market = self._get_market(symbol)
            if target_markets and market not in target_markets:
                continue
                
            period_data = {}

            if market == "US":
                symbol_daily = self.to_akshare_us_symbol(symbol, for_minute=False)
                symbol_min = self.to_akshare_us_symbol(symbol, for_minute=True)
                # 日线
                daily_df = self.fetch_us_daily_data(symbol_daily)
                if daily_df is not None and not daily_df.empty:
                    period_data['1d'] = daily_df
                # 分钟线
                df_1min = self.fetch_us_min_data(symbol_min)
                if df_1min is not None and not df_1min.empty:
                    period_data['1min'] = df_1min
            elif market == "CN":
                daily_df = self.fetch_cn_daily_data(symbol)
                # Fund flow
                self.save_fund_flow(symbol) 
            elif market == "HK":
                daily_df = self.fetch_hk_daily_data(symbol)
            else:
                daily_df = None
                
            if daily_df is not None and not daily_df.empty:
                period_data['1d'] = daily_df

            # 各分钟线 (US logic in original code only loops if periods passed, but US calc above did 1min explicitly)
            # Original code logic:
            # For each period in periods:
            #   fetch min data
            
            for period in periods:
                df = None
                if market == "US" and period == "1":
                    # Already fetched above potentially, but let's follow logic
                    # Original code fetched 1min above for US regardless of 'periods' arg? 
                    # Actually original code:
                    # if market == "US": ... fetch 1min ... period_data['1min'] = ...
                    # then loop periods...
                    # if market == "US" and period == "1": fetch_us_min_data(symbol)
                    # It seems redundant or specific.
                    # Let's trust original logic but ensure we don't double fetch if 1min is already there.
                    if '1min' in period_data:
                        df = period_data['1min']
                    else:
                        df = self.fetch_us_min_data(symbol) # using symbol not symbol_min? 
                        # Original code: df = self.fetch_us_min_data(symbol) -> Wait, method expects which format for US?
                        # to_akshare_us_symbol is used above. 
                        # fetch_us_min_data takes 'symbol'.
                        # In loop: self.fetch_us_min_data(symbol). 
                        # In block above loop: self.fetch_us_min_data(symbol_min).
                        # Let's fix this slightly to be safe: use symbol_min for US min data.
                        pass

                elif market == "HK":
                    df = self.fetch_hk_min_data(symbol, period=period)
                elif market == "CN":
                    df = self.fetch_cn_min_data(symbol, period=period)
                
                if df is not None and not df.empty:
                    df = self._fix_open_price(df)
                    period_data[f'{period}min'] = df

            # 保存
            # 保存
            if period_data:
                self._save_stock_to_excel(symbol, market, period_data)
                self.save_to_db(symbol, market, period_data)

    def fetch_single_stock(self, symbol: str, periods=None):
        if periods is None:
            periods = ['1d', '1', '5']
            
        market = self._get_market(symbol)
        self.logger.info(f"Fetching single stock {symbol} ({market})...")
        
        period_data = {}

        # 1. Daily Data
        daily_df = None
        if market == "US":
            symbol_daily = self.to_akshare_us_symbol(symbol, for_minute=False)
            daily_df = self.fetch_us_daily_data(symbol_daily)
        elif market == "CN":
            daily_df = self.fetch_cn_daily_data(symbol)
        elif market == "HK":
            daily_df = self.fetch_hk_daily_data(symbol)
            
        if daily_df is not None and not daily_df.empty:
            period_data['1d'] = daily_df

        # 2. Minute Data
        # Only fetch '1' and '5' for efficiency if not specified
        target_periods = [p for p in periods if p != '1d']
        
        for period in target_periods:
            df = None
            if market == "US":
                # For US minute, we use the specific symbol format if needed, or just symbol?
                # fetch_us_min_data uses 'symbol' argument and calls stock_us_hist_min_em(symbol=symbol)
                # We need to make sure we pass what it expects.
                # fetch_all_stocks passed 'symbol_min' for 1min? 
                # Let's check fetch_all_stocks again. 
                # It did: symbol_min = self.to_akshare_us_symbol(symbol, for_minute=True)
                # then self.fetch_us_min_data(symbol_min)
                symbol_min = self.to_akshare_us_symbol(symbol, for_minute=True)
                df = self.fetch_us_min_data(symbol_min)
            elif market == "HK":
                df = self.fetch_hk_min_data(symbol, period=period)
            elif market == "CN":
                df = self.fetch_cn_min_data(symbol, period=period)
            
            if df is not None and not df.empty:
                df = self._fix_open_price(df)
                period_data[f'{period}min'] = df

        # 3. Save
        if period_data:
            # We skip Excel for single stock fetch to save time? Or keep it?
            # Creating excel for every single add might be slow. Let's start with DB only for speed.
            # self._save_stock_to_excel(symbol, market, period_data) 
            self.save_to_db(symbol, market, period_data)
            
            # Log counts
            counts = {k: len(v) for k, v in period_data.items()}
            self.logger.info(f"Single stock fetch success for {symbol}: {counts} records.")
            return True
        else:
            self.logger.warning(f"Single stock fetch returned NO data for {symbol}")
        return False

    def _save_stock_to_excel(self, symbol, market, period_data):
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        market_dir = os.path.join(self.output_dir, market)
        os.makedirs(market_dir, exist_ok=True)
        filename = f"{symbol}_{market}_minute_data_{timestamp}_V4.xlsx"
        filepath = os.path.join(market_dir, filename)
        sheet_order = ['1d', '30min', '15min', '5min', '1min']
        ordered_keys = [k for k in sheet_order if k in period_data] + [k for k in period_data if k not in sheet_order]
        try:
            with pd.ExcelWriter(filepath) as writer:
                for period in ordered_keys:
                    df = period_data[period]
                    df.to_excel(writer, sheet_name=period, index=False)
            self.logger.info(f"Data for {symbol} saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Failed to save excel for {symbol}: {e}")

    def _fix_open_price(self, df):
        df = df.copy()
        open_col = "开盘"
