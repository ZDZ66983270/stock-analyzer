"""
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# ⚠️ WARNING: CORE VALUATION LOGIC - DO NOT MODIFY WITHOUT APPROVAL
# ⚠️ WARNING: CORE VALUATION LOGIC - DO NOT MODIFY WITHOUT APPROVAL
# ⚠️ WARNING: CORE VALUATION LOGIC - DO NOT MODIFY WITHOUT APPROVAL
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

Financials Fetcher (财报数据获取)
===============================
负责爬取和解析原始财报数据，填充 `FinancialFundamentals` 表。
关键字段: `net_income_common_ttm`, `shares_diluted`, `data_source`.

逻辑 1: **智能合并策略 (Smart Merge Logic)**
------------------------------------
- 函数: `upsert_financials`
- 规则: 
  - 如果数据库中已存在 `report_type='annual'` (年报) 数据，
  - 且新数据为 `report_type='quarterly'` (季报)，
  - **拒绝更新**。防止高质量的年报数据被低质量/不完整的季报数据覆盖。

逻辑 2: **Yahoo Finance 解析 (US/HK Fallback)**
------------------------------------------
- 使用 `yfinance` 获取 Quarterly/Annual Financials。
- **难点**: Yahoo 返回的 DataFrame 列名为 `Timestamp` 对象，且不同市场字段名不一致 (e.g., 'Net Income' vs 'NetIncome')。
- **处理**: 使用 `get_val` 辅助函数进行多 Key 匹配和日期格式化。

逻辑 3: **FMP Cloud 解析 (US Primary)**
----------------------------------
- 接口: `/income-statement`, `/balance-sheet-statement`, `/cash-flow-statement`。
- **优势**: 直接提供 `netIncomeForCommonStockholders` (归母) 和 `weightedAverageShsOutDil` (稀释股本)。
- **处理**: 分别获取三张表，在内存中按 (Date, Type) 进行 Merging，最后统一入库。

逻辑 4: **AkShare 解析 (CN/HK)**
---------------------------
- **A 股**: 使用 `stock_financial_abstract` 获取摘要数据。需手动解析 '20231231' 为 Annual，'20230930' 为 Quarterly。
- **港股**: 使用 `stock_financial_hk_analysis_indicator_em` (年报) + `stock_financial_hk_report_em` (详情)。
- **特殊**: 港股数据通常是 Accumulated (累计)，在 `valuation_calculator` 中会触发还原逻辑。
"""

import sys
import yfinance as yf
import pandas as pd
from datetime import datetime
from sqlmodel import Session, select
from backend.database import engine
from backend.models import Watchlist, FinancialFundamentals
from backend.symbol_utils import get_yahoo_symbol
import logging

# Suppress repetitive SQL logs
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

FMP_API_KEY = "yytaAKONtPbR5cBcx9azLeqlovaWDRQm"

def get_safe_float(data, key):
    try:
        val = data.get(key)
        return float(val) if val is not None else None
    except:
        return None

def upsert_financials(session, data):
    if not data: return
    
    # Check exist
    existing = session.exec(select(FinancialFundamentals).where(
        FinancialFundamentals.symbol == data['symbol'],
        FinancialFundamentals.as_of_date == data['as_of_date']
    )).first()
    
    if existing:
        # === Smart Merge Logic ===
        # Priority: Annual > Quarterly
        existing_type = getattr(existing, 'report_type', '')
        new_type = data.get('report_type', '')
        
        # If Existing is Annual and New is Quarterly -> STOP (Don't overwrite high-quality data with low-quality)
        if existing_type == 'annual' and new_type == 'quarterly':
            # print(f"   🛡️ protecting Annual {data['symbol']} {data['as_of_date']} from Quarterly overwrite")
            return
            
        print(f"   🔄 Updating {data['symbol']} {data['as_of_date']} ({existing_type} -> {new_type})...")
        for k, v in data.items():
            if v is not None:
                setattr(existing, k, v)
    else:
        print(f"   ➕ Inserting {data['symbol']} {data['as_of_date']} ({data.get('report_type')})...")
        new_rec = FinancialFundamentals(**data)
        session.add(new_rec)

