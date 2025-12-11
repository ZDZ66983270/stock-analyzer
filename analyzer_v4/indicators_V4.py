import os
import pandas as pd
import shutil
import akshare as ak
import time
import re

def calc_ma(df, n):
    return df['收盘'].rolling(window=n).mean()

def calc_macd(df, fast=12, slow=26, signal=9):
    """
    MACD 5.3版：以收盘价为基础的标准MACD算法
    """
    ema_fast = df['收盘'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['收盘'].ewm(span=slow, adjust=False).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False).mean()
    macd = 2 * (dif - dea)
    df['DIF'] = dif
    df['DEA'] = dea
    df['MACD'] = macd
    return df

def calc_kdj(df, n=9, k_init=50, d_init=50):
    low_min = df['最低'].rolling(window=n, min_periods=1).min()
    high_max = df['最高'].rolling(window=n, min_periods=1).max()
    # 防止分母为0
    denominator = (high_max - low_min)
    denominator = denominator.replace(0, pd.NA)  # 用NA替换0，避免除0
    rsv = (df['收盘'] - low_min) / denominator * 100
    rsv = rsv.fillna(50)  # 用50填充NA，或你可以用0或其他合适的初值

    k_list = []
    d_list = []
    k = k_init
    d = d_init
    for val in rsv:
        k = k * 2 / 3 + val / 3
        d = d * 2 / 3 + k / 3
        k_list.append(k)
        d_list.append(d)
    df['K'] = k_list
    df['D'] = d_list
    df['J'] = 3 * df['K'] - 2 * df['D']
    return df

def calc_rsi(df, period=14):
    """
    计算RSI指标，支持任意周期，返回Series。
    公式与主流券商一致，采用SMA（简单移动平均）。
    """
    close = df['收盘'].astype(float)
    delta = close.diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi.rename(f'RSI{period}')

def calc_rsi_wilder(df, period=14):
    """
    计算RSI指标（Wilder's smoothing, EMA, alpha=1/period），支持任意周期。
    """
    close = df['收盘'].astype(float)
    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()

    rs = avg_gain / (avg_loss.replace(0, 1e-10))  # 防止除0
    rsi = 100 - (100 / (1 + rs))

    return rsi.rename(f'RSI{period}')

def calc_wilder_ma(df, n):
    return df['收盘'].ewm(alpha=1/n, adjust=False).mean()

def get_market_from_filename(filename):
    filename = filename.upper()
    if "_US_" in filename or filename.endswith("_US.XLSX") or "_US." in filename:
        return "US"
    elif "_HK_" in filename or filename.endswith("_HK.XLSX") or "_HK." in filename:
        return "HK"
    elif "_CN_" in filename or filename.endswith("_CN.XLSX") or "_CN." in filename:
        return "CN"
    elif ".US_" in filename or ".US." in filename:
        return "US"
    elif ".HK_" in filename or ".HK." in filename:
        return "HK"
    elif ".CN_" in filename or ".CN." in filename:
        return "CN"
    else:
        return "Other"

def process_file(input_path, output_base_dir):
    """
    处理单个行情文件，按市场分目录保存
    """
    # 读取原始文件
    xls = pd.ExcelFile(input_path, engine='openpyxl')
    base_name = os.path.basename(input_path)
    market = get_market_from_filename(base_name)
    
    # 按市场分目录保存
    out_dir = os.path.join(output_base_dir, market)  # 确保保存在市场子目录下
    os.makedirs(out_dir, exist_ok=True)
    
    # 添加时间戳到文件名，避免覆盖
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    name_without_ext = os.path.splitext(base_name)[0]
    out_path = os.path.join(out_dir, f"{name_without_ext}_processed_{timestamp}.xlsx")
    
    period_dfs = {}

    # 读取原有sheet
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        # 美股1d字段翻译（确保先做！）
        if sheet == '1d' and market == "US":
            df.columns = [col.strip().lower() for col in df.columns]
            us_col_map = {
                'date': '时间',
                'open': '开盘',
                'high': '最高',
                'low': '最低',
                'close': '收盘',
                'volume': '成交量'
            }
            df = df.rename(columns=us_col_map)
        # 30天过滤（A股、港股、美股都适用）
        if sheet == '1d' and '时间' in df.columns:
            df['时间'] = pd.to_datetime(df['时间'])
            last_date = df['时间'].dt.date.max()
            first_date = last_date - pd.Timedelta(days=1825)
            df = df[(df['时间'].dt.date >= first_date) & (df['时间'].dt.date <= last_date)]
        if sheet == '1min' and '时间' in df.columns:
            freq_map = {
                '5min': '5T',
                '15min': '15T',
                '30min': '30T',
                '1h': '1H',
                '2h': '2H'
            }
            for period, freq in freq_map.items():
                df_resampled = resample_kline(df, freq, market)
                period_dfs[period] = df_resampled
        period_dfs[sheet] = df

    # 对所有周期做指标计算
    for period, df in period_dfs.items():
        if period.lower() == "fund_flow":
            continue
        if df.empty or '收盘' not in df.columns or '最高' not in df.columns or '最低' not in df.columns:
            continue
        # 计算多个周期的MA
        for n in [5, 10, 20, 30, 60]:
            df[f'MA{n}'] = calc_ma(df, n)
        df = calc_macd(df)
        df = calc_kdj(df)
        for n in [6, 12, 24]:
            df[f'RSI{n}'] = calc_rsi_wilder(df, n)
        period_dfs[period] = df

    # 保存，sheet顺序
    sheet_order = ['1d', '4h', '2h', '30min', '15min', '5min', '1min']
    ordered_keys = [k for k in sheet_order if k in period_dfs] + [k for k in period_dfs if k not in sheet_order]
    
    # 确保输出文件有.xlsx扩展名
    if not out_path.endswith('.xlsx'):
        out_path = out_path + '.xlsx'
        
    with pd.ExcelWriter(out_path, engine='openpyxl') as writer:
        for period in ordered_keys:
            period_dfs[period].to_excel(writer, sheet_name=period, index=False)
    print(f"已保存到 {out_path}")

