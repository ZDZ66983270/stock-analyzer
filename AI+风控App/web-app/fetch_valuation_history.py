"""
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# ⚠️ WARNING: CORE VALUATION LOGIC - DO NOT MODIFY WITHOUT APPROVAL
# ⚠️ WARNING: CORE VALUATION LOGIC - DO NOT MODIFY WITHOUT APPROVAL
# ⚠️ WARNING: CORE VALUATION LOGIC - DO NOT MODIFY WITHOUT APPROVAL
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

Valuation History Fetcher (历史估值获取器)
========================================

功能说明:
1. **全市场覆盖**: 为 A股 (CN), 港股 (HK), 美股 (US) 提供统一的估值指标获取方案。
2. **多源融合**: 结合官方数据源 (AkShare, Futu) 和商业数据源 (FMP, Yahoo) 以及本地推导能力。
3. **指标覆盖**: 市盈率 (PE TTM), 静态市盈率 (PE Static), 市净率 (PB), 股息率 (Dividend Yield)。

模块架构:
========================================

I. Core Fetchers (核心获取器)
----------------------------------------
负责从外部 API获取原始数据，处理网络请求、鉴权和基础清洗。

| 区域 | 函数名 | 数据源 | 关键特性 |
| :--- | :--- | :--- | :--- |
| **CN** | `fetch_cn_valuation_history` | AkShare (`stock_value_em`) | 东方财富官方数据，包含 PE-TTM/Static, PB。 |
| **CN** | `fetch_cn_dividend_yield` | AkShare (`stock_fhps`) | 复杂逻辑：基于"报告期"计算 TTM 分红，除以最新收盘价。 |
| **HK** | `fetch_hk_valuation_futu` | **Futu OpenD** | **核心逻辑**。通过 Socket 连接本地 OpenD，获取精准的历史 PE/PB。包含自动重试和连接保活。 |
| **HK** | `fetch_hk_dividend_yield` | Yahoo Finance | 补充 Futu 缺失的实时股息率字段。 |
| **HK** | `fetch_hk_valuation_baidu` | Baidu Stock | (Legacy) 仅作为 Futu 不可用时的备选方案。 |
| **US** | `fetch_us_valuation_fmp` | **FMP Cloud** | 商业级 API，提供长达 30 年的日线级 PE/PB 历史。 |
| **US** | `fetch_us_valuation_yf` | Yahoo Finance | (Realtime) 仅用于获取美股盘中/收盘后的瞬时快照。 |

II. Data Persistence & Alignment (持久化与对齐)
----------------------------------------
负责将多源异构数据写入 `MarketDataDaily` 表，核心难题是解决**时间戳对齐**。

- **Futu 对齐逻辑** (`save_hk_valuation_futu`):
  Futu K线时间戳通常为 `00:00:00`，而本地数据库可能存储为 `16:00:00` (收盘时间)。
  算法支持 `+/- 5 Days` 的模糊匹配，优先匹配 exact match，其次寻找最近的交易日，确保估值数据能挂载到正确的价格记录上。

- **增量更新**:
  所有保存函数均设计为 Idempotent (幂等)，支持反复运行。仅更新缺失或变动的字段 (PE/PB)，不破坏现有的 OHLCV 数据。

III. US Market Logic & ADR Handling (美股核心逻辑)
----------------------------------------
美股估值获取包含复杂的**混合策略 (Hybrid Strategy)** 和 **ADR 货币对齐**。

1. **混合获取策略**:
   - 优先使用 `FMP Cloud` API 获取长周期的历史每日 PE。
   - 实时数据使用 `Yahoo Finance` 补充。
   - 当 API 缺失时，回退到**本地推导引擎**。

2. **ADR 货币自动转换 (Currency Alignment)**
   - **场景**: 非美企业在美国上市 (ADR)，财报货币通常为本币 (CNY, TWD, JPY)，而股价为美元 (USD)。
   - **逻辑**: 若检测到 `EPS Currency != Price Currency`，自动应用静态汇率进行转换。
   - **支持货币对**:
     - `TWD -> USD` (例如: TSM 台积电)
     - `CNY -> USD` (例如: BABA 阿里巴巴)
     - `HKD -> USD` (例如: 香港公司 ADR)
     - `JPY -> USD` (例如: 日本公司 ADR)
   - *注意*: 目前使用静态汇率表，长期回测可能存在精度偏差。

IV. Generic Derivation Engine (通用推导引擎)
----------------------------------------
提供底层的数学工具，用于在数据稀疏或缺失时填补估值空白。

1. **PE TTM 推导算法**:
   - `Daily PE = Daily Close / Latest EPS (FFill)`
   - 智能识别财报频度 (Annual vs Quarterly)，自动执行 Rolling Sum (4 quarters) 计算 TTM EPS。

2. **稀疏点插值算法**:
   - 用于处理仅有年度数据的情况。
   - 算法: 先反推 Implied EPS，线性插值生成的连续 EPS 曲线，再除以每日股价得到平滑 PE。

V. Interactive CLI & Configuration
----------------------------------------
内置完整的终端交互界面 (`Config`, `print_menu`)，同时支持 Headless 模式。

1. **交互模式 (Default)**:
   - 运行 `python fetch_valuation_history.py` 进入菜单。
   - 支持按市场 (CN/HK/US) 批量筛选下载。

2. **Headless 模式 (Single Asset)**:
   - 支持 `--symbol` 参数直接指定资产 ID，跳过菜单 (e.g. `--symbol HK:STOCK:00700`)。
   - 适用于调试或被其他脚本调用。

VI. Operational Details (运行细节)
----------------------------------------
- **Snapshot Hot-Update (港股)**: 
  Futu 逻辑包含"热更新"机制。在下载历史数据的同时，会拉取最新的即时快照 (Snapshot) 并覆盖当日的 PE TTM，确保盘中数据的实时性。
- **API Throttling**: 
  内置 `sleep(0.5)` 防止触发外部 API (YFinance/FMP) 的速率限制。
- **History Limits**: 
  美股 FMP 接口默认获取最近 20 年 (`limit=20`) 的年度数据，以优化性能。

前置条件:
1. **Futu OpenD**: 必须在本地 127.0.0.1:11111 运行并登录 (针对港股)。
2. **FMP API Key**: 需配置有效的 Financial Modeling Prep Key (针对美股历史)。
3. **Database**: `MarketDataDaily` 表需预先填充 OHLCV 价格数据。


作者: Antigravity
日期: 2026-01-23
"""
import sys
sys.path.append('backend')

import akshare as ak
import pandas as pd
import requests
import json
import argparse
import numpy as np
from datetime import datetime, timedelta
from sqlmodel import Session, select
from backend.database import engine
from backend.models import Watchlist, MarketDataDaily
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FetchValuation")


def fetch_cn_valuation_history(symbol: str, asset_type: str = 'STOCK') -> pd.DataFrame:
    """
    获取A股历史估值数据
    使用 AkShare stock_value_em() 接口
    
    参数:
        symbol: Canonical ID (如 CN:STOCK:600519)
        asset_type: 资产类型 (STOCK, INDEX)
    """
    try:
        # 1. 检查类型。指数暂不支持通过此接口获取估值
        if asset_type == 'INDEX':
            logger.info(f"  ⏭️  指数暂无个股式估值接口，跳过: {symbol}")
            return None
            
        # 从 Canonical ID 提取纯代码 (CN:STOCK:600519 -> 600519)
        code = symbol.split(':')[-1] if ':' in symbol else symbol
        
        logger.info(f"  📥 获取A股估值数据: {code}")
        
        # 调用 AkShare 接口 (仅支持个股)
        df = ak.stock_value_em(symbol=code)
        
        if df is None or df.empty:
            logger.warning(f"  ⚠️  无估值数据: {code}")
            return None
        
        logger.info(f"  ✅ 获取 {len(df)} 条估值记录")
        return df
        
    except Exception as e:
        logger.error(f"  ❌ 获取A股估值数据失败 {symbol}: {e}")
        return None


