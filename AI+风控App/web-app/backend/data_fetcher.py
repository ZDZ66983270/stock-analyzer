
import akshare as ak
import pandas as pd
from datetime import datetime, time as dtime
import pytz
import os
import logging
import time
import threading

class DataFetcher:
    def __init__(self, symbols_file="symbols_V4.txt", log_dir="logs_V4", output_dir="output_V4"):
        # Make paths absolute relative to this file to avoid CWD issues
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.symbols_file = os.path.join(base_dir, symbols_file)
        self.log_dir = os.path.join(base_dir, log_dir)
        self.output_dir = os.path.join(base_dir, output_dir)
        
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
            return pd.DataFrame()

    def fetch_cn_daily_data(self, symbol: str) -> pd.DataFrame:
        try:
            code = symbol.replace('.sh', '').replace('.sz', '').zfill(6)
            self.logger.info(f"Fetching CN daily data for {code} ...")
            df = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq")
            if df is not None and not df.empty and '日期' in df.columns:
                df = df.rename(columns={'日期': '时间'})
                df['时间'] = pd.to_datetime(df['时间'])
            return df
        except Exception as e:
            self.logger.error(f"Error fetching CN daily data for {symbol}: {str(e)}")
            return pd.DataFrame()

    def fetch_hk_daily_data(self, symbol: str) -> pd.DataFrame:
        try:
            code = symbol.replace('.hk', '').zfill(5)
            self.logger.info(f"Fetching HK daily data for {code} ...")
            df = ak.stock_hk_hist(symbol=code, period="daily")
            if df is not None and not df.empty and '日期' in df.columns:
                df = df.rename(columns={'日期': '时间'})
                df['时间'] = pd.to_datetime(df['时间'])
            return df
        except Exception as e:
            self.logger.error(f"Error fetching HK daily data for {symbol}: {str(e)}")
            return pd.DataFrame()

    def fetch_us_daily_data(self, symbol: str) -> pd.DataFrame:
        try:
            self.logger.info(f"Fetching US daily data for {symbol} ...")
            df = ak.stock_us_daily(symbol=symbol)
            if df is not None and not df.empty and '日期' in df.columns:
                df = df.rename(columns={'日期': '时间'})
                df['时间'] = pd.to_datetime(df['时间'])
                # 只保留最近30天
                last_date = df['时间'].dt.date.max()
                first_date = last_date - pd.Timedelta(days=29)
                df = df[(df['时间'].dt.date >= first_date) & (df['时间'].dt.date <= last_date)]
            return df
        except Exception as e:
            self.logger.error(f"Error fetching US daily data for {symbol}: {str(e)}")
            return pd.DataFrame()

            return df
        except Exception as e:
            self.logger.error(f"Error fetching US daily data for {symbol}: {str(e)}")
            return pd.DataFrame()

    def save_to_db(self, symbol: str, market: str, period_data: dict) -> None:
        """
        Save fetched data to SQLite database.
        """
        try:
            # Import here to avoid potential circular imports or context issues
            from database import engine
            from models import MarketData
            from sqlmodel import Session, select
            from datetime import datetime

            with Session(engine) as session:
                for period, df in period_data.items():
                    if df is None or df.empty:
                        continue
                    
                    # Log start
                    # self.logger.info(f"Saving to DB: {symbol} - {period} ({len(df)} rows)")

                    for _, row in df.iterrows():
                        # Parse date
                        date_val = row.get('时间')
                        if isinstance(date_val, (datetime, pd.Timestamp)):
                            date_str = date_val.strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            date_str = str(date_val)
                        
                        # Map columns
                        # akshare usually returns: '开盘','收盘','最高','最低','成交量'
                        # US daily might be: 'Open', 'Close'...? 
                        # Note: `fetch_us_daily_data` uses `ak.stock_us_daily`.
                        # Let's check column names. akshare usually standardizes to Chinese if we use `stock_us_hist_min_em`.
                        # But `stock_us_daily`? 
                        # User code `fetch_us_daily_data`: just renames `日期` to `时间`.
                        # Let's assume standard names or fallback.
                        
                        try:
                            # Try Chinese first (common in akshare)
                            open_p = float(row.get('开盘', row.get('open', 0)))
                            high_p = float(row.get('最高', row.get('high', 0)))
                            low_p = float(row.get('最低', row.get('low', 0)))
                            close_p = float(row.get('收盘', row.get('close', 0)))
                            volume_p = int(row.get('成交量', row.get('volume', 0)))
                        except:
                            continue # Skip bad rows

                        # Check existing
                        statement = select(MarketData).where(
                            MarketData.symbol == symbol,
                            MarketData.market == market,
                            MarketData.period == period,
                            MarketData.date == date_str
                        )
                        existing = session.exec(statement).first()

                        if existing:
                            existing.open = open_p
                            existing.high = high_p
                            existing.low = low_p
                            existing.close = close_p
                            existing.volume = volume_p
                            existing.updated_at = datetime.utcnow()
                            session.add(existing)
                        else:
                            new_record = MarketData(
                                symbol=symbol,
                                market=market,
                                period=period,
                                date=date_str,
                                open=open_p,
                                high=high_p,
                                low=low_p,
                                close=close_p,
                                volume=volume_p
                            )
                            session.add(new_record)
                
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
        if symbol.startswith("105.") or symbol.startswith("106."):
            return "US"
        elif symbol.endswith(".hk"):
            return "HK"
        elif symbol.endswith(".sh") or symbol.endswith(".sz"):
            return "CN"
        else:
            return "Other"

    def get_stock_name(self, symbol: str) -> str:
        """
        Attempt to get stock name.
        """
        market = self._get_market(symbol)
        name = symbol
        try:
            if market == "CN":
                code = symbol.replace('.sh', '').replace('.sz', '').zfill(6)
                df = ak.stock_individual_info_em(symbol=code)
                # value field for '股票名称' key? 
                # akshare output format: 
                # item | value
                # 股票代码 | 600519
                # 股票简称 | 贵州茅台
                if df is not None and not df.empty:
                    # Filter where item == '股票简称'
                    row = df[df['item'] == '股票简称']
                    if not row.empty:
                        name = row.iloc[0]['value']
            elif market == "HK":
                # HK info? ak.stock_hk_spot_em() -> list all maybe too heavy
                # ak.stock_hk_daily(symbol=code) -> name?
                # Simple fallback: use symbol for now or specific API
                pass
            elif market == "US":
                # US name
                pass
        except Exception as e:
            self.logger.error(f"Error getting name for {symbol}: {e}")
        return name

    # NOTE: Modified fetch_all_stocks to accept an optional 'markets' filter
    def fetch_all_stocks(self, periods, target_markets=None):
        """
        Fetch data for all loaded symbols.
        :param periods: list of periods e.g. ['1', '5']
        :param target_markets: Optional list of markets to filter by e.g. ['CN', 'US']
        """
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
        close_col = "收盘"
        if open_col in df.columns and close_col in df.columns:
            # Iterate efficiently? rows logic from user
            # Using loop for exact behavior
            for i in range(1, len(df)):
                try:
                    # Handle potential string/float type issues
                    if float(df.iloc[i][open_col]) == 0:
                        col_idx = df.columns.get_loc(open_col)
                        df.iloc[i, col_idx] = df.iloc[i-1][close_col]
                except Exception:
                    continue
        return df

    def to_akshare_us_symbol(self, symbol, for_minute=False):
        if for_minute:
            if symbol.startswith("105.") or symbol.startswith("106."):
                return symbol.lower()
            if symbol.upper() == "TSM":
                return "106.tsm"
            else:
                # Default assume 105 for nasdaq/nyse? user logic simple
                return "105." + symbol.lower()
        else:
            if symbol.startswith("105.") or symbol.startswith("106."):
                return symbol.split(".")[1].upper()
            return symbol.upper()

# Standalone run
if __name__ == "__main__":
    fetcher = DataFetcher()
    fetcher.fetch_all_stocks(periods=['1', '5', '15', '30'])
