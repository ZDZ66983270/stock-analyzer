"""
ETL Service (数据清洗与入库服务)
=============================

功能说明:
1. 将 RawMarketData (JSON 格式) 清洗并转换为结构化的 MarketDataDaily (历史) 和 MarketSnapshot (快照)。
2. 负责时间归一化、异常数据过滤（如盘中错误快照）以及核心指标的初步计算。

核心逻辑与公式:
1. **时间归一化 (Time Normalization)**:
   - 日线数据: 若时间为 00:00:00，则自动归一化为收盘时间。
   - 公式: `Target_Time = Date + Market_Close_Time (US:16:00, HK:16:00, CN:15:00)`
2. **价格指标计算**:
   - 涨跌额 (Change): `Price - Previous_Close`
   - 涨跌幅 (Pct Change): `(Change / Previous_Close) * 100`
   - 说明: `Previous_Close` 优先选用数据源提供的字段，若缺失则从数据库查询上一交易日记录。
3. **快照更新策略**:
   - 盘中时段: 更新 `MarketSnapshot` 的最新价 and 实时涨跌幅，不写入 `MarketDataDaily`。
   - 盘后时段: 待 ETL 完成后，用 `MarketDataDaily` 的标准收盘数据刷新 `MarketSnapshot`。

作者: Antigravity
日期: 2026-01-23
"""

import json
import pandas as pd
import logging
from datetime import datetime, time
from sqlmodel import Session, select, delete
from database import engine
from models import RawMarketData, MarketDataDaily, MarketSnapshot
from market_status import is_market_open
from symbols_config import get_canonical_symbol  # ✅ 导入符号规范化

logger = logging.getLogger("ETLService")