def fetch_hk_valuation_baidu_direct(code: str, indicator: str = "市盈率(TTM)") -> pd.DataFrame:
    """
    直接调用百度股市通 OpenData 接口获取港股历史估值数据
    
    参数:
        code: 5位港股代码 (如 '00700')
        indicator: '市盈率(TTM)' 或 '市净率'
    """
    try:
        url = "https://gushitong.baidu.com/opendata"
        params = {
            "openapi": "1",
            "dspName": "iphone",
            "tn": "tangram",
            "client": "app",
            "query": indicator,
            "code": code,
            "resource_id": "51171",
            "srcid": "51171",
            "market": "hk",
            "tag": indicator,
            "skip_industry": "1",
            "chart_select": "全部",
            "finClientType": "pc"
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        logger.info(f"  🌐 调用百度接口获取 {indicator}: {code}")
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"  ❌ 接口响应错误: {response.status_code}")
            return None
            
        data = response.json()
        
        # 复杂 JSON 路径提取
        # Result[0].DisplayData.resultData.tplData.result.chartInfo[0].body
        try:
            results = data.get("Result", [])
            if not results:
                return None
            
            display_data = results[0].get("DisplayData", {}).get("resultData", {}).get("tplData", {}).get("result", {})
            chart_info = display_data.get("chartInfo", [])
            
            if not chart_info:
                return None
                
            body = chart_info[0].get("body", [])
            
            if not body:
                return None
            
            # body 格式为 [[date, value], ...]
            df = pd.DataFrame(body, columns=['date', 'value'])
            
            # 转换日期和数值
            df['date'] = pd.to_datetime(df['date'])
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            
            return df
            
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"  ❌ 解析结果失败: {e}")
            return None
            
    except Exception as e:
        logger.error(f"  ❌ 调用百度接口异常: {e}")
        return None


def fetch_cn_dividend_yield(symbol: str) -> float:
    """
    获取A股最新股息率
    计算方式: Sum(最近一年每股分红) / 当前股价
    使用 AkShare: stock_fhps_detail_em (分红) + stock_zh_a_hist (股价)
    """
    try:
        import akshare as ak
        from datetime import datetime, timedelta
        
        # 从 Canonical ID 提取纯代码 (CN:STOCK:600030 -> 600030)
        code = symbol.split(':')[-1] if ':' in symbol else symbol
        
        logger.info(f"  📊 获取A股股息率: {code}")
        
        # 1. 获取当前股价
        try:
            # 获取最近几天的K线，取最新收盘价
            # 使用 qfq (前复权) 比较合适? 不，股息率通常用不复权价格计算实时的。
            # 直接取最近一条记录
            start_dt = (datetime.now() - timedelta(days=10)).strftime("%Y%m%d")
            price_df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start_dt, adjust="qfq")
            if price_df is None or price_df.empty:
                logger.warning(f"  ⚠️  无法获取股价: {code}")
                return None
            current_price = float(price_df.iloc[-1]['收盘'])
        except Exception as e:
            logger.warning(f"  ⚠️  获取股价失败: {e}")
            return None
            
        if current_price <= 0:
            return None

        # 2. 获取分红配送详情
        df = ak.stock_fhps_detail_em(symbol=code)
        
        if df is None or df.empty:
            return None
        
        if '现金分红-现金分红比例' not in df.columns:
            logger.warning("  ⚠️  找不到分红比例列")
            return None

        # 3. 使用"报告期"计算TTM (最近一年宣告分红)
        # 避免因除权除息日变动导致 "刚过365天就归零" 的情况
        report_col = '报告期'
        if report_col not in df.columns:
             # 回退到旧逻辑 (除权日)
             logger.warning("  ⚠️  找不到报告期列, 回退到除权日逻辑")
             
             # ... (Fallback if needed, but for now we trust Report Date usually exists)
             date_col = '除权除息日'
             if date_col not in df.columns: return None
             df[date_col] = pd.to_datetime(df[date_col], errors='coerce').dt.date
             recent_dividends = df[df[date_col] >= (datetime.now().date() - timedelta(days=365))]
        else:
            df[report_col] = pd.to_datetime(df[report_col], errors='coerce').dt.date
            max_report_date = df[report_col].max()
            
            if pd.isna(max_report_date):
                return 0.0
                
            # 截断日期: 最新报告期 - 1年
            # 例如: 最新 2024-12-31. 截断 2023-12-31.
            # 我们需要 > 2023-12-31 的记录 (即 2024-06, 2024-12).
            cutoff_date = max_report_date - timedelta(days=365)
            
            recent_dividends = df[df[report_col] > cutoff_date]
        
        if recent_dividends.empty:
            logger.info(f"  ℹ️  过去一年无分红宣告 (Based on Report Date)")
            return 0.0
            
        # 4. 计算总每股分红 (DPS)
        # 列名: '现金分红-现金分红比例' (每10股派多少元)
        sum_per_10 = recent_dividends['现金分红-现金分红比例'].sum()
        total_dps = sum_per_10 / 10.0

        # 5. 计算股息率
        dividend_yield = (total_dps / current_price) * 100
        
        logger.info(f"  ✅ TTM股息率(宣告): {dividend_yield:.2f}% (DPS: {total_dps}, Price: {current_price})")
        return dividend_yield
        
    except Exception as e:
        logger.warning(f"  ⚠️  获取A股股息率失败 {symbol}: {e}")
        return None


def fetch_hk_dividend_yield(symbol: str) -> float:
    """
    获取港股最新股息率
    使用yfinance
    """
    try:
        import yfinance as yf
        # 从 Canonical ID 提取纯代码 (HK:STOCK:00700 -> 00700)
        code = symbol.split(':')[-1] if ':' in symbol else symbol
        
        # 转换为yfinance格式 (00700 -> 0700.HK)
        # yfinance 需要4位数字代码 (例如 0700.HK)
        clean_code = code.lstrip('0')
        if len(clean_code) < 4:
            clean_code = clean_code.zfill(4)
        yf_symbol = f"{clean_code}.HK"
        
        logger.info(f"  📊 获取港股股息率: {yf_symbol}")
        
        ticker = yf.Ticker(yf_symbol)
        
        # 直接从 info 获取 (用户倾向于 Direct Fetch)
        info = ticker.info
        dividend_yield = info.get('dividendYield')
        
        if dividend_yield is not None:
             # yfinance 返回的就是百分比数值 (e.g. 4.0 = 4%)
             # 无需乘以100
             converted_yield = dividend_yield
             logger.info(f"  ✅ [Fetch] 港股股息率: {converted_yield:.2f}%")
             return converted_yield
        
        logger.warning(f"  ⚠️  无法获取港股股息率 (Info is None)")
        return None
        
    except Exception as e:
        logger.warning(f"  ⚠️  获取港股股息率失败 {symbol}: {e}")
        return None


def fetch_hk_valuation_history(symbol: str, indicator: str = "市盈率") -> pd.DataFrame:
    """
    获取港股历史估值数据
    使用百度接口 (TTM PE 和 PB)
    """
    try:
        # 从 Canonical ID 提取纯代码 (HK:STOCK:00700 -> 00700)
        code = symbol.split(':')[-1] if ':' in symbol else symbol
        
        if indicator == "市盈率(TTM)":
            # 获取 TTM PE
            df = fetch_hk_valuation_baidu_direct(code, indicator="市盈率(TTM)")
            if df is not None and not df.empty:
                df = df.rename(columns={'value': 'pe'}) # Temporary rename, value is generic
                return df
        elif indicator == "市盈率":
             # 获取 Static PE (Baidu usually '市盈率' implies Static/Lyr or just PE)
             df = fetch_hk_valuation_baidu_direct(code, indicator="市盈率")
             if df is not None and not df.empty:
                 df = df.rename(columns={'value': 'pe'})
                 return df
                
        elif indicator == "市净率":
            # 获取 PB
            df = fetch_hk_valuation_baidu_direct(code, indicator="市净率")
            if df is not None and not df.empty:
                df = df.rename(columns={'value': 'pb'})
                logger.info(f"  ✅ 获取 {len(df)} 条 PB 记录")
                return df
        
        return None
            
    except Exception as e:
        logger.error(f"  ❌ 获取港股{indicator}数据失败 {symbol}: {e}")
        return None


