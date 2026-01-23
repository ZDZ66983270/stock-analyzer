#!/usr/bin/env python3
"""
PE 回填脚本 - 最终优化版
- 预加载财报数据
- 缓存股本数据
- 正确的 TTM 和汇率计算
"""
import sys
import time
from datetime import datetime
from sqlmodel import Session, select
import logging
from collections import defaultdict

# 添加后端路径
sys.path.append('backend')
from database import engine
from models import MarketDataDaily, Watchlist, FinancialFundamentals
from valuation_calculator import (
    get_ttm_net_income, 
    compute_ttm_eps_per_unit,
    get_shares_outstanding
)
from symbols_config import SYMBOLS_CONFIG, normalize_code

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("FinalBackfill")

# 配置
BATCH_SIZE = 100
MAX_RETRIES = 3
RETRY_DELAY = 1

# 全局缓存
SHARES_CACHE = {}


def preload_all_financials(session: Session, symbols: list) -> dict:
    """批量预加载所有股票的财报数据"""
    logger.info("📥 批量预加载财报数据...")
    
    financials_cache = defaultdict(list)
    
    all_financials = session.exec(
        select(FinancialFundamentals)
        .where(FinancialFundamentals.symbol.in_(symbols))
        .order_by(FinancialFundamentals.symbol, FinancialFundamentals.as_of_date.desc())
    ).all()
    
    for fin in all_financials:
        financials_cache[fin.symbol].append(fin)
    
    logger.info(f"✅ 预加载完成: {len(financials_cache)} 个股票的财报数据")
    return financials_cache


def get_shares_cached(symbol: str, market: str) -> float:
    """获取股本（带缓存）"""
    if symbol not in SHARES_CACHE:
        try:
            shares = get_shares_outstanding(symbol, market)
            SHARES_CACHE[symbol] = shares
        except Exception as e:
            logger.warning(f"获取 {symbol} 股本失败: {e}")
            SHARES_CACHE[symbol] = None
    return SHARES_CACHE[symbol]


def calculate_pe_fast(
    symbol: str,
    market: str,
    close_price: float,
    as_of_date: str,
    financials_cache: list
) -> dict:
    """快速计算 PE（使用缓存）"""
    try:
        # 1. 过滤有效财报
        valid_fins = [f for f in financials_cache if f.as_of_date <= as_of_date]
        if not valid_fins:
            return {'eps': None, 'pe': None}
        
        # 2. 计算 TTM 净利润
        ttm_income, fin_currency = get_ttm_net_income(valid_fins, as_of_date)
        if not ttm_income:
            return {'eps': None, 'pe': None}
        
        # 3. 获取股本（缓存）
        shares = get_shares_cached(symbol, market)
        if not shares:
            return {'eps': None, 'pe': None}
        
        # 4. 获取配置
        simple_code = normalize_code(symbol)
        config = SYMBOLS_CONFIG.get(simple_code, {})
        adr_ratio = config.get('adr_ratio', 1.0)
        
        market_currency_map = {'US': 'USD', 'HK': 'HKD', 'CN': 'CNY'}
        market_currency = market_currency_map.get(market, 'USD')
        
        # 5. 计算 EPS
        eps = compute_ttm_eps_per_unit(
            ttm_income,
            shares,
            fin_currency or market_currency,
            market_currency,
            adr_ratio
        )
        
        if not eps or eps == 0:
            return {'eps': None, 'pe': None}
        
        # 6. 计算 PE
        pe = close_price / eps
        return {'eps': eps, 'pe': pe}
        
    except Exception as e:
        logger.error(f"计算 PE 失败 ({symbol}): {e}")
        return {'eps': None, 'pe': None}


def commit_with_retry(session: Session, max_retries: int = MAX_RETRIES):
    """带重试的提交"""
    for attempt in range(max_retries):
        try:
            session.commit()
            return True
        except Exception as e:
            if 'database is locked' in str(e):
                if attempt < max_retries - 1:
                    logger.warning(f"  ⚠️ 数据库锁定，{RETRY_DELAY}秒后重试 ({attempt + 1}/{max_retries})")
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    logger.error(f"  ❌ 数据库锁定，已达最大重试次数")
                    session.rollback()
                    return False
            else:
                logger.error(f"  ❌ 提交失败: {e}")
                session.rollback()
                return False
    return False


