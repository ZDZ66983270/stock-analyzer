"""
后台任务：为新添加的自选股获取数据
1. 快速获取最新数据（实时行情）
2. 慢速下载历史数据（K线图用）
"""
import asyncio
from sqlmodel import Session
from database import engine
from models import MarketDataDaily
from data_fetcher import DataFetcher
# ✅ 使用统一的符号转换工具
from utils.symbol_utils import normalize_symbol_db
from datetime import datetime
import pandas as pd


async def fetch_new_watchlist_stock(symbol: str, market: str):
    """
    为新添加的自选股获取数据
    - 第一步：快速获取最新数据（1-2秒）
    - 第二步：下载历史数据（10-30秒，不阻塞）
    """
    print(f"[Background] 开始处理新股票: {symbol} ({market})")
    
    fetcher = DataFetcher()
    
    # ========================================
    # 第一步：快速获取最新数据
    # ========================================
    print(f"[Background] 第1步：获取最新数据...")
    try:
        latest = await asyncio.to_thread(
            fetcher.fetch_latest_data,
            symbol,
            market,
            force_refresh=True,
            save_db=True  # 自动保存到Snapshot
        )
        
        if latest:
            print(f"[Background] ✅ 最新数据获取成功: {symbol} = {latest.get('price')}")
        else:
            print(f"[Background] ⚠️ 最新数据获取失败: {symbol}")
    except Exception as e:
        print(f"[Background] ❌ 最新数据获取出错: {symbol} - {e}")
    
    # ========================================
    # 第二步：下载历史数据（不阻塞，即使失败也不影响）
    # ========================================
    print(f"[Background] 第2步：开始下载历史数据...")
    try:
        # 获取历史数据
        df = None
        if market == 'CN':
            df = await asyncio.to_thread(fetcher.fetch_cn_daily_data, symbol)
        elif market == 'HK':
            df = await asyncio.to_thread(fetcher.fetch_hk_daily_data, symbol)
        elif market == 'US':
            df = await asyncio.to_thread(fetcher.fetch_us_daily_data, symbol)
        
        if df is not None and not df.empty:
            # 保存到数据库
            count = await asyncio.to_thread(
                save_history_to_db, df, symbol, market
            )
            print(f"[Background] ✅ 历史数据下载成功: {symbol} - {count} 条记录")
        else:
            print(f"[Background] ⚠️ 历史数据为空: {symbol}")
            
    except Exception as e:
        print(f"[Background] ⚠️ 历史数据下载失败（不影响添加）: {symbol} - {e}")
        # 不抛出异常，失败了也不影响
    
    print(f"[Background] 完成处理: {symbol}")


def save_history_to_db(df: pd.DataFrame, symbol: str, market: str) -> int:
    """
    将历史数据DataFrame通过ETL流程保存到MarketDataDaily表
    使用Raw+ETL确保时间标准化被应用
    返回保存的记录数
    """
    if df is None or df.empty:
        return 0
    
    from models import RawMarketData
    from etl_service import ETLService
    import json
    
    db_symbol = normalize_symbol_db(symbol, market)
    
    # 标准化字段名：中文 -> 英文
    # A股数据通常有中文字段名，需要转换为ETL期待的英文名
    column_mapping = {
        '时间': 'date',
        '日期': 'date',
        '股票代码': 'code',
        '开盘': 'open',
        '收盘': 'close',
        '最高': 'high',
        '最低': 'low',
        '成交量': 'volume',
        '成交额': 'turnover',
        '涨跌额': 'change',
        '涨跌幅': 'pct_change',
        '振幅': 'amplitude',
        '换手率': 'turnover_rate'
    }
    
    # 重命名列
    df = df.rename(columns=column_mapping)
    
    # 确保有date列
    if 'date' not in df.columns:
        print(f"[Background] ⚠️ DataFrame缺少date列，跳过")
        return 0
    
    # 将DataFrame转换为JSON payload
    payload = df.to_dict('records')
    
    # 创建Raw记录
    with Session(engine) as session:
        raw = RawMarketData(
            source='history_download',
            symbol=db_symbol,
            market=market,
            period='1d',
            fetch_time=datetime.now(),
            payload=json.dumps(payload, ensure_ascii=False, default=str),
            processed=False
        )
        session.add(raw)
        session.commit()
        session.refresh(raw)
        raw_id = raw.id
    
    # 通过ETL处理（应用时间标准化）
    try:
        ETLService.process_raw_data(raw_id)
        
        # 统计保存的记录数
        with Session(engine) as session:
            from sqlmodel import select, func
            count = session.exec(
                select(func.count()).select_from(MarketDataDaily).where(
                    MarketDataDaily.symbol == db_symbol,
                    MarketDataDaily.market == market
                )
            ).one()
            return count
            
    except Exception as e:
        print(f"[Background] ETL处理历史数据失败: {e}")
        return 0