def save_cn_valuation_to_daily(symbol: str, df: pd.DataFrame, session: Session) -> int:
    """
    将A股估值数据保存到 MarketDataDaily 表
    更新 pe_ratio 和 pb_ratio 字段
    """
    if df is None or df.empty:
        return 0
    
    updated_count = 0
    
    for _, row in df.iterrows():
        try:
            # 解析日期
            date_str = str(row['数据日期'])
            if len(date_str) == 8:  # YYYYMMDD
                timestamp_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]} 15:00:00"
            else:
                # 已经是 YYYY-MM-DD 格式
                timestamp_str = f"{date_str} 15:00:00"
            
            # 查找对应的日线记录
            existing = session.exec(
                select(MarketDataDaily).where(
                    MarketDataDaily.symbol == symbol,
                    MarketDataDaily.timestamp == timestamp_str
                )
            ).first()

            # Fallback: 尝试 00:00:00 (如果ETL未归一化)
            if not existing:
                if len(date_str) == 8:
                    timestamp_00 = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]} 00:00:00"
                else:
                    timestamp_00 = f"{date_str} 00:00:00"
                
                existing = session.exec(
                    select(MarketDataDaily).where(
                        MarketDataDaily.symbol == symbol,
                        MarketDataDaily.timestamp == timestamp_00
                    )
                ).first()
                if existing:
                    # Self-heal timestamp
                    existing.timestamp = timestamp_str
            
            if existing:
                # 更新PE和PB
                existing.pe_ttm = float(row['PE(TTM)']) if pd.notna(row['PE(TTM)']) else None
                # PE(静) mapping
                existing.pe = float(row['PE(静)']) if 'PE(静)' in row and pd.notna(row['PE(静)']) else None
                
                existing.pb = float(row['市净率']) if pd.notna(row['市净率']) else None
                # 保存股息率(如果有)
                if 'dividend_yield' in row and pd.notna(row['dividend_yield']):
                    existing.dividend_yield = float(row['dividend_yield'])
                existing.updated_at = datetime.now()
                session.add(existing)
                updated_count += 1
                
        except Exception as e:
            logger.warning(f"  ⚠️  跳过记录 {date_str}: {e}")
            continue
    
    if updated_count > 0:
        session.commit()
        logger.info(f"  💾 更新 {updated_count} 条记录的PE/PB数据")
    
    return updated_count


def save_hk_valuation_to_daily(symbol: str, df_pe_ttm: pd.DataFrame, df_pe_static: pd.DataFrame, df_pb: pd.DataFrame, session: Session) -> int:
    """
    将港股估值数据保存到 MarketDataDaily 表
    更新 pe_ratio 和 pb_ratio 字段
    
    注意: 百度返回的日期可能与实际交易日期有偏差,使用日期部分匹配
    """
    updated_count = 0
    pe_ttm_matched = 0
    pe_static_matched = 0
    pb_matched = 0
    
    # 处理 PE TTM
    if df_pe_ttm is not None and not df_pe_ttm.empty:
        logger.info(f"  📊 处理 {len(df_pe_ttm)} 条 PE(TTM) 数据...")
        for _, row in df_pe_ttm.iterrows():
            try:
                date = pd.to_datetime(row['date'])
                date_str = date.strftime('%Y-%m-%d')
                val = float(row['pe']) if pd.notna(row['pe']) else None
                if val is None: continue

                # Match logic: Try nearest within +/- 5 days
                matched = False
                offsets = [0, -1, 1, -2, 2, -3, 3, -4, 4, -5, 5]
                for offset in offsets:
                    target_date = date + pd.Timedelta(days=offset)
                    timestamp_str = target_date.strftime('%Y-%m-%d') + ' 16:00:00'
                    existing = session.exec(select(MarketDataDaily).where(MarketDataDaily.symbol == symbol, MarketDataDaily.market == 'HK', MarketDataDaily.timestamp == timestamp_str)).first()
                    if not existing:
                        timestamp_00 = target_date.strftime('%Y-%m-%d') + ' 00:00:00'
                        existing = session.exec(select(MarketDataDaily).where(MarketDataDaily.symbol == symbol, MarketDataDaily.market == 'HK', MarketDataDaily.timestamp == timestamp_00)).first()
                        if existing: existing.timestamp = timestamp_str
                    
                    if existing:
                        existing.pe_ttm = val
                        existing.updated_at = datetime.now()
                        session.add(existing)
                        pe_ttm_matched += 1
                        matched = True
                        break
            except Exception: continue

    # 处理 PE Static
    if df_pe_static is not None and not df_pe_static.empty:
        logger.info(f"  📊 处理 {len(df_pe_static)} 条 PE(Static) 数据...")
        for _, row in df_pe_static.iterrows():
            try:
                date = pd.to_datetime(row['date'])
                val = float(row['pe']) if pd.notna(row['pe']) else None
                if val is None: continue
                
                matched = False
                offsets = [0, -1, 1, -2, 2, -3, 3, -4, 4, -5, 5]
                for offset in offsets:
                    target_date = date + pd.Timedelta(days=offset)
                    timestamp_str = target_date.strftime('%Y-%m-%d') + ' 16:00:00'
                    existing = session.exec(select(MarketDataDaily).where(MarketDataDaily.symbol == symbol, MarketDataDaily.market == 'HK', MarketDataDaily.timestamp == timestamp_str)).first()
                    if not existing:
                        timestamp_00 = target_date.strftime('%Y-%m-%d') + ' 00:00:00'
                        existing = session.exec(select(MarketDataDaily).where(MarketDataDaily.symbol == symbol, MarketDataDaily.market == 'HK', MarketDataDaily.timestamp == timestamp_00)).first()
                        if existing: existing.timestamp = timestamp_str
                    
                    if existing:
                        existing.pe = val
                        existing.updated_at = datetime.now()
                        session.add(existing)
                        pe_static_matched += 1
                        matched = True
                        break
            except Exception: continue
    
    # 处理PB数据
    if df_pb is not None and not df_pb.empty:
        logger.info(f"  📊 处理 {len(df_pb)} 条PB数据...")
        for _, row in df_pb.iterrows():
            try:
                date = pd.to_datetime(row['date'])
                date_str = date.strftime('%Y-%m-%d')
                pb_value = float(row['pb']) if pd.notna(row['pb']) else None
                
                if pb_value is None:
                    continue
                
                # Match logic: Try nearest within +/- 5 days
                matched = False
                # Priority: 0, -1, 1, -2, 2, -3, 3, -4, 4, -5, 5
                offsets = [0, -1, 1, -2, 2, -3, 3, -4, 4, -5, 5]
                
                for offset in offsets:
                    target_date = date + pd.Timedelta(days=offset)
                    timestamp_str = target_date.strftime('%Y-%m-%d') + ' 16:00:00'
                    existing = session.exec(select(MarketDataDaily).where(MarketDataDaily.symbol == symbol, MarketDataDaily.market == 'HK', MarketDataDaily.timestamp == timestamp_str)).first()
                    
                    if not existing:
                        timestamp_00 = target_date.strftime('%Y-%m-%d') + ' 00:00:00'
                        existing = session.exec(select(MarketDataDaily).where(MarketDataDaily.symbol == symbol, MarketDataDaily.market == 'HK', MarketDataDaily.timestamp == timestamp_00)).first()
                        if existing: existing.timestamp = timestamp_str # Self-heal
                    
                    if existing:
                        # Avoid overwriting if we already have a closer match? 
                        # Ideally updates are idempotent.
                        existing.pb = pb_value
                        existing.updated_at = datetime.now()
                        session.add(existing)
                        pb_matched += 1
                        matched = True
                        break
                
                if not matched:
                    logger.debug(f"  ⚠️  未匹配到PB记录: {date_str}")
                    
            except Exception as e:
                logger.warning(f"  ❌ 处理PB记录失败 {date_str}: {e}")
                continue
    
    updated_count = pe_ttm_matched + pe_static_matched + pb_matched
    
    if updated_count > 0:
        session.commit()
        logger.info(f"  💾 更新 {updated_count} 条记录 (PE_TTM: {pe_ttm_matched}, PE_Static: {pe_static_matched}, PB: {pb_matched})")
    else:
        logger.warning(f"  ⚠️  没有匹配到任何记录")
    
    return updated_count