def fetch_yahoo_financials(canonical_id, market='US', report_type='annual'):
    """
    Fetch financials from Yahoo Finance.
    Args:
        canonical_id: Canonical ID (e.g. 'HK:STOCK:00700', 'US:STOCK:AAPL')
        market: Market identifier ('HK', 'CN', 'US')
        report_type: 'annual' or 'quarterly'
    Returns a LIST of dicts mapping to our model fields.
    """
    symbol = canonical_id.split(':')[-1] if ':' in canonical_id else canonical_id
    results = []
    try:
        yf_symbol = get_yahoo_symbol(symbol, market)
        
        print(f"   📥 Fetching Yahoo {report_type} financials for {yf_symbol}...")

        ticker = yf.Ticker(yf_symbol)
        
        # 1. Fetch Dataframes (Annual or Quarterly)
        try:
            if report_type == 'quarterly':
                inc = ticker.quarterly_financials
                bs = ticker.quarterly_balance_sheet
                cf = ticker.quarterly_cashflow
            else:
                inc = ticker.financials
                bs = ticker.balance_sheet
                cf = ticker.cashflow
        except Exception:
            return []

        # 2. Iterate through common columns (dates)
        if inc.empty:
            return []
            
        dates = inc.columns
        for date in dates:
            date_str = date.strftime('%Y-%m-%d')
            
            # Helper to extract from DF with robust key/date handling
            def get_val(df_list, keys, col_date):
                if not isinstance(keys, list): keys = [keys]
                
                # Check column existence
                target_col = col_date
                if col_date not in df_list.columns:
                    # try fallback by checking string representation
                    found_col = None
                    try:
                        target_str = col_date.strftime('%Y-%m-%d')
                        for c in df_list.columns:
                             if hasattr(c, 'strftime') and c.strftime('%Y-%m-%d') == target_str:
                                 found_col = c
                                 break
                    except: pass
                    
                    if found_col:
                        target_col = found_col
                    else:
                        return None
                
                # Try keys
                for k in keys:
                    if k in df_list.index:
                        try:
                            val = df_list.loc[k, target_col]
                            if pd.notnull(val):
                                return float(val)
                        except:
                            continue
                return None

            # 获取股息率(仅最新年度有效)
            dividend_yield = None
            try:
                dividend_yield = ticker.info.get('dividendYield')
            except:
                pass
            
            # Date filtering for Quarterly: Last 2 years only
            if report_type == 'quarterly':
                try:
                    dt = datetime.strptime(date_str, '%Y-%m-%d')
                    if dt.year < datetime.now().year - 2:
                        continue 
                except: pass

            data = {
                'symbol': canonical_id,  # 使用 Canonical ID
                'as_of_date': date_str,
                'report_type': report_type,  
                'data_source': f'yahoo-{report_type}',
                'currency': ticker.info.get('financialCurrency') or ticker.info.get('currency'),
                
                # Profitability
                'revenue_ttm': get_val(inc, ['Total Revenue', 'Operating Revenue', 'Revenue'], date), 
                'net_income_ttm': get_val(inc, ['Net Income', 'NetIncome'], date),
                'net_income_common_ttm': get_val(inc, ['Net Income Common Stockholders', 'Net Income'], date), # VERA Pro
                'eps': get_val(inc, ['Basic EPS', 'BasicEPS'], date), 
                'eps_diluted': get_val(inc, ['Diluted EPS', 'DilutedEPS'], date), # VERA Pro
                'shares_diluted': get_val(inc, ['Diluted Average Shares', 'Basic Average Shares'], date), # VERA Pro
                
                # Cash Flow
                'operating_cashflow_ttm': get_val(cf, ['Operating Cash Flow', 'Total Cash From Operating Activities'], date),
                'free_cashflow_ttm': get_val(cf, ['Free Cash Flow'], date),
                
                # Balance Sheet
                'total_assets': get_val(bs, ['Total Assets'], date),
                'total_liabilities': get_val(bs, ['Total Liabilities Net Minority Interest', 'Total Liabilities'], date),
                'total_debt': get_val(bs, ['Total Debt'], date),
                'cash_and_equivalents': get_val(bs, ['Cash And Cash Equivalents', 'Cash', 'Total Cash'], date),
                
                # Ratios
                'debt_to_equity': None, 
                'current_ratio': None,
                'dividend_yield': dividend_yield if report_type == 'annual' else None, # Keep div yield with annual
                'dividend_amount': abs(get_val(cf, ['Cash Dividends Paid', 'Common Stock Dividend Paid'], date) or 0) # ABS of Cash Outflow
            }
            
            # Manual Net Debt
            if data['total_debt'] is not None and data['cash_and_equivalents'] is not None:
                data['net_debt'] = data['total_debt'] - data['cash_and_equivalents']

            results.append(data)

        return results

    except Exception as e:
        print(f"   ❌ Yahoo fetch error for {symbol}: {e}")
    except Exception as e:
        print(f"   ❌ Yahoo fetch error for {symbol}: {e}")
        return []

