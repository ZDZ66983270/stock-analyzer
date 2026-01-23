#!/usr/bin/env python3
"""
fetch_corporate_actions.py
分红与拆股数据获取脚本 (Dividend & Split Architecture v1.2)

功能：
1. 从 Yahoo Finance 获取分红 (Dividends) 和 拆股 (Splits) 数据。
2. 存入 DividendFact 和 SplitFact 表。
3. 支持全量回溯 (Full Backfill) 和 增量更新 (Incremental Update) 模式。

使用方法：
    python3 fetch_corporate_actions.py --mode full --asset TSLA
    python3 fetch_corporate_actions.py --mode full --all
    python3 fetch_corporate_actions.py --mode incremental --all
"""

import sys
import os
import argparse
import logging
from datetime import datetime, date, timedelta
from typing import List, Optional

import pandas as pd
import yfinance as yf
from sqlmodel import Session, select, func

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database import engine
from models import DividendFact, SplitFact, Watchlist, Index
from backend.symbols_config import get_yfinance_symbol

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CorporateActions")


def get_all_assets(session: Session) -> List[tuple]:
    """获取所有需要更新的资产 (Watchlist + Index)"""
    assets = []
    
    # Watchlist
    watchlist = session.exec(select(Watchlist)).all()
    for item in watchlist:
        assets.append((item.symbol, item.market))
        
    # Index (虽然指数通常无分红，但也可能有 split 或类似行为，且部分 ETF 可能在 Index 表)
    indices = session.exec(select(Index)).all()
    for item in indices:
        assets.append((item.symbol, item.market))
        
    return list(set(assets))


def fetch_and_save_actions(session: Session, asset_id: str, market: str, start_date: date, end_date: date, mode: str):
    """
    核心逻辑：拉取指定时间段的分红和拆股数据并保存
    """
    
    # 从 Canonical ID 提取纯代码 (HK:STOCK:00700 -> 00700)
    code = asset_id.split(':')[-1] if ':' in asset_id else asset_id
    
    # 1. 获取 Yahoo Symbol
    yf_symbol = get_yfinance_symbol(code, market)
    if not yf_symbol:
        logger.warning(f"⚠️ 无法转换符号: {asset_id}")
        return

    logger.info(f"🔄 Fetching {asset_id} ({yf_symbol}) [{start_date} -> {end_date}] Mode: {mode}")
    
    try:
        ticker = yf.Ticker(yf_symbol)
        
        # ---------------------------------------------------------
        # A. 分红 (Dividends)
        # ---------------------------------------------------------
        dividends = ticker.dividends
        
        # 过滤时间段
        mask_div = (dividends.index.date >= start_date) & (dividends.index.date <= end_date)
        divs_in_range = dividends.loc[mask_div]
        
        div_count = 0
        if not divs_in_range.empty:
            currency = ticker.info.get('currency', 'USD') # 尝试获取币种
            
            for ts, value in divs_in_range.items():
                if value <= 0: continue
                
                ex_date_str = ts.strftime('%Y-%m-%d')
                
                # 构建 DividendFact
                fact = DividendFact(
                    asset_id=asset_id,
                    ex_date=ex_date_str,
                    cash_dividend=float(value),
                    currency=currency,
                    is_special=False, # 暂不区分
                    source="yahoo"
                )
                
                # Upsert (Merge)
                # SQLModel 不直接支持 upsert, 这里使用 merge
                # 需确保 (asset_id, ex_date) 唯一约束生效
                existing = session.exec(
                    select(DividendFact).where(
                        DividendFact.asset_id == asset_id,
                        DividendFact.ex_date == ex_date_str
                    )
                ).first()
                
                if existing:
                    existing.cash_dividend = float(value)
                    existing.currency = currency
                    existing.source = "yahoo"
                    session.add(existing)
                else:
                    session.add(fact)
                
                div_count += 1
        
        # ---------------------------------------------------------
        # B. 拆股 (Splits)
        # ---------------------------------------------------------
        splits = ticker.splits
        
        mask_split = (splits.index.date >= start_date) & (splits.index.date <= end_date)
        splits_in_range = splits.loc[mask_split]
        
        split_count = 0
        if not splits_in_range.empty:
            for ts, value in splits_in_range.items():
                # value = split_factor (新股/旧股)
                # yahoo返回通常是 float, e.g., 5.0 (5:1 split)
                if value <= 0: continue
                
                eff_date_str = ts.strftime('%Y-%m-%d')
                
                fact = SplitFact(
                    asset_id=asset_id,
                    effective_date=eff_date_str,
                    split_factor=float(value),
                    raw_label=f"Split factor: {value}",
                    source="yahoo"
                )
                
                existing = session.exec(
                    select(SplitFact).where(
                        SplitFact.asset_id == asset_id,
                        SplitFact.effective_date == eff_date_str
                    )
                ).first()
                
                if existing:
                    existing.split_factor = float(value)
                    existing.source = "yahoo"
                    session.add(existing)
                else:
                    session.add(fact)
                    
                split_count += 1

        session.commit()
        if div_count > 0 or split_count > 0:
            logger.info(f"✅ Saved {asset_id}: {div_count} dividends, {split_count} splits.")
        else:
            logger.info(f"ℹ️  No actions for {asset_id} in range.")

    except Exception as e:
        logger.error(f"❌ Error fetching {asset_id}: {e}")
        session.rollback()