class ETLService:
    
    @staticmethod
    def process_raw_data(raw_id: int):
        """
        Main Pipeline: Raw -> Clean -> Prod
        """
        with Session(engine) as session:
            # 1. Extract
            raw_record = session.get(RawMarketData, raw_id)
            if not raw_record:
                logger.error(f"Raw record {raw_id} not found")
                return
            
            if raw_record.processed:
                logger.info(f"Raw record {raw_id} already processed")
                return

            # ✅ 2. 符号规范化：800000→HSI, 800700→HSTECH
            original_symbol = raw_record.symbol
            canonical_symbol = get_canonical_symbol(original_symbol)
            if canonical_symbol != original_symbol:
                logger.info(f"符号规范化: {original_symbol} → {canonical_symbol}")
                raw_record.symbol = canonical_symbol

            try:
                payload_data = json.loads(raw_record.payload)
                
                # Handle wrapped payload (e.g. {'symbol':..., 'data': [...]})
                if isinstance(payload_data, dict) and 'data' in payload_data:
                    data_list = payload_data['data']
                elif isinstance(payload_data, list):
                    data_list = payload_data
                else:
                    logger.error(f"Unknown payload format for {raw_id}")
                    return

                if not data_list:
                    raw_record.processed = True
                    session.add(raw_record)
                    session.commit()
                    return

                df = pd.DataFrame(data_list)
                
                # 2. Transform & Load - 基于数据类型和市场状态判断
                market_is_open = is_market_open(raw_record.market)
                
                if raw_record.period == '1d':
                    # 日线数据：始终尝试处理，内部会判定日期是否已定型
                    logger.info(f"Processing 1d record: {raw_record.symbol}")
                    ETLService._process_daily(session, df, raw_record)
                else:
                    # 非日线数据（分钟/实时）：不保存Daily
                    logger.info(f"Intraday/Other data (period={raw_record.period}): skipping Daily table")
                
                # 3. 总是更新Snapshot（最新行情）
                ETLService._update_snapshot(session, df, raw_record, market_is_open)
                
                # Mark Done
                raw_record.processed = True
                session.add(raw_record)
                session.commit()
                logger.info(f"✅ ETL Complete for Raw {raw_id} ({raw_record.symbol})")
                
            except Exception as e:
                logger.error(f"ETL Failed for {raw_id}: {e}")
                raw_record.error_log = str(e)
                session.add(raw_record)
                session.commit()

    @staticmethod
    def _process_daily(session: Session, df: pd.DataFrame, meta: RawMarketData):
        """
        Clean Daily Data:
        1. Time Normalization: 00:00:00 -> Market Close Time
        2. Bad Data Filter: Reject 15:59 intraday snapshots
        3. US Market Open Filter: Remove today's data (real-time price with wrong timestamp)
        4. Indicator Calc: Fill missing Change
        """
        # ✅ 统一使用timestamp作为时间字段
        # Field normalizer将"日期"映射为"timestamp"，ETL内部也统一使用timestamp
        # 只在保存到DB时才映射为'date'（兼容现有schema）
        
        # 兼容旧数据：如果只有date没有timestamp，复制过来
        if 'date' in df.columns and 'timestamp' not in df.columns:
            df['timestamp'] = df['date']
        
        # Ensure timestamp type - 支持字符串和毫秒timestamp
        if 'timestamp' in df.columns:
            # 智能判断：字符串用默认解析，数值用unit='ms'
            if df['timestamp'].dtype == 'object':  # 字符串格式 (CN/HK)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            else:  # 数值格式 (US毫秒timestamp)
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        else:
            raise KeyError("'timestamp' column not found in DataFrame")
        
        # 删除US开盘过滤（冗余逻辑）
        # ETL不应判断市场状态，应由调用方决定
        
        # Sort for calculation
        df = df.sort_values('timestamp')
        
        # Pre-fetch last close from DB for continuity
        # ✅ 修复：查询小于当前批次最小日期的记录，避免查到当天已保存的记录
        last_close = None
        if not df.empty:
            # 获取当前批次的最小日期
            min_timestamp_in_batch = df['timestamp'].min()
            if pd.notna(min_timestamp_in_batch):
                min_date_str = min_timestamp_in_batch.strftime('%Y-%m-%d %H:%M:%S')
                
                stmt = select(MarketDataDaily).where(
                    MarketDataDaily.symbol == meta.symbol,
                    MarketDataDaily.market == meta.market,
                    MarketDataDaily.timestamp < min_date_str
                ).order_by(MarketDataDaily.timestamp.desc()).limit(1)
                
                prev_rec = session.exec(stmt).first()
                if prev_rec:
                    last_close = prev_rec.close
                    logger.info(f"✅ Pre-fetched last_close={last_close} for {meta.symbol} (before {min_date_str})")


        record_count = 0  # ✅ 批量提交计数器
        
        # 🧪 获取市场当前日期用于过滤盘中未定型数据
        from market_status import get_market_time, is_market_open, get_market_close_time
        market_now = get_market_time(meta.market)
        market_today = market_now.date()
        market_open = is_market_open(meta.market)
        
        market_close_time = get_market_close_time(meta.market)
        
        # --- ITERATE: Process Each Row ---
        # last_close is already initialized above, no need to reset here
        for _, row in df.iterrows():
            orig_time = row['timestamp']
            
            # --- 🛡️ GUARD: Only skip "Today" if the market is NOT FINISHED ---
            # Define "Finished": current_time >= close_time OR market is forcibly closed and passed date
            # We are conservative: If date is TODAY, and current_time < close_time, SKIP.
            # Even if market is technically "closed" for lunch, we shouldn't finalize daily data yet.
            if orig_time.date() == market_today and meta.market != 'WORLD':
                current_time = market_now.time()
                is_unfinished_day = False
                
                # Check 1: Is market currently open?
                if market_open:
                    is_unfinished_day = True
                
                # Check 2: Is it before closing time? (e.g. Lunch break or Pre-market)
                elif current_time < market_close_time:
                    is_unfinished_day = True
                
                if is_unfinished_day:
                    logger.info(f"⏭️ Skipping Daily storage for {meta.symbol} on {orig_time.date()} (Market OPEN or PRE-CLOSE)")
                    continue
            
            h, m, s = orig_time.hour, orig_time.minute, orig_time.second
                
            # --- TRANSFORM: Time Normalization ---
            # Rule: 00:00:00 -> Market Close Time
            # For daily data from sources like AkShare/yfinance, they often return 00:00:00
            # We need to normalize it to market close time
            target_time = orig_time
            has_time = (h != 0 or m != 0 or s != 0)
            
            # Normalize if time is 00:00:00 (daily data)
            if not has_time:
                if meta.market == 'US':
                    # Set to 16:00 US Eastern
                    target_time = orig_time.replace(hour=16, minute=0, second=0)
                elif meta.market == 'HK':
                    # Set to 16:00 HK Time
                    target_time = orig_time.replace(hour=16, minute=0, second=0)
                elif meta.market == 'CN':
                    # Set to 15:00 Beijing Time
                    target_time = orig_time.replace(hour=15, minute=0, second=0)
            
            # --- CALC: Indicators ---
            close_p = float(row['close'])
            change_p = row.get('change')
            pct_p = row.get('pct_change')
            prev_close_from_row = row.get('prev_close')
            
            # ✅ 混合方案：如果数据源没有提供prev_close，从数据库查询
            if prev_close_from_row is None and close_p is not None:
                try:
                    # 准备日期字符串用于查询
                    target_time = orig_time
                    has_time = (orig_time.hour != 0 or orig_time.minute != 0 or orig_time.second != 0)
                    if not has_time:
                        if meta.market == 'US':
                            target_time = orig_time.replace(hour=16, minute=0, second=0)
                        elif meta.market == 'HK':
                            target_time = orig_time.replace(hour=16, minute=0, second=0)
                        elif meta.market == 'CN':
                            target_time = orig_time.replace(hour=15, minute=0, second=0)
                    
                    current_date_str = target_time.strftime('%Y-%m-%d %H:%M:%S')
                    
                    # 查询前一条记录
                    prev_record = session.exec(
                        select(MarketDataDaily)
                        .where(MarketDataDaily.symbol == meta.symbol)
                        .where(MarketDataDaily.market == meta.market)
                        .where(MarketDataDaily.timestamp < current_date_str)
                        .order_by(MarketDataDaily.timestamp.desc())
                    ).first()
                    
                    if prev_record and prev_record.close:
                        prev_close_from_row = prev_record.close
                        logger.info(f"✅ 从数据库补全prev_close: {meta.symbol} {current_date_str} prev_close={prev_close_from_row}")
                except Exception as e:
                    logger.warning(f"查询prev_close失败: {e}")
            
            # Calculate if missing (None), don't recalculate if explicitly 0
            # Use prev_close from row (original or补全from DB) or last_close from iteration
            effective_prev_close = prev_close_from_row if prev_close_from_row is not None else last_close
            
            if (change_p is None or pct_p is None) and effective_prev_close:
                 change_p = close_p - effective_prev_close
                 pct_p = (change_p / effective_prev_close) * 100
                 logger.info(f"ETL Calculated: change={change_p:.2f}, pct={pct_p:.2f}% (prev_close={effective_prev_close:.2f})")
            
            # Prepare Model
            db_date_str = target_time.strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"ETL Saving {meta.symbol}: target_time={target_time} -> db_date_str={db_date_str} (has_time={has_time})")
            
            # Check exist (Upsert logic)
            # For simplicity in this session, we query-check. In prod, use ON CONFLICT.
            existing = session.exec(select(MarketDataDaily).where(
                MarketDataDaily.symbol == meta.symbol,
                MarketDataDaily.market == meta.market,
                MarketDataDaily.timestamp == db_date_str
            )).first()
            
            if existing:
                # Update
                existing.close = close_p
                existing.change = change_p
                existing.pct_change = pct_p
                existing.prev_close = effective_prev_close  # ✅ 修复：也要更新prev_close
                existing.volume = row.get('volume', existing.volume)
                session.add(existing)
            else:
                # Insert
                # ✅ 修复：处理 Trusts/Mutual Funds 只有收盘价的情况 (Open/High/Low may be None/NaN)
                def clean_val(val, fallback):
                    if pd.isna(val) or val is None: return fallback
                    return val
                
                safe_open = clean_val(row.get('open'), close_p)
                safe_high = clean_val(row.get('high'), close_p)
                safe_low = clean_val(row.get('low'), close_p)

                # Insert
                new_rec = MarketDataDaily(
                    symbol=meta.symbol,
                    market=meta.market,
                    timestamp=db_date_str,  # ✅ 修复：使用timestamp而非date
                    open=safe_open,
                    high=safe_high,
                    low=safe_low,
                    close=close_p,
                    volume=row.get('volume'),
                    change=change_p,
                    pct_change=pct_p,
                    prev_close=effective_prev_close,
                    updated_at=datetime.now()
                )
                session.add(new_rec)
            
            # ✅ 批量提交优化: 每100条提交一次
            record_count += 1
            if record_count % 100 == 0:
                session.commit()
                logger.info(f"💾 Batch commit: {record_count} records processed")
            
            # Update last_close for next iteration
            last_close = close_p
        
        # ✅ 最后提交剩余记录
        if record_count % 100 != 0:
            session.commit()
            logger.info(f"💾 Final commit: {record_count} total records")
            
        logger.info(f"Daily ETL: Parsed {len(df)} rows, Upserted {record_count} rows.")


    # MarketDataMinute已废弃，分钟数据处理暂时不需要
    # 如需恢复，可以重新实现分钟级数据存储
    
    @staticmethod
    def _update_snapshot(session: Session, df: pd.DataFrame, meta: RawMarketData, is_market_open: bool):
        """
        更新MarketSnapshot（最新行情）
        盘中：使用分钟数据最新价格
        盘后：从Daily表读取收盘价
        """
        try:
            if is_market_open:
                # 盘中：使用分钟数据
                if df.empty:
                    return
                
                latest_row = df.iloc[-1]
                
                # 计算涨跌幅（基于前一日收盘）
                prev_daily = session.exec(
                    select(MarketDataDaily)
                    .where(MarketDataDaily.symbol == meta.symbol)
                    .order_by(MarketDataDaily.timestamp.desc())
                    .limit(1)
                ).first()
                
                prev_close = prev_daily.close if prev_daily else None
                current_price = float(latest_row.get('close', 0))
                change = current_price - prev_close if prev_close else 0
                pct_change = (change / prev_close * 100) if prev_close else 0
                
                snapshot_data = {
                    'price': current_price,
                    'open': float(latest_row.get('open', 0)),
                    'high': float(latest_row.get('high', 0)),
                    'low': float(latest_row.get('low', 0)),
                    'volume': int(latest_row.get('volume', 0)),
                    'change': change,
                    'pct_change': pct_change,
                    'prev_close': prev_close,
                    'date': str(latest_row.get('date', '')),
                    'data_source': 'intraday',
                    'updated_at': datetime.now()
                }
                
                logger.info(f"Updating Snapshot from intraday data: {meta.symbol} = {current_price}")
                
            else:
                # 盘后：从Daily表读取已经计算好的数据
                if df.empty:
                    logger.warning(f"Empty dataframe for {meta.symbol}, skipping snapshot update")
                    return
                
                latest_row = df.iloc[-1]
                
                # ✅ 修复：查询Daily表的最新记录，使用其中已经计算好的prev_close/change/pct_change
                latest_daily = session.exec(
                    select(MarketDataDaily)
                    .where(MarketDataDaily.symbol == meta.symbol)
                    .where(MarketDataDaily.market == meta.market)
                    .order_by(MarketDataDaily.timestamp.desc())
                    .limit(1)
                ).first()
                
                # 优先使用Daily表中已经计算好的值
                if latest_daily:
                    current_price = float(latest_daily.close)
                    prev_close = latest_daily.prev_close
                    change = latest_daily.change if latest_daily.change is not None else 0.0
                    pct_change = latest_daily.pct_change if latest_daily.pct_change is not None else 0.0
                    logger.info(f"从Daily表读取: {meta.symbol} close={current_price}, prev_close={prev_close}, change={change:.2f}, pct={pct_change:+.2f}%")
                else:
                    # Fallback：Daily表没有数据，从DataFrame计算
                    current_price = float(latest_row.get('close', 0))
                    prev_close = None
                    change = 0.0
                    pct_change = 0.0
                    logger.warning(f"Daily表无数据，使用DataFrame: {meta.symbol} = {current_price}")
                
                snapshot_data = {
                    'price': current_price,
                    'open': float(latest_row.get('open', 0)),
                    'high': float(latest_row.get('high', 0)),
                    'low': float(latest_row.get('low', 0)),
                    'volume': int(latest_row.get('volume', 0)),
                    'change': change,
                    'pct_change': pct_change,
                    'prev_close': prev_close,
                    'timestamp': latest_daily.timestamp if latest_daily else str(latest_row.get('timestamp', '')),  # ✅ 使用timestamp
                    'data_source': 'daily_close',
                    'updated_at': datetime.now()
                }
                
                logger.info(f"Updating Snapshot from daily data: {meta.symbol} = {current_price} (change={change:.2f}, {pct_change:+.2f}%)")
            
            # Upsert Snapshot
            snapshot = session.exec(
                select(MarketSnapshot)
                .where(
                    MarketSnapshot.symbol == meta.symbol,
                    MarketSnapshot.market == meta.market
                )
            ).first()
            
            if snapshot:
                # 更新现有记录
                for key, value in snapshot_data.items():
                    setattr(snapshot, key, value)
            else:
                # 创建新记录
                snapshot = MarketSnapshot(
                    symbol=meta.symbol,
                    market=meta.market,
                    **snapshot_data
                )
                session.add(snapshot)
            
            session.commit()
            logger.info(f"✅ Snapshot updated: {meta.symbol}")
            
        except Exception as e:
            logger.error(f"Failed to update snapshot for {meta.symbol}: {e}")