def fetch_us_valuation_yfinance(symbol: str) -> dict:
    """
    从 yfinance 获取美股的实时估值指标
    使用 ticker.info API
    """
    try:
        import yfinance as yf
        
        # 从 Canonical ID 提取纯代码 (US:STOCK:AAPL -> AAPL)
        code = symbol.split(':')[-1] if ':' in symbol else symbol
        
        logger.info(f"  📥 获取美股估值数据: {code}")
        
        ticker = yf.Ticker(code)
        info = ticker.info
        
        # 获取 PE (优先使用 trailingPE, 其次 forwardPE)
        pe = info.get('trailingPE') or info.get('forwardPE')
        
        # 获取 PB
        pb = info.get('priceToBook')
        
        # 获取股息率
        dividend_yield = info.get('dividendYield')
        # 无需乘以100
        if dividend_yield is not None:
            pass
        
        result = {
            'pe_ttm': pe, # Yfinance trailingPE -> pe_ttm
            'pb': pb,
            'dividend_yield': dividend_yield
        }
        
        # 格式化输出
        pe_str = f"{pe:.2f}" if pe else "N/A"
        pb_str = f"{pb:.2f}" if pb else "N/A"
        div_str = f"{dividend_yield:.2f}%" if dividend_yield else "N/A"
        logger.info(f"  ✅ PE: {pe_str}, PB: {pb_str}, 股息率: {div_str}")
        
        return result
        
    except Exception as e:
        logger.error(f"  ❌ 获取美股估值数据失败 {symbol}: {e}")
        return None



FMP_API_KEY = "yytaAKONtPbR5cBcx9azLeqlovaWDRQm"

def fetch_us_valuation_history_fmp(symbol: str, limit: int = 5) -> pd.DataFrame:
    """
    从 FMP Cloud 获取美股历史估值数据 (PE, PB)
    使用 /stable/ratios 接口
    """
    try:
        # 纯代码
        code = symbol.split(':')[-1] if ':' in symbol else symbol
        
        url = f"https://financialmodelingprep.com/stable/ratios?symbol={code}&period=annual&limit={limit}&apikey={FMP_API_KEY}"
        logger.info(f"  📥 [FMP] 获取美股历史估值: {code}")
        
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if not data:
            logger.info(f"  ℹ️  [FMP] 无历史数据: {code}")
            return None
        
        # 处理 API 错误 (例如 Limit Reach)
        if isinstance(data, dict) and "Error Message" in data:
             logger.warning(f"  ⚠️ [FMP] API 限制或错误: {data['Error Message']}")
             return None

        # 转换为 DataFrame
        records = []
        for item in data:
            if not isinstance(item, dict): continue
            records.append({
                'date': item.get('date'),
                'pe': item.get('priceToEarningsRatio'),
                'pb': item.get('priceToBookRatio')
            })
            
        df = pd.DataFrame(records)
        logger.info(f"  ✅ [FMP] 获取 {len(df)} 条历史记录")
        return df
        
    except Exception as e:
        logger.error(f"  ❌ [FMP] 获取失败 {symbol}: {e}")
        return None

def fetch_us_valuation_history_fmp_ttm(symbol: str, limit: int = 365) -> pd.DataFrame:
    """
    从 FMP Cloud 获取美股每日滚动 PE (TTM)
    使用 /v3/ratios-ttm 接口
    """
    try:
        # 纯代码
        code = symbol.split(':')[-1] if ':' in symbol else symbol
        
        # 使用 v3 接口 (根据用户请求)
        url = f"https://financialmodelingprep.com/api/v3/ratios-ttm/{code}?limit={limit}&apikey={FMP_API_KEY}"
        logger.info(f"  📥 [FMP] 获取美股 TTM PE: {code}")
        
        response = requests.get(url, timeout=10)
        
        # 错误处理
        if response.status_code == 403:
             logger.warning(f"  ⚠️ [FMP] API Key 无效或无 TTM 权限 (403): {response.text[:100]}")
             return None
             
        data = response.json()
        
        if not data:
            logger.info(f"  ℹ️  [FMP] 无 TTM 数据: {code}")
            return None
        
        if isinstance(data, dict) and "Error Message" in data:
             logger.warning(f"  ⚠️ [FMP] API 错误: {data['Error Message']}")
             return None

        # 转换为 DataFrame
        records = []
        for item in data:
            if not isinstance(item, dict): continue
            
            # FMP TTM field: peRatioTTM
            val = item.get('peRatioTTM')
            if val is None: val = item.get('priceEarningsRatioTTM')
            
            # --- VERA Pro Fields ---
            # NOTE: The endpoint /ratios-ttm usually only returns Ratios (PE, PB, etc.), NOT fundamentals.
            # To get NetIncomeCommon and SharesDiluted(TTM), we strictly need /key-metrics-ttm or calculate from /income-statement.
            # However, for simple PE history backfill (this function's purpose is PE history), we might just be saving PE TTM directly?
            # Wait, `fetch_us_valuation_history_fmp_ttm` returns a DF that is saving to MarketDataDaily directly in `recalc_historical_pe` or saving to Financials?
            # Looking at `save_us_historical_valuation_to_daily`, it saves directly to DAILY.
            # This function is for "downloading pre-calculated PE from FMP".
            
            # BUT, the user wants us to CALCULATE locally using Fundamentals.
            # So we need a NEW function in `fetch_financials.py` (or here) that fetches INCOME STATEMENT and fills FinancialFundamentals.
            # This function `fetch_us_valuation_history_fmp_ttm` is about fetching PE directly.
            
            # Let's keep this as is for BACKUP PE sources, but we need to ensure we can FETCH FUNDAMENTALS.
            # The user instruction was: "Update FMP API calls to fetch specific fields: netIncomeForCommonStockholders..."
            # This implies we need to update where we fetch FinancialFundamentals.
            
            if val is None: continue
            
            records.append({
                'date': item.get('date'),
                'pe_ttm': val
            })
            
        df = pd.DataFrame(records)
        logger.info(f"  ✅ [FMP] 获取 {len(df)} 条 TTM 记录")
        return df
        
    except Exception as e:
        logger.error(f"  ❌ [FMP] 获取 TTM 失败 {symbol}: {e}")
        return None

def save_us_historical_valuation_to_daily(symbol: str, df: pd.DataFrame, session: Session) -> int:
    """
    保存 FMP 历史估值数据到 MarketDataDaily (Fallback logic)
    支持 pe, pb, pe_ttm
    """
    if df is None or df.empty:
        return 0
        
    updated_count = 0
    
    for _, row in df.iterrows():
        try:
            date_str = row['date'] # YYYY-MM-DD
            pe = float(row['pe']) if 'pe' in row and pd.notna(row['pe']) else None
            pe_ttm = float(row['pe_ttm']) if 'pe_ttm' in row and pd.notna(row['pe_ttm']) else None
            pb = float(row['pb']) if 'pb' in row and pd.notna(row['pb']) else None
            
            if pe is None and pb is None and pe_ttm is None:
                continue
                
            task_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            matched = False
            for offset in [0, -1, -2, -3]:
                d = task_date + timedelta(days=offset)
                ts_str = d.strftime("%Y-%m-%d") + " 16:00:00"
                
                existing = session.exec(
                    select(MarketDataDaily).where(
                        MarketDataDaily.symbol == symbol,
                        MarketDataDaily.market == 'US',
                        MarketDataDaily.timestamp == ts_str
                    )
                ).first()
                
                # Fallback: 尝试 00:00
                if not existing:
                    ts_str_00 = d.strftime("%Y-%m-%d") + " 00:00:00"
                    existing = session.exec(
                        select(MarketDataDaily).where(
                            MarketDataDaily.symbol == symbol,
                            MarketDataDaily.market == 'US',
                            MarketDataDaily.timestamp == ts_str_00
                        )
                    ).first()
                    if existing:
                        existing.timestamp = ts_str

                if existing:
                    if pe is not None: existing.pe = pe
                    if pe_ttm is not None: existing.pe_ttm = pe_ttm
                    if pb is not None: existing.pb = pb
                    existing.updated_at = datetime.now()
                    session.add(existing)
                    updated_count += 1
                    matched = True
                    break
            
            if not matched:
                logger.debug(f"  ⚠️  [FMP] 未匹配到历史日线: {date_str}")

        except Exception as e:
            logger.warning(f"  ⚠️  保存失败 {date_str}: {e}")
            
    if updated_count > 0:
        session.commit()
    return updated_count