def resample_kline(df, freq, market=None):
    df = df.copy()
    df['时间'] = pd.to_datetime(df['时间'])
    df = df.set_index('时间')
    df_resampled = df.resample(freq, label='right', closed='right').agg({
        '开盘': 'first',
        '最高': 'max',
        '最低': 'min',
        '收盘': 'last',
        '成交量': 'sum',
    }).dropna().reset_index()

    # 修正1d的收盘时间
    if freq.lower() in ['1d', '1day', 'd', 'day']:
        if market == "CN":
            close_time = "15:00:00"
        elif market == "HK":
            close_time = "16:00:00"
        elif market == "US":
            close_time = "16:00:00"
        else:
            close_time = "15:00:00"
        df_resampled['时间'] = df_resampled['时间'].dt.strftime('%Y-%m-%d') + f' {close_time}'
        df_resampled['时间'] = pd.to_datetime(df_resampled['时间'])
    return df_resampled

def batch_process(input_dir, output_dir):
    """
    批量处理行情文件，跳过重复文件
    """
    os.makedirs(output_dir, exist_ok=True)
    processed_symbols = set()
    
    # 获取所有文件并按时间戳排序
    files = []
    for filename in os.listdir(input_dir):
        if filename.endswith('.xlsx'):
            m = re.match(r'([A-Za-z0-9\.]+)_([A-Z]+)_.*?(\d{8})', filename)
            if m:
                symbol = m.group(1)
                date_str = m.group(3)
                files.append((filename, symbol, date_str))
    
    # 按时间戳降序排序
    files.sort(key=lambda x: x[2], reverse=True)
    
    # 处理文件，跳过已处理的股票
    for filename, symbol, _ in files:
        if symbol in processed_symbols:
            print(f"跳过重复文件: {filename}")
            continue
        processed_symbols.add(symbol)
        
        file_path = os.path.join(input_dir, filename)
        print(f"处理股票 {symbol} 的文件: {filename}")
        process_file(file_path, output_dir)
    
    print("批量指标处理完成！")

def copy_fund_flow_files(input_dir, output_base_dir):
    for fname in os.listdir(input_dir):
        if fname.endswith('fund_flow.xlsx'):
            market = "CN"
            out_dir = os.path.join(output_base_dir, market)
            os.makedirs(out_dir, exist_ok=True)
            src = os.path.join(input_dir, fname)
            dst = os.path.join(out_dir, fname)
            shutil.copy2(src, dst)
            print(f"资金流向文件已拷贝到 {dst}")

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
        return df
    except Exception as e:
        self.logger.error(f"Error fetching US daily data for {symbol}: {str(e)}")
        return pd.DataFrame()

def _save_stock_to_excel(self, symbol, market, period_data):
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    market_dir = os.path.join(self.output_dir, market)
    os.makedirs(market_dir, exist_ok=True)
    filename = f"{symbol}_{market}_minute_data_{timestamp}_V4.xlsx"  # 确保文件名以.xlsx结尾
    filepath = os.path.join(market_dir, filename)
    
    sheet_order = ['1d', '30min', '15min', '5min', '1min']
    ordered_keys = [k for k in sheet_order if k in period_data] + [k for k in period_data if k not in sheet_order]
    
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        for period in ordered_keys:
            df = period_data[period]
            df.to_excel(writer, sheet_name=period, index=False)
    self.logger.info(f"Data for {symbol} saved to {filepath}")

def resample_kline_2h_market(df, market):
    df = df.copy()
    df['时间'] = pd.to_datetime(df['时间'])
    # 市场开市时间
    if market == "CN":
        open_time = "09:30"
        close_time = "15:00"
    elif market == "HK":
        open_time = "09:30"
        close_time = "16:00"
    elif market == "US":
        open_time = "09:30"
        close_time = "16:00"
    else:
        open_time = "09:30"
        close_time = "15:00"
    df['date'] = df['时间'].dt.date
    df['time'] = df['时间'].dt.time

    result = []
    for date, group in df.groupby('date'):
        day_df = group.copy()
        day_df = day_df[(day_df['时间'].dt.time >= pd.to_datetime(open_time).time()) &
                        (day_df['时间'].dt.time <= pd.to_datetime(close_time).time())]
        if day_df.empty:
            continue
        # 以开市时间为起点，每2小时分组
        day_df = day_df.sort_values('时间')
        start = pd.to_datetime(f"{date} {open_time}")
        end = pd.to_datetime(f"{date} {close_time}")
        bins = pd.date_range(start, end, freq='2H')
        day_df['2h_bin'] = pd.cut(day_df['时间'], bins, right=True, labels=bins[1:])
        for bin_label, bin_group in day_df.groupby('2h_bin'):
            if bin_group.empty:
                continue
            res = {
                '时间': bin_group['时间'].max(),  # 2h区间最后一根K线的时间
                '开盘': bin_group['开盘'].iloc[0],
                '最高': bin_group['最高'].max(),
                '最低': bin_group['最低'].min(),
                '收盘': bin_group['收盘'].iloc[-1],
                '成交量': bin_group['成交量'].sum()
            }
            result.append(res)
    return pd.DataFrame(result)