def fetch_fmp_financials(canonical_id, market='US'):
    """
    Fetch financials from FMP Cloud (US Stocks).
    Fetches Income Statement, Balance Sheet, Cash Flow (Annual & Quarterly).
    Populates new VERA Pro fields: Net Income Common, Diluted Shares, Filing Date.
    """
    if market != 'US': return []
    
    import requests
    symbol = canonical_id.split(':')[-1] if ':' in canonical_id else canonical_id
    
    results_map = {} # Key: (as_of_date, report_type) -> data_dict
    
    endpoints = [
        ('income-statement', 'income'),
        ('balance-sheet-statement', 'bs'),
        ('cash-flow-statement', 'cf')
    ]
    
    print(f"   🌊 Calling FMP Financials for {symbol}...")
    
    for ep, tag in endpoints:
        for period in ['annual', 'quarter']: 
            # period for API: year vs quarter
            # FMP uses 'period=quarter' query param
            url = f"https://financialmodelingprep.com/api/v3/{ep}/{symbol}?apikey={FMP_API_KEY}&limit=20"
            if period == 'quarter':
                url += "&period=quarter"
                
            try:
                # print(f"      Fetching {ep} ({period})...")
                res = requests.get(url, timeout=10)
                data_list = res.json()
                if not data_list or isinstance(data_list, dict): continue # Handle error dict
                
                for item in data_list:
                    date_str = item.get('date') # YYYY-MM-DD
                    if not date_str: continue
                    
                    rep_type = 'quarterly' if period == 'quarter' else 'annual'
                    key = (date_str, rep_type)
                    
                    if key not in results_map:
                        results_map[key] = {
                            'symbol': canonical_id,
                            'as_of_date': date_str,
                            'report_type': rep_type,
                            'data_source': f'fmp-{rep_type}',
                            'currency': item.get('reportedCurrency') or 'USD',
                            'filing_date': item.get('fillingDate') or item.get('acceptedDate', '')[:10]  # PIT
                        }
                    
                    rec = results_map[key]
                    
                    # Income Statement
                    if tag == 'income':
                        rec['revenue_ttm'] = get_safe_float(item, 'revenue')
                        rec['net_income_ttm'] = get_safe_float(item, 'netIncome') # Raw period NI
                        
                        # ✅ VERA Pro Fields
                        rec['net_income_common_ttm'] = get_safe_float(item, 'netIncomeForCommonStockholders')
                        rec['eps'] = get_safe_float(item, 'eps')
                        rec['eps_diluted'] = get_safe_float(item, 'epsdiluted')
                        rec['shares_diluted'] = get_safe_float(item, 'weightedAverageShsOutDil')
                        
                    # Balance Sheet
                    elif tag == 'bs':
                        rec['total_assets'] = get_safe_float(item, 'totalAssets')
                        rec['total_liabilities'] = get_safe_float(item, 'totalLiabilities')
                        rec['total_debt'] = get_safe_float(item, 'totalDebt')
                        rec['cash_and_equivalents'] = get_safe_float(item, 'cashAndCashEquivalents')
                        
                    # Cash Flow
                    elif tag == 'cf':
                        rec['operating_cashflow_ttm'] = get_safe_float(item, 'operatingCashFlow')
                        rec['free_cashflow_ttm'] = get_safe_float(item, 'freeCashFlow')
                        rec['dividend_amount'] = abs(get_safe_float(item, 'dividendsPaid') or 0)
            
            except Exception as e:
                print(f"      ⚠️ FMP Fetch Error ({ep}): {e}")
                
    # Post-process Net Debt
    final_list = []
    for k, rec in results_map.items():
        if rec.get('total_debt') is not None and rec.get('cash_and_equivalents') is not None:
            rec['net_debt'] = rec['total_debt'] - rec['cash_and_equivalents']
        final_list.append(rec)
        
    return final_list