def save_us_valuation_to_daily(symbol: str, valuation: dict, session: Session) -> int:
    """
    将美股估值数据保存到 MarketDataDaily 表
    """
    if not valuation:
        return 0
    
    try:
        from backend.market_status import MarketStatus
        
        is_market_open = MarketStatus.is_market_open('US')
        market_time = MarketStatus.get_market_time('US')
        
        latest_record = session.exec(
            select(MarketDataDaily).where(
                MarketDataDaily.symbol == symbol,
                MarketDataDaily.market == 'US'
            ).order_by(MarketDataDaily.timestamp.desc())
        ).first()
        
        if not latest_record:
            logger.warning(f"  ⚠️  未找到日线记录: {symbol}")
            return 0
        
        record_date = datetime.strptime(latest_record.timestamp, '%Y-%m-%d %H:%M:%S').date()
        today = market_time.date()
        
        if is_market_open and record_date == today:
            logger.info(f"  ⏭️  盘中时段,跳过今日数据,仅更新前一交易日: {symbol}")
            records = session.exec(
                select(MarketDataDaily).where(
                    MarketDataDaily.symbol == symbol,
                    MarketDataDaily.market == 'US'
                ).order_by(MarketDataDaily.timestamp.desc())
            ).all()
            
            if len(records) < 2:
                logger.warning(f"  ⚠️  没有前一交易日记录: {symbol}")
                return 0
            latest_record = records[1]
        
        updated = False
        if valuation.get('pe_ttm'):
            latest_record.pe_ttm = valuation['pe_ttm']
            updated = True
        # Static PE not updated from Yfinance (Realtime) usually
        if valuation.get('pe'):
             latest_record.pe = valuation['pe']
             updated = True
        if valuation.get('pb'):
            latest_record.pb = valuation['pb']
            updated = True
        if valuation.get('dividend_yield'):
            latest_record.dividend_yield = valuation['dividend_yield']
            updated = True
        
        if updated:
            latest_record.updated_at = datetime.now()
            session.add(latest_record)
            session.commit()
            logger.info(f"  💾 更新记录的估值数据 ({latest_record.timestamp})")
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"  ❌ 保存美股估值数据失败 {symbol}: {e}")
        return 0


def derive_daily_pe_from_points(symbol: str, daily_prices: pd.DataFrame, report_points: pd.DataFrame) -> pd.Series:
    """
    通用函数: 基于稀疏的 PE 报告点推导日线 PE
    """
    try:
        if daily_prices.empty or report_points.empty:
            return pd.Series(dtype=float)
            
        # 1. 准备数据
        reports = report_points.sort_values('date').copy()
        reports = reports[reports['pe'] > 0]
        
        if reports.empty:
            return pd.Series(dtype=float)

        daily_idx = daily_prices.index.sort_values()
        
        # 2. 计算每个报告日的隐含 EPS
        eps_map = {}
        for _, row in reports.iterrows():
            r_date = row['date']
            r_pe = row['pe']
            
            # 在日线价格中找 exact match 或 nearest (Look-back only)
            matched_date = None
            try:
                # 使用 asof 寻找最近的一个交易日 (Look-back, 避免未来数据)
                # asof returns the last index label <= r_date
                closest_date = daily_idx.asof(r_date)
                
                if pd.isna(closest_date):
                    continue
                    
                # 检查时间跨度是否过大 (超过 5 天视为无效匹配)
                if (r_date - closest_date).days > 5:
                    continue
                    
                matched_date = closest_date
                close = daily_prices.loc[matched_date, 'close']

                if isinstance(close, pd.Series): close = close.iloc[0]
                
                if close > 0 and r_pe > 0:
                    eps_implied = close / r_pe
                    if matched_date:
                        eps_map[matched_date] = eps_implied
            except:
                continue
                
        if not eps_map:
            return pd.Series(dtype=float)
            
        # 3. 生成 EPS 序列并对齐到日线
        eps_series = pd.Series(eps_map).sort_index()
        eps_daily = eps_series.reindex(daily_idx).ffill()
        
        # 4. 计算 Daily PE
        daily_pe = daily_prices['close'] / eps_daily
        daily_pe = daily_pe.replace([np.inf, -np.inf], np.nan).dropna()
        
        return daily_pe.round(2)
        
    except Exception as e:
        logger.error(f"  ❌ 推导失败 {symbol}: {e}")
        return pd.Series(dtype=float)


def derive_daily_pb_from_points(symbol: str, daily_prices: pd.DataFrame, report_points: pd.DataFrame) -> pd.Series:
    """
    通用函数: 基于稀疏的 PB 报告点推导日线 PB
    逻辑同 PE 推导: Implied BPS = Close / PB
    """
    try:
        if daily_prices.empty or report_points.empty:
            return pd.Series(dtype=float)
            
        # 1. 准备数据
        reports = report_points.sort_values('date').copy()
        reports = reports[reports['pb'] > 0]
        
        if reports.empty:
            return pd.Series(dtype=float)

        daily_idx = daily_prices.index.sort_values()
        
        # 2. 计算每个报告日的隐含 BPS
        bps_map = {}
        for _, row in reports.iterrows():
            r_date = row['date']
            r_pb = row['pb']
            
            # 在日线价格中找 match (Look-back only)
            matched_date = None
            try:
                # 使用 asof 寻找最近的一个交易日 (Look-back, 避免未来数据)
                # asof returns the last index label <= r_date
                closest_date = daily_idx.asof(r_date)
                
                if pd.isna(closest_date):
                    continue
                    
                # 检查时间跨度是否过大
                if (r_date - closest_date).days > 5:
                    continue
                    
                matched_date = closest_date
                close = daily_prices.loc[matched_date, 'close']

                if isinstance(close, pd.Series): close = close.iloc[0]
                
                if close > 0 and r_pb > 0:
                    bps_implied = close / r_pb
                    if matched_date:
                        bps_map[matched_date] = bps_implied
            except:
                continue
                
        if not bps_map:
            return pd.Series(dtype=float)
            
        # 3. 生成 BPS 序列并对齐到日线
        bps_series = pd.Series(bps_map).sort_index()
        bps_daily = bps_series.reindex(daily_idx).ffill()
        
        # 4. 计算 Daily PB
        daily_pb = daily_prices['close'] / bps_daily
        daily_pb = daily_pb.replace([np.inf, -np.inf], np.nan).dropna()
        
        return daily_pb.round(2)
        
    except Exception as e:
        logger.error(f"  ❌ PB推导失败 {symbol}: {e}")
        return pd.Series(dtype=float)


# ==============================================================================
# Local Derivation (Fallback for missing API data)
# ==============================================================================

