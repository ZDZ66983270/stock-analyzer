"""
DataFetcher V2.0 (Refactored)
Strategy: yfinance First (Global Unified)
Markets: US / HK / CN
Author: Antigravity
Date: 2025-12-21
"""

import logging
import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import Dict, Optional, Any
import os

# Internal modules
from market_status import is_market_open
from rate_limiter import get_rate_limiter
from models import MarketSnapshot, MarketDataDaily
from database import engine 
from sqlmodel import Session, select
from etl_service import ETLService  # Re-use ETL logic

# Configure Logger
logger = logging.getLogger("DataFetcher")

class DataFetcher:
    """
    统一数据获取器 V2
    仅使用 yfinance 作为主数据源，极简架构。
    """
    
    def __init__(self):
        self.rate_limiter = get_rate_limiter()
        logger.info("DataFetcher V2 initialized (Strategy: yfinance First)")

    def fetch_latest_data(self, symbol: str, market: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        获取最新行情数据 (API / Cache)
        
        Args:
            symbol: 股票代码
            market: 市场 (US/HK/CN)
            force_refresh: 是否强制刷新 API
            
        Returns:
            Dict: 包含 price, change, pct_change 等字段的标准字典
        """
        
        # 1. 检查市场状态
        market_open = is_market_open(market)
        
        # 2. 策略判断
        # 如果市场关闭 且 不强制刷新 -> 尝试返回数据库缓存
        if not market_open and not force_refresh:
            cached = self._get_from_db_snapshot(symbol, market)
            if cached:
                logger.info(f"💾 Cached: {symbol} (Market Closed)")
                return cached

        # 3. 实时/强制获取 (API)
        return self._fetch_from_yfinance_unified(symbol, market)

    def _fetch_from_yfinance_unified(self, symbol: str, market: str) -> Optional[Dict[str, Any]]:
        """
        统一从 yfinance 获取数据 (覆盖所有市场)
        """
        yf_symbol = self._convert_to_yfinance_symbol(symbol, market)
        logger.info(f"🔄 API Fetch: {symbol} -> {yf_symbol}")
        
        # Rate Limit check
        self.rate_limiter.wait_if_needed(symbol, source="yfinance")
        
        try:
            # 使用 yfinance 获取最新数据 (period='5d' 以防假期/周末)
            # auto_adjust=True 拿到复权价
            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(period="5d", auto_adjust=True)
            
            if df.empty:
                logger.warning(f"⚠️ yfinance returned no data for {yf_symbol}")
                return None
                
            # 获取最新一行
            latest = df.iloc[-1]
            
            # 基础数据
            price = float(latest['Close'])
            open_p = float(latest['Open'])
            high = float(latest['High'])
            low = float(latest['Low'])
            volume = int(latest['Volume'])
            date_obj = latest.name # Index is Timestamp
            
            # 计算涨跌 (基于前一日)
            prev_close = 0.0
            change = 0.0
            pct_change = 0.0
            
            if len(df) >= 2:
                prev_row = df.iloc[-2]
                prev_close = float(prev_row['Close'])
                change = price - prev_close
                if prev_close > 0:
                    pct_change = (change / prev_close) * 100
            
            # 构造返回字典
            data = {
                "symbol": symbol,
                "market": market,
                "price": price,
                "change": round(change, 4),
                "pct_change": round(pct_change, 2),
                "open": open_p,
                "high": high,
                "low": low,
                "close": price,
                "prev_close": prev_close,
                "volume": volume,
                "date": date_obj.strftime("%Y-%m-%d %H:%M:%S"),
                "data_source": "yfinance",
                "timestamp": datetime.now().isoformat()
            }
            
            # 异步/同步 触发 ETL 保存流程 (为了更持久化)
            # 这里简单起见，我们直接返回Dict给前端，
            # 但同时也应该保存到 DB (Raw -> ETL) 以保持历史记录完整性
            # 将 DataFrame 保存到 RawMarketData，让 ETL 去处理持久化
            self._save_to_raw_pipeline(symbol, market, df)
            
            return data
            
        except Exception as e:
            logger.error(f"❌ API Error {symbol}: {e}")
            return None

    def _convert_to_yfinance_symbol(self, symbol: str, market: str) -> str:
        """
        标准化符号转换 (Smart Suffix)
        """
        # 从 Canonical ID 提取纯代码 (US:STOCK:AAPL -> AAPL)
        if ':' in symbol:
            symbol = symbol.split(':')[-1]
        
        s = symbol.strip().upper()
        if "." in s: return s # 已经有后缀
        
        if market == "US":
            return s
        elif market == "HK":
            # 纯数字则补齐5位 加 .HK
            if s.isdigit(): return f"{int(s):05d}.HK"
            # 指数
            if s == "HSI": return "^HSI"
            if s == "HSTECH": return "^HSTECH"
            return f"{s}.HK"
        elif market == "CN":
            if s.startswith("6"): return f"{s}.SS"
            if s.startswith("0") or s.startswith("3"): return f"{s}.SZ"
            if s.startswith("4") or s.startswith("8"): return f"{s}.BJ"
            
        return s

    def _get_from_db_snapshot(self, symbol: str, market: str) -> Optional[Dict]:
        """从 SQLite 快照表读取缓存"""
        try:
            with Session(engine) as session:
                snapshot = session.exec(
                    select(MarketSnapshot).where(
                        MarketSnapshot.symbol == symbol,
                        MarketSnapshot.market == market
                    )
                ).first()
                
                if snapshot:
                    return {
                        "symbol": snapshot.symbol,
                        "market": snapshot.market,
                        "price": snapshot.price,
                        "change": snapshot.change,
                        "pct_change": snapshot.pct_change,
                        "date": snapshot.timestamp, # 假设已是字符串
                        "data_source": "cache_db"
                    }
        except Exception as e:
            logger.error(f"DB Read Error: {e}")
        return None

    def _save_to_raw_pipeline(self, symbol: str, market: str, df: pd.DataFrame):
        """
        将数据注入标准 ETL 管道 (Raw -> ETL Service)
        """
        try:
            # 1. Format Payload
            df_reset = df.reset_index()
            # 映射列名 yfinance Title -> internal lowercase
            rename_map = {
                'Date': 'timestamp', 'Datetime': 'timestamp',
                'Open': 'open', 'High': 'high', 'Low': 'low', 
                'Close': 'close', 'Volume': 'volume'
            }
            df_reset = df_reset.rename(columns=rename_map)
            
            # Stringify date
            if 'timestamp' in df_reset.columns:
                df_reset['timestamp'] = df_reset['timestamp'].dt.strftime('%Y-%m-%d')
                
            records = df_reset.to_dict(orient='records')
            
            # 2. Save to Raw DB
            import json
            from models import RawMarketData
            
            payload = {
                "symbol": symbol, "market": market, "source": "yfinance",
                "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data": records
            }
            
            with Session(engine) as session:
                raw = RawMarketData(
                    symbol=symbol, market=market, source="yfinance",
                    period="smart", payload=json.dumps(payload), processed=False
                )
                session.add(raw)
                session.commit()
                # 触发 ETL
                ETLService.process_raw_data(raw.id)
                
        except Exception as e:
            logger.error(f"Save Pipeline Error: {e}")

# Global Instance
data_fetcher = DataFetcher()

def fetch_latest_data(symbol, market, force_refresh=False):
    """Module-level wrapper for backward compatibility"""
    return data_fetcher.fetch_latest_data(symbol, market, force_refresh)

def normalize_symbol_db(symbol: str, market: str) -> str:
    """
    Standardize symbol format for Database storage (DB-KEY).
    """
    symbol = symbol.strip().upper()
    if "." in symbol:
        base, suffix = symbol.split(".")
        if suffix == "SH": return f"{base}.SS"
        if suffix == "HK" and base.isdigit(): return f"{int(base):05d}.HK"
        return symbol
    if market == "HK" and symbol.isdigit(): return f"{int(symbol):05d}.HK"
    if market == "CN" and symbol.isdigit():
        if symbol.startswith("6"): return f"{symbol}.SS"
        else: return f"{symbol}.SZ"
    return symbol