def fetch_akshare_cn_financials_abstract(canonical_id):
    """
    Fetch CN financials using AkShare 'stock_financial_abstract' (Sina based).
    Returns list of dicts (Mixed Annual and Quarterly).
    Fields are derived from abstract indicators.
    """
    import akshare as ak
    symbol = canonical_id.split(':')[-1]
    # Remove .SS or .SZ suffix if present? Usually AkShare takes 6 digits.
    symbol = symbol.split('.')[0]
    
    print(f"   🌊 Calling AkShare Abstract for {symbol}...")
    try:
        df = ak.stock_financial_abstract(symbol=symbol)
        if df is None or df.empty:
            return []
            
        # df shape: rows=indicators, cols=dates (plus '选项','指标')
        # We need to iterate columns describing dates.
        
        # Extract Indicator Map
        # 营业总收入 -> Revenue
        # 归母净利润 -> Net Income
        # 经营现金流量净额 -> OCF
        # 股东权益合计(净资产) -> Equity
        # 资产负债率 -> Debt Ratio (Calculate Assets)
        
        # Transpose or simple lookup?
        # Lookup is easier.
        
        # Get date columns
        cols = [c for c in df.columns if c not in ['选项', '指标']]
        
        results = []
        for d_str in cols:
            # d_str format: YYYYMMDD e.g. 20250930
            if not d_str.isdigit() or len(d_str) != 8:
                continue
            
            # Parse Date
            as_of_date = f"{d_str[:4]}-{d_str[4:6]}-{d_str[6:]}"
            
            # Determine Report Type
            report_type = 'annual' if d_str.endswith('1231') else 'quarterly'
            
            # Strict user limits:
            # Quarterly: Last 2 years (e.g. 2026, 2025, 2024)
            # Annual: Last 10 years (e.g. 2026...2016)
            
            dt_year = int(d_str[:4])
            current_year = datetime.now().year
            
            if report_type == 'quarterly':
                if dt_year < (current_year - 2):
                    continue
            else:
                # Annual
                if dt_year < (current_year - 10):
                    continue

            # Helper to get value for this date and indicator
            def get_indic(name):
                row = df[df['指标'] == name]
                if row.empty: return None
                try:
                    val = row.iloc[0][d_str]
                    return float(val)
                except:
                    return None
            
            revenue = get_indic('营业总收入')
            net_income = get_indic('归母净利润') or get_indic('净利润')
            eps = get_indic('基本每股收益') # Added: Extract Basic EPS
            ocf = get_indic('经营现金流量净额')
            equity = get_indic('股东权益合计(净资产)')
            debt_ratio_pct = get_indic('资产负债率') # in Percent
            
            # Derived Assets
            total_assets = None
            total_liabilities = None
            if equity is not None and debt_ratio_pct is not None:
                # Assets = Equity / (1 - Ratio)
                # Ensure ratio is valid (0 to 100)
                if debt_ratio_pct < 100:
                    ratio = debt_ratio_pct / 100.0
                    if 1 - ratio > 0.001:
                        total_assets = equity / (1 - ratio)
                        total_liabilities = total_assets * ratio
            
            data = {
                'symbol': canonical_id,
                'as_of_date': as_of_date,
                'report_type': report_type,
                'data_source': f'akshare-abstract-{report_type}',
                'currency': 'CNY',
                'revenue_ttm': revenue,
                'net_income_ttm': net_income,
                'eps': eps, # Added
                'operating_cashflow_ttm': ocf,
                'total_assets': total_assets,
                'total_liabilities': total_liabilities,
                
                # Missing details
                'total_debt': None,
                'cash_and_equivalents': None,
                'debt_to_equity': None,
                'dividend_yield': None,
                'dividend_amount': None # Abstract doesn't provide Total Div Paid easily
            }
            results.append(data)
            
        return results

    except Exception as e:
        print(f"   ❌ AkShare Abstract fetch error for {symbol}: {e}")
        return []