def derive_pe_ttm_from_fundamentals(symbol: str, session: Session) -> pd.DataFrame:
    """
    3. **History (Derivation)**: **本地推导引擎** (Fallback)。
       - 当 API 缺失时，利用本地 `FinancialFundamentals` (EPS) + `MarketDataDaily` (Close) 计算。
       - **高级特性: 汇率自动对齐 (Currency Alignment)**
         本脚本包含硬编码的近似汇率逻辑，以解决财报货币与交易货币不一致的问题：
         - **US Market (ADR)**: TWD/CNY/HKD/JPY -> USD (e.g. TSM: TWD EPS -> USD Price).
         - **HK Market**: CNY/USD -> HKD (e.g. H股财报为 CNY -> 港股报价为 HKD).
         - *注意*: 使用静态汇率 (Static Rates)，历史精度不如专业版动态汇率。
       - **频度处理**: 智能识别 Annual/Quarterly 报告并进行 Rolling TTM 计算。
    """
    try:
        from backend.models import FinancialFundamentals
        
        # 1. 获取日线价格
        daily_prices = pd.read_sql(
            select(MarketDataDaily.timestamp, MarketDataDaily.close)
            .where(MarketDataDaily.symbol == symbol)
            .order_by(MarketDataDaily.timestamp),
            engine
        )
        if daily_prices.empty:
            return None
            
        daily_prices['timestamp'] = pd.to_datetime(daily_prices['timestamp'])
        daily_prices.set_index('timestamp', inplace=True)
        # Ensure numeric
        daily_prices['close'] = pd.to_numeric(daily_prices['close'], errors='coerce')
        
        # 2. 获取财务数据 (EPS)
        # 优先使用 eps 字段 (假设为 Basic/Diluted EPS)
        # TODO: 区分 Annual/Quarterly 并正确计算 TTM EPS.
        # 但 FinancialFundamentals 存储的是原始 Report 数据.
        # 如果是 Annual, EPS is annual. If Quarterly, EPS is quarterly.
        # 简单起见，我们只能假设 fetch_financials 已经尽力获取了 EPS.
        # 如果是美股，fetch_financials 可能获取的是 Quarterly?
        # A股 (AkShare) 获取的是 Annual/Quarterly.
        # 我们这里暂时假设: 使用最近一次报告的 EPS * (如果是季度则需调整? 不, PE TTM 需要 TTM EPS)
        # 如果 FinancialFundamentals 里的是 Quarterly EPS, 单季 EPS 不能直接用.
        # 需要 Sum Last 4 Quarters.
        # 但这很复杂.
        # 此时 check 'net_income_ttm'. 如果有 net_income_ttm, 我们可以用 net_income_ttm / shares?
        # 但 shares 历史很难找.
        # 所以最好还是用 'eps' 字段, 并假设它是 TTM EPS (如果 source 提供) 或者 Annual EPS.
        # 对于美股 (Yahoo), financial data varies.
        # 让我们检查一下 FinancialFundamentals schema.
        # ... 'revenue_ttm', 'net_income_ttm' exist.
        # So wait, we HAVE net_income_ttm!
        # Do we have Market Cap?
        # MarketDataDaily has 'market_cap'.
        # PE = Market Cap / Net Income TTM.
        # This is MUCH better if we have Market Cap history.
        # MarketDataDaily market_cap might be missing or derived?
        # If we have Close Price, we need Shares Outstanding History to get Market Cap History.
        # If we don't have Shares history, we can't get accurate Market Cap history.
        # So we stick to Price / EPS.
        # We need TTM EPS.
        # If financial_fundamentals has only Annual EPS, we use it (Static PE approx).
        # We will try to filter for Annual reports only? Or use provided data.
        
        financials = session.exec(
            select(FinancialFundamentals)
            .where(FinancialFundamentals.symbol == symbol)
            .order_by(FinancialFundamentals.as_of_date)
        ).all()
        
        if not financials:
            return None
            
        eps_list = []
        for f in financials:
            val = None
            # 1. 优先使用 eps_ttm (如果有)
            if hasattr(f, 'eps_ttm') and f.eps_ttm is not None:
                val = f.eps_ttm
            # 2. 其次使用 eps (需判断 Annual 还是 Quarterly)
            elif f.eps is not None:
                # 简单处理：如果是 Quarterly 且没有 TTM，暂时假设需要 Rolling Sum (但在 Loop 里不好做 Rolling)
                # 更好的做法是先转 DataFrame 再 Rolling Sum
                # 这里先只收集原始 EPS
                val = f.eps
            
            if val is not None:
                eps_list.append({
                    'date': f.as_of_date,
                    'eps': val,
                    'type': f.report_type,
                    'currency': f.currency if hasattr(f, 'currency') else None
                })
        
        if not eps_list:
            return None
            
        df_eps = pd.DataFrame(eps_list)
        df_eps['date'] = pd.to_datetime(df_eps['date'])
        df_eps = df_eps.set_index('date').sort_index()
        
        # --- Handle Quarterly to TTM ---
        # 如果大部分数据是 quarterly，且值很小（相比股价），说明是单季 EPS
        # 需要计算 Rolling 4 Sum
        # 简单逻辑：如果是 quarterly，执行 rolling(4).sum()
        # 注意：这需要数据是连续的 quarters。如果中间缺，sum 会错。
        # 稳健做法：
        # 1. 筛选 quarterly rows
        # 2. resample('Q') 填充缺失? No, too complex.
        # 3. 只是简单 Rolling 4 sum, min_periods=4.
        
        # 混合 Annual/Quarterly 怎么办？
        # Strategy:
        # A. Separate Annual and Quarterly series.
        # B. If Quarterly exists and is sufficient, use Quarterly Rolling Sum. 
        # C. Fill gaps with Annual?
        # D. Simplify: If 'report_type' == 'quarterly', use rolling sum. If 'annual', use as is (static PE).
        
        # Check predominant type
        q_count = len(df_eps[df_eps['type'] == 'quarterly'])
        a_count = len(df_eps[df_eps['type'] == 'annual'])
        
        final_eps_series = None
        
        if q_count > a_count:
            # Main strategy: Quarterly Rolling Sum
            q_series = df_eps[df_eps['type'] == 'quarterly']['eps']
            # Rolling sum of last 4 (window=4)
            # Use 'time' based rolling? No, just periods if sorted.
            # Assuming ~4 reports per year.
            ttm_series = q_series.rolling(window=4, min_periods=1).sum() # min_periods=1 to have *some* data initially? No, TTM needs 4.
            # actually usually min_periods=4 for valid TTM. 
            # But let's be loose -> min_periods=1 allows partial TTM (better than nothing? No, dangerous. Partial sum is meaningless).
            # But if we use min_periods=4, early history is blank.
            # Let's use min_periods=4 but fillna with * 4 if only 1? No.
            # Let's try min_periods=4.
            ttm_series = q_series.rolling(window=4, min_periods=4).sum()
            final_eps_series = ttm_series
        else:
            # Annual strategy
            final_eps_series = df_eps['eps'] # Use as Static PE (Previous Year EPS)

        if final_eps_series is None or final_eps_series.empty:
             final_eps_series = df_eps['eps'] # Fallback to whatever we have

        # --- Currency Conversion ---
        # Check last record currency
        last_currency = df_eps.iloc[-1].get('currency')
        currency_multiplier = 1.0
        
        # Special Case for TSM (ADR vs TWD EPS)
        # TSM Price is USD (~190), EPS is TWD (~87). 
        # Need to divide EPS by TWD/USD rate (~32).
        # Or multiply Price by 32. 
        # PE = Price / EPS.
        # IF Price is USD, EPS is TWD. PE = USD / TWD = wrong.
        # We need PE = Price_USD / EPS_USD.
        # EPS_USD = EPS_TWD / ExchangeRate.
        # ExchangeRate ~ 32.5.
        
        if symbol == 'US:STOCK:TSM' and (last_currency == 'TWD' or last_currency is None):
             # Hardcode fix for TSM if currency not explicitly USD
             # Assuming EPS is TWD (87.2 is definitely TWD, USD EPS would be ~2.7)
             # EPS > 20 usually implies not USD for TSM.
             if final_eps_series.mean() > 20: 
                 currency_multiplier = 1.0 / 32.5 # approx rate
                 logger.info(f"  💱 TSM Detected: Converting TWD EPS to USD (Rate ~32.5)")

        # Generic Currency Handler
        # 1. US Market (Target: USD)
        if 'US:STOCK' in symbol and last_currency not in ['USD', None]:
            if last_currency in ['CNY', 'RMB']:
                 currency_multiplier = 1.0 / 7.2
            elif last_currency == 'TWD':
                 currency_multiplier = 1.0 / 32.5
            elif last_currency == 'HKD':
                 currency_multiplier = 1.0 / 7.8
            elif last_currency == 'JPY':
                 currency_multiplier = 1.0 / 150.0
        
        # 2. HK Market (Target: HKD)
        elif 'HK:STOCK' in symbol:
             # HK Stocks often report in CNY or USD
             if last_currency == 'USD':
                 currency_multiplier = 7.78  # USD -> HKD
             elif last_currency in ['CNY', 'RMB']:
                 currency_multiplier = 1.08  # CNY -> HKD (Approx, 1 CNY ~ 1.08 HKD)
                 # Wait, 1 CNY is STRONGER than HKD. 1 CNY = 1.08 HKD.
                 # EPS (CNY) * 1.08 = EPS (HKD). Correct.
             elif last_currency == 'HKD':
                 currency_multiplier = 1.0

        final_eps_series = final_eps_series * currency_multiplier

        # 将 EPS 对齐到日线 (FFill)
        eps_daily = final_eps_series.reindex(daily_prices.index, method='ffill')
        
        # 计算 PE
        pe_series = daily_prices['close'] / eps_daily
        pe_series = pe_series.replace([np.inf, -np.inf], np.nan).dropna()
        
        # Filter outliers? PE > 5000 or < 0
        pe_series = pe_series[(pe_series > 0) & (pe_series < 5000)]
        
        if pe_series.empty:
            return None
            
        return pd.DataFrame({'date': pe_series.index.strftime('%Y-%m-%d'), 'pe_ttm': pe_series.values})

    except Exception as e:
        logger.error(f"  ❌ 本地推导失败 {symbol}: {e}")
        return None

