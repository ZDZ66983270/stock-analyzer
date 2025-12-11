# data_fetcher.py

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
        self.symbols_file = symbols_file
        self.log_dir = log_dir
        self.output_dir = output_dir
        self.est_tz = pytz.timezone('Asia/Shanghai')
        self._setup_logger()
        self.symbols = self._load_symbols()

    def _setup_logger(self):
        log_dir = 'logs_V4'
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_V4.log")
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console.setFormatter(formatter)
        logging.getLogger().addHandler(console)
        self.logger = logging.getLogger(__name__)

    def _load_symbols(self) -> list:
        symbols = []
        try:
            fetcher_dir = os.path.dirname(os.path.abspath(__file__))
            symbols_file = os.path.join(fetcher_dir, 'symbols_V4.txt')
            with open(symbols_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        symbols.append(line)
            self.logger.info(f"Loaded symbols: {symbols}")
        except Exception as e:
            self.logger.error(f"Error loading symbols: {str(e)}")
        return symbols

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

    def save_data(self, df: pd.DataFrame, symbol: str, market: str, period: str) -> None:
        if df.empty:
            self.logger.warning(f"No data to save for {symbol} period={period}")
            return
        market_dir = os.path.join("output_V4", market)
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
                fund_flow_df = ak.stock_individual_fund_flow(stock=stock, market=symbol[-2:])
                if fund_flow_df is not None and not fund_flow_df.empty:
                    # 直接存到 proceeded/CN 目录
                    market_dir = os.path.join(self.output_dir, "proceeded", market)
                    os.makedirs(market_dir, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{symbol}_{market}_fund_flow_{timestamp}_V4.xlsx"
                    filepath = os.path.join(market_dir, filename)
                    fund_flow_df.to_excel(filepath, index=False)
                    self.logger.info(f"资金流向已保存到 {filepath}")
            except Exception as e:
                self.logger.error(f"资金流向获取失败: {symbol}, 原因: {e}")

    def fetch_all_stocks(self, periods):
        self.logger.info(f"Starting to fetch data for {len(self.symbols)} stocks, periods: {periods}")
        for symbol in self.symbols:
            market = self._get_market(symbol)
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
            elif market == "HK":
                daily_df = self.fetch_hk_daily_data(symbol)
            else:
                daily_df = None
            if daily_df is not None and not daily_df.empty:
                period_data['1d'] = daily_df

            # 各分钟线
            for period in periods:
                if market == "US" and period == "1":
                    df = self.fetch_us_min_data(symbol)
                elif market == "HK":
                    df = self.fetch_hk_min_data(symbol, period=period)
                elif market == "CN":
                    df = self.fetch_cn_min_data(symbol, period=period)
                else:
                    df = None
                if df is not None and not df.empty:
                    df = self._fix_open_price(df)
                    period_data[f'{period}min'] = df

            # 保存
            if period_data:
                self._save_stock_to_excel(symbol, market, period_data)
            if market == "CN":
                self.save_fund_flow(symbol)

    def _save_stock_to_excel(self, symbol, market, period_data):
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        market_dir = os.path.join(self.output_dir, market)
        os.makedirs(market_dir, exist_ok=True)
        filename = f"{symbol}_{market}_minute_data_{timestamp}_V4.xlsx"
        filepath = os.path.join(market_dir, filename)
        sheet_order = ['1d', '30min', '15min', '5min', '1min']
        ordered_keys = [k for k in sheet_order if k in period_data] + [k for k in period_data if k not in sheet_order]
        with pd.ExcelWriter(filepath) as writer:
            for period in ordered_keys:
                df = period_data[period]
                df.to_excel(writer, sheet_name=period, index=False)
        self.logger.info(f"Data for {symbol} saved to {filepath}")

    def _get_market(self, symbol):
        if symbol.startswith("105.") or symbol.startswith("106."):
            return "US"
        elif symbol.endswith(".hk"):
            return "HK"
        elif symbol.endswith(".sh") or symbol.endswith(".sz"):
            return "CN"
        else:
            return "Other"

    def _fix_open_price(self, df):
        """
        修正分钟行情中开盘价为0的情况：
        若开盘价为0，则用前一分钟的收盘价填充；若前一分钟无收盘价则不处理。
        适配列名为"开盘""收盘"，并用 iloc 保证按行号遍历。
        """
        df = df.copy()
        open_col = "开盘"
        close_col = "收盘"
        if open_col in df.columns and close_col in df.columns:
            for i in range(1, len(df)):
                try:
                    if float(df.iloc[i][open_col]) == 0:
                        df.iloc[i, df.columns.get_loc(open_col)] = df.iloc[i-1][close_col]
                except Exception:
                    continue
        return df

    def resample_kline(self, df, freq):
        df = df.copy()
        df['时间'] = pd.to_datetime(df['时间'])
        df = df.set_index('时间')
        df_resampled = df.resample(freq, label='right', closed='right').agg({
            '开盘': 'first',
            '最高': 'max',
            '最低': 'min',
            '收盘': 'last',
            '成交量': 'sum',
            # 其他字段可按需添加
        }).dropna().reset_index()
        return df_resampled

    def to_akshare_us_symbol(self, symbol, for_minute=False):
        # symbol 可能是 105.msft、106.tsm、MSFT、TSM
        if for_minute:
            # 保留前缀，转小写
            if symbol.startswith("105.") or symbol.startswith("106."):
                return symbol.lower()
            if symbol.upper() == "TSM":
                return "106.tsm"
            else:
                return "105." + symbol.lower()
        else:
            # 去掉前缀，转大写
            if symbol.startswith("105.") or symbol.startswith("106."):
                return symbol.split(".")[1].upper()
            return symbol.upper()

    def download_cn_reports(self, symbols):
        """
        下载A股的资产负债表、利润表、现金流量表，并合并到同一个Excel文件的不同sheet。
        只对"报告日"转字符串，数字列保留原样。
        """
        import akshare as ak
        from datetime import datetime
        import os
        import pandas as pd

        report_types = {
            "资产负债表": "balance_sheet",
            "利润表": "income_statement",
            "现金流量表": "cashflow_statement"
        }
        for symbol in symbols:
            if symbol.endswith('.sh') or symbol.endswith('.sz') or symbol.endswith('.bj'):
                code = symbol[:6]
                report_dfs = {}
                for report_name, sheet_name in report_types.items():
                    try:
                        df = ak.stock_financial_report_sina(stock=code, symbol=report_name)
                        if df is not None and not df.empty:
                            # 只对"报告日"转为字符串，其他列保留原样
                            if '报告日' in df.columns:
                                df['报告日'] = df['报告日'].astype(str)
                            report_dfs[sheet_name] = df
                            print(f"{report_name}下载成功: {symbol}")
                        else:
                            print(f"{report_name}无数据: {symbol}")
                    except Exception as e:
                        print(f"{report_name}下载失败: {symbol}, 原因: {e}")
                if report_dfs:
                    market_dir = os.path.join(self.output_dir, "CN")
                    os.makedirs(market_dir, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{symbol}_CN_financial_reports_{timestamp}_V4.xlsx"
                    filepath = os.path.join(market_dir, filename)
                    with pd.ExcelWriter(filepath) as writer:
                        for sheet_name, df in report_dfs.items():
                            df.to_excel(writer, sheet_name=sheet_name, index=False)
                    print(f"三大报表已合并保存到 {filepath}")

def ask_download_reports():
    print("检测到A股代码，是否需要同时下载报表？(y/n, 10秒内不输入默认否): ", end='', flush=True)
    result = {'answer': 'n'}
    def get_input():
        ans = input()
        if ans.strip().lower() == 'y':
            result['answer'] = 'y'
    t = threading.Thread(target=get_input)
    t.daemon = True
    t.start()
    t.join(timeout=10)
    return result['answer']

def main():
    fetcher = DataFetcher()
    # 检查是否有A股
    has_cn = any(s.endswith('.sh') or s.endswith('.sz') or s.endswith('.bj') for s in fetcher.symbols)
    if has_cn:
        ans = ask_download_reports()
        if ans == 'y':
            fetcher.download_cn_reports(fetcher.symbols)
    fetcher.fetch_all_stocks(periods=['1', '5', '15', '30'])

if __name__ == "__main__":
    main()