def fetch_akshare_hk_financials(canonical_id, preferred_currency='HKD'):
    """
    Fetch HK financials using AkShare (returns historical annual data).
    Args:
        canonical_id: Canonical ID (e.g. 'HK:STOCK:00700')
    """
    import akshare as ak
    code = canonical_id.split(':')[-1] if ':' in canonical_id else canonical_id
    code = code.replace('.HK', '')
    print(f"   🌊 Calling AkShare stock_financial_hk_analysis_indicator_em(symbol='{code}')...")
    try:
        df = ak.stock_financial_hk_analysis_indicator_em(symbol=code, indicator="年度")
        if df is None or df.empty:
            return []
            
        results = []
        for _, row in df.iterrows():
            start_date = row.get('START_DATE') or row.get('RDATE')
            if not start_date: continue
            
            date_str = str(start_date)
            year_str = date_str.split('-')[0]
            if not year_str.isdigit(): continue
                
            as_of_date = f"{year_str}-12-31"
            
            data = {
                'symbol': canonical_id,
                'as_of_date': as_of_date,
                'report_type': 'annual',
                'data_source': 'akshare-hk-annual',
                'currency': preferred_currency, 
                'revenue_ttm': get_safe_float(row, 'OPERATE_INCOME'),
                'net_income_ttm': get_safe_float(row, 'HOLDER_PROFIT'),
                'eps': get_safe_float(row, 'BASIC_EPS'), # Added for VERA PE Calc
                'total_assets': None,
                'total_liabilities': None,
                'operating_cashflow_ttm': None,
                'dividend_yield': None
            }
            results.append(data)
        return results
    except Exception as e:
        print(f"   ❌ AkShare HK fetch error: {e}")
        return []