# ==============================================================================
# Interactive CLI
# ==============================================================================

class Config:
    def __init__(self):
        self.markets = {'CN', 'HK', 'US'}
        # Default all selected
        self.selected_markets = self.markets.copy()

def clear_screen():
    print("\033[H\033[J", end="")

def print_menu(cfg: Config):
    clear_screen()
    print("="*60)
    print(" 📊 估值数据下载器 (Interactive) - 仅支持个股 (STOCK)")
    print("="*60)
    
    def status(condition):
        return "✅" if condition else "❌"
    
    # Simple Market Toggles
    print(f" [1] {status('CN' in cfg.selected_markets)} CN")
    print(f" [2] {status('HK' in cfg.selected_markets)} HK")
    print(f" [3] {status('US' in cfg.selected_markets)} US")
    
    print("-" * 60)
    print(" [0] ▶️  开始更新     [A] 全选     [C] 清空")
    print(" [Q] 退出")
    print("="*60)

def configure():
    cfg = Config()
    
    # Mapping keys to toggle actions
    toggles = {
        '1': lambda: toggle(cfg.selected_markets, 'CN'),
        '2': lambda: toggle(cfg.selected_markets, 'HK'),
        '3': lambda: toggle(cfg.selected_markets, 'US'),
    }
    
    while True:
        print_menu(cfg)
        try:
            choice = input(" 请输入选项 [0-9/A/C]: ").strip().upper()
        except (EOFError, KeyboardInterrupt):
            print("\n退出")
            sys.exit(0)
            
        if choice == '0':
            return cfg
        elif choice == 'Q':
            sys.exit(0)
        elif choice in toggles:
            toggles[choice]()
        elif choice == 'A':
            cfg.selected_markets = cfg.markets.copy()
        elif choice == 'C':
            cfg.selected_markets.clear()
            
def toggle(selection_set, item):
    if item in selection_set:
        selection_set.remove(item)
    else:
        selection_set.add(item)

# ==============================================================================
# Futu Interface
# ==============================================================================
def fetch_hk_valuation_futu(symbol: str, market: str, session: Session):
    """
    Use Futu OpenD to fetch historical PE for HK stocks.
    Requires FutuOpenD running on 127.0.0.1:11111.
    """
    try:
        from futu import OpenQuoteContext, KLType, AuType, RET_OK
        import datetime
        
        # Futu Code Format: HK:STOCK:00700 -> HK.00700
        futu_code = symbol.replace('HK:STOCK:', 'HK.')
        
        # Connect
        quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
        
        # Fetch History with Pagination
        end_str = datetime.datetime.now().strftime("%Y-%m-%d")
        start_str = "2020-01-01"
        
        all_data = []
        page_req_key = None
        
        while True:
            ret, data, page_req_key = quote_ctx.request_history_kline(
                code=futu_code,
                start=start_str,
                end=end_str,
                ktype=KLType.K_DAY,
                autype=AuType.QFQ,
                max_count=1000,
                page_req_key=page_req_key
            )
            
            if ret == RET_OK:
                if not data.empty:
                    all_data.append(data)
            else:
                logger.error(f"  ❌ Futu Error {symbol}: {data}")
                break
                
            if page_req_key is None:
                break
                
        if not all_data:
            logger.warning(f"  ⚠️  Futu Empty {symbol}")
            quote_ctx.close()
            return
            
        import pandas as pd
        data = pd.concat(all_data, ignore_index=True)

            
        # Parse and Save
        # Data columns: time_key, pe_ratio, ...
        # Futu PE is Static.
        
        # Check for Time Shift (Simulation Mode support)
        # If System Time is 2026 but Futu returns 2025, we shift Futu dates to match DB.
        system_year = datetime.datetime.now().year
        futu_latest_str = data.iloc[-1]['time_key']
        futu_latest_year = int(futu_latest_str.split('-')[0])
        
        year_offset = 0
        if system_year > futu_latest_year:
             year_offset = system_year - futu_latest_year
             logger.info(f"  🕰️  Detected Simulation Mode: Shifting Futu data by +{year_offset} years")
        
        updates = []
        for _, row in data.iterrows():
            futu_date_str = row['time_key'].split(' ')[0] # 2025-01-01
            pe_val = row['pe_ratio']
            
            # Apply Shift
            if year_offset > 0:
                 futu_dt = datetime.datetime.strptime(futu_date_str, "%Y-%m-%d")
                 shifted_dt = futu_dt.replace(year=futu_dt.year + year_offset)
                 date_str = shifted_dt.strftime("%Y-%m-%d")
            else:
                 date_str = futu_date_str
            
            # Map Close Time (HK 16:00)
            timestamp_str = f"{date_str} 16:00:00"
            
            # Find DB Record
            stmt = select(MarketDataDaily).where(
                MarketDataDaily.symbol == symbol,
                MarketDataDaily.market == market,
                MarketDataDaily.timestamp == timestamp_str
            )
            record = session.exec(stmt).first()
            
            if record:
                if pe_val and pe_val > 0:
                    record.pe = float(pe_val) # Save to Static PE
                    # record.pe_ttm = None    # Keep TTM clean or update from Snapshot later
                    record.updated_at = datetime.datetime.now()
                    session.add(record)
                    updates.append(1)
        
        # --- NEW: Fetch Snapshot for Latest TTM ---
        # Only if we have a record for Today (or latest available)
        try:
            ret_s, data_s = quote_ctx.get_market_snapshot([futu_code])
            if ret_s == RET_OK and not data_s.empty:
                pe_ttm = data_s.iloc[0].get('pe_ttm_ratio')
                pe_static = data_s.iloc[0].get('pe_ratio')
                
                if pe_ttm and pe_ttm > 0:
                     # Find TODAY's record (System Date)
                     today_str = datetime.datetime.now().strftime("%Y-%m-%d")
                     ts_today = f"{today_str} 16:00:00"
                     
                     rec_today = session.exec(select(MarketDataDaily).where(
                         MarketDataDaily.symbol == symbol,
                         MarketDataDaily.timestamp == ts_today
                     )).first()
                     
                     if rec_today:
                         rec_today.pe_ttm = float(pe_ttm)
                         # Optionally update PE Static if Snapshot is fresher? 
                         # But History loop usually covers it.
                         # rec_today.pe = float(pe_static) 
                         session.add(rec_today)
                         logger.info(f"  📸 Snapshot TTM Updated: {symbol} -> {pe_ttm}")
                         updates.append(1)
            else:
                logger.warning(f"  ⚠️  Snapshot Failed {symbol}: {data_s}")
        except Exception as e:
            logger.error(f"  ❌ Snapshot Error {symbol}: {e}")

        session.commit()
        quote_ctx.close()

        if updates:
             logger.info(f"  ✅ Futu Saved {symbol}: {len(updates)} records (Static PE)")
             
    except ImportError:
        logger.error("  ❌ Futu API not installed (pip install futu-api)")
    except Exception as e:
         logger.error(f"  ❌ Futu Exception {symbol}: {e}")