def backfill_stock_pe(session: Session, symbol: str, market: str, financials_cache: dict):
    """回填单个股票的 PE"""
    logger.info(f"正在回填 {symbol}...")
    
    records = session.exec(
        select(MarketDataDaily)
        .where(
            MarketDataDaily.symbol == symbol,
            MarketDataDaily.market == market
        )
        .order_by(MarketDataDaily.timestamp)
    ).all()
    
    if not records:
        logger.warning(f"  ⚠️ 未找到历史数据")
        return 0
    
    financials = financials_cache.get(symbol, [])
    if not financials:
        logger.warning(f"  ⚠️ 未找到财报数据")
        return 0
    
    logger.info(f"  历史数据: {len(records)} 条, 财报: {len(financials)} 条")
    
    updated_count = 0
    batch_count = 0
    
    for i, rec in enumerate(records, 1):
        try:
            date_str = str(rec.timestamp)[:10]
            
            pe_metrics = calculate_pe_fast(
                symbol, market, rec.close, date_str, financials
            )
            
            if pe_metrics['eps'] is not None or pe_metrics['pe'] is not None:
                rec.eps = pe_metrics['eps']
                rec.pe = pe_metrics['pe']
                rec.updated_at = datetime.now()
                session.add(rec)
                updated_count += 1
                batch_count += 1
            
            if batch_count >= BATCH_SIZE:
                if commit_with_retry(session):
                    logger.info(f"  💾 已提交 {updated_count} 条 ({i}/{len(records)})")
                    batch_count = 0
                else:
                    logger.error(f"  ❌ 批次提交失败")
                    return updated_count
                
        except Exception as e:
            logger.error(f"  ❌ 处理 {date_str} 失败: {e}")
            continue
    
    if batch_count > 0:
        if commit_with_retry(session):
            logger.info(f"  💾 最终提交 {batch_count} 条")
    
    logger.info(f"  ✅ 完成: {updated_count}/{len(records)} 条")
    return updated_count


def main():
    """主函数"""
    logger.info("="*80)
    logger.info("🚀 开始 PE 回填（最终优化版）")
    logger.info("="*80)
    
    start_time = time.time()
    
    with Session(engine) as session:
        watchlist = session.exec(select(Watchlist)).all()
        stocks = [w for w in watchlist if 'STOCK' in w.symbol]
        
        logger.info(f"\n找到 {len(stocks)} 只股票")
        logger.info(f"批次大小: {BATCH_SIZE} 条/批\n")
        
        # 预加载财报
        symbols = [s.symbol for s in stocks]
        financials_cache = preload_all_financials(session, symbols)
        
        # 预加载股本（避免每条记录都调用 API）
        logger.info("📥 预加载股本数据...")
        for i, stock in enumerate(stocks, 1):
            logger.info(f"  [{i}/{len(stocks)}] 获取 {stock.symbol} 股本...")
            get_shares_cached(stock.symbol, stock.market)
        logger.info("✅ 股本预加载完成\n")
        
        # 逐个回填
        total_updated = 0
        for i, stock in enumerate(stocks, 1):
            logger.info(f"\n[{i}/{len(stocks)}] {stock.symbol}")
            
            try:
                count = backfill_stock_pe(session, stock.symbol, stock.market, financials_cache)
                total_updated += count
                
                elapsed = time.time() - start_time
                avg_time = elapsed / i
                remaining = avg_time * (len(stocks) - i)
                logger.info(f"  ⏱️  已用时: {elapsed/60:.1f}分钟, 预计剩余: {remaining/60:.1f}分钟")
                    
            except Exception as e:
                logger.error(f"  ❌ 回填失败: {e}")
                continue
    
    elapsed = time.time() - start_time
    logger.info("\n" + "="*80)
    logger.info(f"✅ 回填完成！共更新 {total_updated} 条记录")
    logger.info(f"⏱️  总用时: {elapsed/60:.1f} 分钟")
    logger.info("="*80)


if __name__ == "__main__":
    main()