def fetch_akshare_hk_financials_details(canonical_id):
    """
    Fetch HK financials details (Balance Sheet, Cash Flow) using AkShare 'stock_financial_hk_report_em'.
    Returns list of dicts.
    """
    import akshare as ak
    import pandas as pd
    
    code = canonical_id.split(':')[-1] if ':' in canonical_id else canonical_id
    code = code.replace('.HK', '') # Ensure 5 digits
    
    print(f"   🌊 Calling AkShare Detailed Reports for {code}...")
    
    results_map = {} # Date -> Dict
    
    try:
        # 1. Balance Sheet (资产负债表)
        try:
            df_bs = ak.stock_financial_hk_report_em(stock=code, symbol="资产负债表", indicator="年度")
            if df_bs is not None and not df_bs.empty:
                # Pivot: REPORT_DATE as index, STD_ITEM_NAME as columns
                # Filter relevant columns
                relevant_cols = ['REPORT_DATE', 'STD_ITEM_NAME', 'AMOUNT']
                df_bs = df_bs[relevant_cols]
                
                # Iterate and populate
                for _, row in df_bs.iterrows():
                    d_str = str(row['REPORT_DATE']).split(' ')[0] # YYYY-MM-DD
                    if d_str not in results_map:
                        results_map[d_str] = {'as_of_date': d_str, 'symbol': canonical_id, 'report_type': 'annual', 'data_source': 'akshare-hk-details'}
                    
                    item = row['STD_ITEM_NAME']
                    amt = get_safe_float(row, 'AMOUNT')
                    
                    if item == '总资产': results_map[d_str]['total_assets'] = amt
                    elif item == '总负债': results_map[d_str]['total_liabilities'] = amt
                    elif item == '现金及等价物': results_map[d_str]['cash_and_equivalents'] = amt
                    elif item == '借款总额': results_map[d_str]['total_debt'] = amt # Try exact match
                    
        except Exception as e:
            print(f"    ⚠️ BS Fetch Error: {e}")

        # 2. Cash Flow (现金流量表)
        try:
            df_cf = ak.stock_financial_hk_report_em(stock=code, symbol="现金流量表", indicator="年度")
            if df_cf is not None and not df_cf.empty:
                relevant_cols = ['REPORT_DATE', 'STD_ITEM_NAME', 'AMOUNT']
                df_cf = df_cf[relevant_cols]
                
                for _, row in df_cf.iterrows():
                    d_str = str(row['REPORT_DATE']).split(' ')[0]
                    if d_str not in results_map:
                         results_map[d_str] = {'as_of_date': d_str, 'symbol': canonical_id, 'report_type': 'annual', 'data_source': 'akshare-hk-details'}
                    
                    item = row['STD_ITEM_NAME']
                    amt = get_safe_float(row, 'AMOUNT')
                    
                    if item == '经营业务现金净额': results_map[d_str]['operating_cashflow_ttm'] = amt
                    elif item == '已付股息(融资)': results_map[d_str]['dividend_amount'] = abs(amt) if amt else 0
                    
        except Exception as e:
            print(f"    ⚠️ CF Fetch Error: {e}")

        # Post-process: Calculate Net Debt
        for date_key, data in results_map.items():
            t_debt = data.get('total_debt')
            cash = data.get('cash_and_equivalents')
            if t_debt is not None and cash is not None:
                data['net_debt'] = t_debt - cash

        return list(results_map.values())

    except Exception as e:
        print(f"   ❌ AkShare HK Details fetch error: {e}")
        return []

import argparse