# ==============================================================================
# Main
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description='获取历史估值数据 (PE/PB)')
    parser.add_argument('--symbol', type=str, help='指定要处理的 Canonical ID (例如 US:STOCK:TSLA, HK:STOCK:00700)')
    args = parser.parse_args()

    # 1. Configuration (Interactive vs Headless)
    selected_markets = {'CN', 'HK', 'US'}
    
    if args.symbol:
        print(f"🎯 仅处理指定资产: {args.symbol}")
        # Infer market from symbol if possible, or just rely on symbol filter later
        # But we need selected_markets for the query logic below
        parts = args.symbol.split(':')
        if len(parts) > 0 and parts[0] in selected_markets:
            selected_markets = {parts[0]}
    else:
        # Interactive Mode
        print("进入交互模式...")
        try:
            cfg = configure()
            selected_markets = cfg.selected_markets
        except KeyboardInterrupt:
            print("\nExit")
            return

    print("=" * 80)
    print(f"📊 开始获取估值数据 (Markets: {selected_markets})")
    print("   注意: 仅更新个股 (STOCK)")
    print("=" * 80)
    
    try:
        with Session(engine) as session:
            # 构建查询
            stmt = select(Watchlist).where(Watchlist.market.in_(selected_markets))
            
            # 如果指定了 symbol, 增加过滤条件
            if args.symbol:
                stmt = stmt.where(Watchlist.symbol == args.symbol)
                
            watchlist = session.exec(stmt).all()
            
            if not watchlist:
                print(f"⚠️  未找到匹配的资产" + (f": {args.symbol}" if args.symbol else ""))
                return
            
            # 预先过滤: 只保留 STOCK
            targets = []
            for item in watchlist:
                parts = item.symbol.split(':')
                # Canonical ID Format: MARKET:TYPE:CODE
                # But sometimes simple formats exist. Let's use robust check.
                # Assuming format is strictly followed or at least contains type.
                if len(parts) >= 2:
                    asset_type = parts[1]
                else:
                    # Fallback or skip? safely skip if unsure
                    continue
                    
                if asset_type == 'STOCK':
                    targets.append(item)
            
            count_total = len(targets)
            if count_total == 0:
                print("⚠️  筛选后无个股目标 (STOCK).")
                return

            print(f"\n共 {count_total} 个个股资产需要获取估值数据\n")
            
            cn_count = 0
            hk_count = 0
            us_count = 0

            for idx, item in enumerate(targets, 1):
                print(f"\n[{idx}/{count_total}] {'='*60}")
                
                # Check for strict interruption
                
                parts = item.symbol.split(':')
                asset_type = parts[1] if len(parts) >= 2 else 'STOCK'
                
                try:
                    if item.market == 'CN':
                        # A股保持原有逻辑
                        df = fetch_cn_valuation_history(item.symbol, asset_type)
                        
                        if df is not None and not df.empty:
                            dividend_yield = fetch_cn_dividend_yield(item.symbol)
                            if dividend_yield is not None:
                                df['dividend_yield'] = dividend_yield
                            
                            updated = save_cn_valuation_to_daily(item.symbol, df, session)
                            if updated > 0:
                                cn_count += 1
                                
                    elif item.market == 'HK':
                        print(f"🔄 处理港股 (Futu + Dividend): {item.symbol}")
                        # 1. Futu: PE/PE_TTM/PB
                        fetch_hk_valuation_futu(item.symbol, "HK", session)
                        
                        # 2. Yahoo: Dividend Yield (Restore)
                        div_yield = fetch_hk_dividend_yield(item.symbol)
                        if div_yield is not None:
                             # Save Dividend Yield to Database (Find latest record)
                             # Reuse save_cn_valuation_to_daily logic or inline simple update?
                             # Let's verify if save_hk_valuation_to_daily supports dividend? No.
                             # Simple inline update for today/latest
                             try:
                                 latest_rec = session.exec(
                                     select(MarketDataDaily).where(
                                         MarketDataDaily.symbol == item.symbol, 
                                         MarketDataDaily.market == 'HK'
                                     ).order_by(MarketDataDaily.timestamp.desc())
                                 ).first()
                                 if latest_rec:
                                     latest_rec.dividend_yield = div_yield
                                     latest_rec.updated_at = datetime.now()
                                     session.add(latest_rec)
                                     session.commit()
                                     print(f"  💾 已保存股息率: {div_yield}%")
                             except Exception as e:
                                 logger.error(f"  ❌ 保存股息率失败: {e}")

                        hk_count += 1


                    elif item.market == 'US':
                        print(f"🔄 处理美股: {item.symbol}")
                        # 1. 实时估值 (yfinance)
                        valuation = fetch_us_valuation_yfinance(item.symbol)
                        if valuation:
                            updated = save_us_valuation_to_daily(item.symbol, valuation, session)
                            if updated > 0:
                                us_count += 1 
                        
                        # 2. 历史估值 (FMP)
                        df_fmp = fetch_us_valuation_history_fmp(item.symbol, limit=20) 
                        
                        if df_fmp is not None and not df_fmp.empty:
                            save_us_historical_valuation_to_daily(item.symbol, df_fmp, session)
                            
                            # 3. 推导 (Base on FMP)
                            try:
                                daily_prices = pd.read_sql(
                                    select(MarketDataDaily.timestamp, MarketDataDaily.close)
                                    .where(MarketDataDaily.symbol == item.symbol)
                                    .order_by(MarketDataDaily.timestamp),
                                    engine
                                )
                                if not daily_prices.empty:
                                    daily_prices['timestamp'] = pd.to_datetime(daily_prices['timestamp'])
                                    daily_prices.set_index('timestamp', inplace=True)
                                    
                                    derived_pe = derive_daily_pe_from_points(item.symbol, daily_prices, df_fmp)
                                    if not derived_pe.empty:
                                        logger.info(f"  📈 [Derivation] US: 推导并保存 {len(derived_pe)} 条 PE TTM (Based on FMP)")
                                        df_derived = pd.DataFrame({'date': derived_pe.index.strftime('%Y-%m-%d'), 'pe_ttm': derived_pe.values})
                                        save_us_historical_valuation_to_daily(item.symbol, df_derived, session)
                            except Exception as e:
                                logger.error(f"  ❌ 美股 FMP 推导逻辑异常: {e}")
                                
                        # 4. [New Fallback] 如果 FMP 失败 (df_fmp is None), 尝试本地财报推导
                        if df_fmp is None or df_fmp.empty:
                            logger.info(f"  ⚠️  FMP 失败或无数据，尝试本地财报推导...")
                            derived_local = derive_pe_ttm_from_fundamentals(item.symbol, session)
                            if derived_local is not None and not derived_local.empty:
                                logger.info(f"  📈 [Fallback] US: 使用本地财报推导 {len(derived_local)} 条 PE TTM")
                                save_us_historical_valuation_to_daily(item.symbol, derived_local, session)

                    # 避免请求过快

                    # 避免请求过快
                    import time
                    time.sleep(0.5)

                except Exception as e:
                    logger.error(f"❌ 处理失败 {item.symbol}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue

            # 总结
            print("\n" + "=" * 80)
            print("📋 获取完成统计")
            print("=" * 80)
            print(f"✅ A股成功: {cn_count} 个")
            print(f"✅ 港股成功: {hk_count} 个")
            print(f"✅ 美股成功: {us_count} 个")
            print("=" * 80)
            
    except Exception as e:
         logger.error(f"❌ 程序执行出错: {e}")
         import traceback
         traceback.print_exc()

if __name__ == "__main__":
    main()
