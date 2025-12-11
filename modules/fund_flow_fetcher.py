import akshare as ak
import pandas as pd

def fetch_fund_flow(symbol: str) -> pd.DataFrame:
    market = identify_market(symbol)

    if market == "SH" or market == "SZ":
        return fetch_cn_fund_flow(symbol)
    elif market == "HK":
        return fetch_hk_fund_flow(symbol)
    elif market == "US":
        # 美股资金流暂未接入，可以返回空DataFrame
        print(f"[资金流向] 暂不支持美股资金流拉取: {symbol}")
        return pd.DataFrame()
    else:
        print(f"[资金流向] 不支持的市场类型: {symbol}")
        return pd.DataFrame()

def identify_market(symbol: str) -> str:
    if symbol.startswith("US."):
        return "US"
    elif symbol.startswith("SH."):
        return "SH"
    elif symbol.startswith("SZ."):
        return "SZ"
    elif symbol.startswith("HK."):
        return "HK"
    else:
        return "Unknown"

def fetch_cn_fund_flow(symbol: str) -> pd.DataFrame:
    stock_code = symbol.split('.')[1]
    try:
        df = ak.stock_individual_fund_flow(stock=stock_code)
        return df
    except Exception as e:
        print(f"[ERROR] 拉取A股资金流失败: {e}")
        return pd.DataFrame()

def fetch_hk_fund_flow(symbol: str) -> pd.DataFrame:
    try:
        all_hk_spot = ak.stock_hk_spot()
        stock_code = symbol.split('.')[1]
        stock_row = all_hk_spot[all_hk_spot['symbol'].str.contains(stock_code)]
        if stock_row.empty:
            raise ValueError("新浪港股列表中找不到该股票")
        return stock_row
    except Exception as e:
        print(f"[ERROR] 拉取港股资金流失败: {e}")
        return pd.DataFrame()