def main():
    parser = argparse.ArgumentParser(description='Fetch Financial Data')
    parser.add_argument('--market', type=str, choices=['CN', 'HK', 'US', 'ALL'], help='Market to fetch (CN, HK, US, ALL)')
    parser.add_argument('--limit', type=int, default=10, help='Limit per stock')
    args = parser.parse_args()

    selected_market = args.market

    # Interactive Menu if no argument provided
    if not selected_market:
        print("\n" + "="*50)
        print("📊 Select Market to Fetch Financials")
        print("="*50)
        print("  1. CN (A-Share)")
        print("  2. HK (Hong Kong)")
        print("  3. US (United States)")
        print("  0. ALL Markets")
        print("="*50)
        
        try:
            choice = input("Enter your choice (0-3) [default: 0]: ").strip()
        except EOFError:
            choice = '0' # Default for non-interactive
            
        if choice == '1': selected_market = 'CN'
        elif choice == '2': selected_market = 'HK'
        elif choice == '3': selected_market = 'US'
        else: selected_market = 'ALL'

    print(f"\n🚀 Starting Financials Fetch (Market: {selected_market})...")
    
    with Session(engine) as session:
        # Build Query
        stmt = select(Watchlist)
        if selected_market != 'ALL':
            stmt = stmt.where(Watchlist.market == selected_market)
            
        stocks = session.exec(stmt).all()
        
        total_stocks = len(stocks)
        print(f"📋 Found {total_stocks} assets to process.")
        
        for idx, stock in enumerate(stocks, 1):
            # Skip Indices, Crypto and ETFs (No corporate financial reports)
            if ':INDEX:' in stock.symbol or ':CRYPTO:' in stock.symbol or ':ETF:' in stock.symbol:
                continue
            
            # Additional fallback for old formats
            if stock.symbol.startswith('^') or stock.symbol.endswith('-USD'):
                continue

            print(f"\n[{idx}/{total_stocks}] Processing {stock.symbol} ({stock.name})...")
            
            data_list = []
            
            # === MARKET DISPATCH ===
            if stock.market == 'CN':
                 # AKShare Single Stock (Abstract)
                 data_list.extend(fetch_akshare_cn_financials_abstract(stock.symbol))
                 
                 # Yahoo Fallback? (Usually not needed if AkShare works, but purely supplemental)
                 # Skipping Yahoo for CN to save time as per user request.

            elif stock.market == 'HK':
                  # 1. AkShare (Annual - Indicator)
                  # Detect Currency First
                  # Use get_yahoo_symbol to ensure correct format (e.g. 0700.HK)
                  try:
                      code_raw = stock.symbol.split(':')[-1]
                      yf_sym_cur = get_yahoo_symbol(code_raw, 'HK')
                      t = yf.Ticker(yf_sym_cur)
                      cur = t.info.get('financialCurrency') or 'HKD'
                  except: cur = 'HKD'
                  
                  data_list.extend(fetch_akshare_hk_financials(stock.symbol, preferred_currency=cur))
                  
                  # 2. AkShare (Annual - Details for BS/CF) [NEW]
                  data_list.extend(fetch_akshare_hk_financials_details(stock.symbol))
                  
                  # 3. Yahoo (Quarterly) - Fetch First
                  print(f"   📥 Fetching HK Quarterly for {stock.symbol}...")
                  data_list.extend(fetch_yahoo_financials(stock.symbol, market='HK', report_type='quarterly'))

                  # 4. Yahoo (Annual) [NEW - Enabled for Div/History] - Fetch Last (Precedence)
                  print(f"   📥 Fetching HK Yahoo Annual for {stock.symbol}...")
                  data_list.extend(fetch_yahoo_financials(stock.symbol, market='HK', report_type='annual'))

            elif stock.market == 'US':
                 # FMP (High Quality) - Fetch First
                 data_list.extend(fetch_fmp_financials(stock.symbol, market='US'))
                 
                 # Yahoo Annual + Quarterly (Fallback / Supplement)
                 yh_annual = fetch_yahoo_financials(stock.symbol, market='US', report_type='annual')
                 yh_quarter = fetch_yahoo_financials(stock.symbol, market='US', report_type='quarterly')
                 
                 # Append Yahoo First
                 # Reset list order to ensure FMP priority (Last update wins in upsert logic? Or first?)
                 # Upsert logic: "if existing... update fields".
                 # So if we process Yahoo FIRST, then FMP, FMP will overwrite fields if they exist.
                 # This is what we want (FMP is better).
                 
                 data_list = []
                 data_list.extend(yh_annual)
                 data_list.extend(yh_quarter)
                 data_list.extend(fetch_fmp_financials(stock.symbol, market='US'))
            
            # === SAVE ===
            if data_list:
                # Sort by date
                data_list.sort(key=lambda x: x['as_of_date'], reverse=True)
                print(f"   ✅ Saving {len(data_list)} records for {stock.symbol}...")
                for d in data_list:
                    upsert_financials(session, d)
                session.commit()
            else:
                print(f"   ℹ️ No data found for {stock.symbol}")
                
    print("\n✅ Financials fetch complete.")

if __name__ == "__main__":
    sys.path.insert(0, ".")
    main()