def backfill_full(session: Session, asset_id: str, market: str):
    """
    模式 A: 全量回溯
    - 忽略 max_date
    - 抓取完整历史
    """
    # 理论最早日期
    start_date = date(1900, 1, 1)
    end_date = date.today()
    
    # 可选：先清空该 asset 的历史数据？
    # SQLModel delete logic if needed. 
    # v1.2: "可先 DELETE ... 再重新拉取"
    # 但由于我们有 upsert 逻辑，也可以直接覆盖。为了纯净，DELETE 更佳。
    
    try:
        # 使用 standard delete statement
        from sqlmodel import delete
        session.exec(delete(DividendFact).where(DividendFact.asset_id == asset_id))
        session.exec(delete(SplitFact).where(SplitFact.asset_id == asset_id))
        session.commit()
    except Exception as e:
        logger.warning(f"Cleanup failed: {e}")
        session.rollback()
        
    fetch_and_save_actions(session, asset_id, market, start_date, end_date, mode="full")


def backfill_incremental(session: Session, asset_id: str, market: str, lookback_years: int = 5):
    """
    模式 B: 增量更新
    - 基于库中 max(ex_date) 回溯 n 年
    - 若无数据，自动降级为 Full Backfill
    """
    # 1. 查库中最后日期
    # Max of (max_div_date, max_split_date)
    last_div = session.exec(select(func.max(DividendFact.ex_date)).where(DividendFact.asset_id == asset_id)).one_or_none()
    last_split = session.exec(select(func.max(SplitFact.effective_date)).where(SplitFact.asset_id == asset_id)).one_or_none()
    
    last_date_str = None
    if last_div and last_split:
        last_date_str = max(last_div, last_split)
    elif last_div:
        last_date_str = last_div
    elif last_split:
        last_date_str = last_split
        
    if not last_date_str:
        logger.info(f"⚠️ No history found for {asset_id}, fallback to FULL backfill.")
        backfill_full(session, asset_id, market)
        return

    # 2. 计算 start_date
    last_date = datetime.strptime(last_date_str, "%Y-%m-%d").date()
    try:
        start_date = last_date.replace(year=last_date.year - lookback_years)
    except ValueError:
        start_date = last_date - timedelta(days=365 * lookback_years)
        
    end_date = date.today()
    
    fetch_and_save_actions(session, asset_id, market, start_date, end_date, mode="incremental")


def main():
    parser = argparse.ArgumentParser(description="Fetch Dividends & Splits")
    parser.add_argument("--mode", choices=["full", "incremental"], required=True, help="Backfill mode")
    parser.add_argument("--asset", help="Specific asset (Canonical ID), e.g., HK:STOCK:00700")
    parser.add_argument("--all", action="store_true", help="Process entire watchlist + index")
    
    args = parser.parse_args()
    
    if not args.asset and not args.all:
        print("❌ Must specify --asset or --all")
        sys.exit(1)
        
    with Session(engine) as session:
        targets = []
        if args.asset:
            # 单个资产，需猜测 market 或由用户提供 (这里简化，假设用户知道 ID)
            # 实际上我们的 ID 包含 market: CN:STOCK:600000
            # 解析 market
            parts = args.asset.split(':')
            if len(parts) >= 3:
                # "HK:STOCK:00700" -> market="HK"
                market = parts[0]
                targets.append((args.asset, market))
            else:
                print(f"❌ Invalid Canonical ID format: {args.asset}")
                sys.exit(1)
        else:
            targets = get_all_assets(session)
            
        print(f"🚀 Starting Corporate Actions Fetch. Mode: {args.mode}, Targets: {len(targets)}")
        
        for asset_id, market in targets:
            if args.mode == "full":
                backfill_full(session, asset_id, market)
            else:
                backfill_incremental(session, asset_id, market)
                
    print("✅ All Done.")


if __name__ == "__main__":
    main()
