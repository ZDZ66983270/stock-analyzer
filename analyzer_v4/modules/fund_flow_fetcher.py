import akshare as ak
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def fetch_fund_flow_data(symbol: str, market: str) -> pd.DataFrame:
    """
    获取指定股票的资金流数据

    参数:
        symbol (str): 股票代码
        market (str): 市场标识 "sh", "sz", "hk"

    返回:
        pd.DataFrame: 资金流数据表格，若失败则返回空DataFrame
    """
    try:
        if market == "A股":
            code = symbol.split(".")[0]
            exchange = "sh" if symbol.endswith(".SH") else "sz"
            df = ak.stock_individual_fund_flow(stock=code, market=exchange)
            logger.info(f"✅ 成功获取 A股 资金流数据：{symbol}")
            return df
        elif market == "港股":
            logging.warning(f"[资金流向] 暂不支持港股资金流拉取: {symbol}")
            return pd.DataFrame()
        elif market == "美股":
            logging.warning(f"[资金流向] 暂不支持美股资金流拉取: {symbol}")
            return pd.DataFrame()
        else:
            logging.error(f"[资金流向] 不支持的市场类型: {symbol}")
            return pd.DataFrame()
    except Exception as e:
        logging.error(f"❌ 拉取{market}资金流失败: {e}")
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

def fetch_fund_flow(code: str) -> pd.DataFrame:
    """
    获取个股资金流向数据
    
    Args:
        code: A股股票代码，如 "600309"
        
    Returns:
        DataFrame: 资金流向数据，包含以下字段：
            - 日期
            - 主力净流入-净额
            - 主力净流入-净占比
            - 超大单净流入-净额
            - 超大单净流入-净占比
            - 大单净流入-净额
            - 大单净流入-净占比
            - 中单净流入-净额
            - 中单净流入-净占比
            - 小单净流入-净额
            - 小单净流入-净占比
    """
    try:
        # 验证是否为A股代码
        if not (code.startswith(('6', '0', '3'))):
            logger.warning(f"暂不支持获取非A股股票{code}的资金流向数据")
            return pd.DataFrame()
            
        logger.info(f"开始获取A股{code}的资金流向数据")
        
        # 使用东方财富接口获取资金流向数据
        df = ak.stock_individual_fund_flow(
            stock=code,
            market="sh" if code.startswith('6') else "sz"
        )
        
        if df is not None and not df.empty:
            # 统一日期列名为datetime
            if '日期' in df.columns:
                df = df.rename(columns={'日期': 'datetime'})
                
            # 确保datetime列为datetime类型
            df['datetime'] = pd.to_datetime(df['datetime'])
            
            # 按日期升序排序
            df = df.sort_values('datetime')
            
            logger.info(f"成功获取A股{code}的资金流向数据，共{len(df)}条记录")
            return df
        else:
            logger.warning(f"未获取到A股{code}的资金流向数据")
            return pd.DataFrame()
            
    except Exception as e:
        logger.error(f"获取A股{code}的资金流向数据失败: {str(e)}")
        return pd.DataFrame()
