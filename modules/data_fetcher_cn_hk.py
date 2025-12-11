# modules/data_fetcher_cn_hk.py

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta

def fetch_cn_hk_day_kline(symbol: str) -> pd.DataFrame:
    """
    获取A股或港股日线数据，使用 Akshare
    返回DataFrame，包含: date, open, high, low, close, volume
    """
    try:
        if symbol.startswith('SH.') or symbol.startswith('SZ.'):
            market, code = symbol.split('.')
            stock_df = ak.stock_zh_a_daily(symbol=code, adjust="qfq")
        elif symbol.startswith('HK.'):
            code = symbol.split('.')[1]
            stock_df = ak.stock_hk_daily(symbol=code)
        else:
            print(f"[WARNING] 未知市场类型 {symbol}")
            return None

        if stock_df is not None and not stock_df.empty:
            stock_df['date'] = pd.to_datetime(stock_df['date'])
            stock_df = stock_df[stock_df['date'] >= (datetime.now() - timedelta(days=14))]
            stock_df = stock_df[['date', 'open', 'high', 'low', 'close', 'volume']]
            return stock_df.reset_index(drop=True)
    except Exception as e:
        print(f"[WARNING] 拉取 {symbol} 日线异常: {e}")
    return None

def fetch_cn_hk_minute_kline(symbol: str, interval: str) -> pd.DataFrame:
    """
    获取A股或港股分钟线数据，使用 Akshare
    返回DataFrame，包含: datetime, open, high, low, close, volume
    """
    try:
        market_map = {
            'SH.': '1',  # 上交所
            'SZ.': '0',  # 深交所
            'HK.': '116' # 港交所
        }
        market_prefix = symbol[:3]
        code = symbol.split('.')[1]
        secid = f"{market_map[market_prefix]}.{code}"

        interval_mapping = {
            '5m': '5',
            '15m': '15',
            '30m': '30',
            '1h': '60',
            '2h': '120'
        }

        if interval not in interval_mapping:
            print(f"[WARNING] 不支持的分钟周期: {interval}")
            return None

        df = ak.stock_kline_early_em(
            secid=secid,
            klt=interval_mapping[interval],
            fqt='1',
            end="20500101",
            lmt="100"  # 取最近100条，足够覆盖7天
        )

        if df is not None and not df.empty:
            df['datetime'] = pd.to_datetime(df['日期'])
            df = df[['datetime', '开盘', '最高', '最低', '收盘', '成交量']]
            df.rename(columns={
                '开盘': 'open',
                '最高': 'high',
                '最低': 'low',
                '收盘': 'close',
                '成交量': 'volume'
            }, inplace=True)
            return df.reset_index(drop=True)
    except Exception as e:
        print(f"[WARNING] 拉取 {symbol} {interval}分钟线异常: {e}")
    return None 