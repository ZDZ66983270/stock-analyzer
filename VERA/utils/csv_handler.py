import pandas as pd
import sqlite3
from db.connection import get_connection
from utils.canonical_resolver import resolve_canonical_symbol

def parse_and_import_csv(uploaded_file, fallback_id=None, fallback_name=None, mode="overwrite", start_date=None, end_date=None, target_assets=None):
    """
    解析用户上传的 CSV 并存入 vera_price_cache
    核心规则：
    1. 仅使用已有的符号映射关系（不创建新映射）
    2. 未映射的代码会被跳过并报告给用户
    3. 返回详细的导入摘要
    
    Args:
        mode: "overwrite" (更新已有记录) or "incremental" (仅插入新记录)
    """
    try:
        # 1. 读取 CSV
        df = pd.read_csv(uploaded_file)
        
        # 2. 列名清洗（启发式匹配）
        raw_columns = list(df.columns)
        df.columns = [c.strip().lower() for c in df.columns]
        
        # 映射逻辑
        mapping = {
            'date': ['date', 'time', 'timestamp', '日期'],
            'close': ['close', 'adj close', '收盘价', '成交价'],
            'open': ['open', '开盘价'],
            'high': ['high', '最高价'],
            'low': ['low', '最低价'],
            'volume': ['volume', '成交量'],
            'symbol': ['symbol', 'ticker', 'code', '代码', '标的']
        }
        
        # 匹配必需列
        date_col = next((c for c in df.columns if any(k == c for k in mapping['date'])), None)
        close_col = next((c for c in df.columns if any(k == c for k in mapping['close'])), None)
        symbol_col = next((c for c in df.columns if any(k == c for k in mapping['symbol'])), None)
        
        if not date_col or not close_col:
            return False, f"CSV 缺少必需列 (需包含日期和收盘价)。已发现列: {raw_columns}"
            
        # 准备清洗后的基础数据
        cleaned_data = pd.DataFrame()
        cleaned_data['trade_date'] = pd.to_datetime(df[date_col]).dt.strftime('%Y-%m-%d')
        cleaned_data['close'] = pd.to_numeric(df[close_col], errors='coerce')
        
        # 处理 Symbol
        if symbol_col:
            cleaned_data['raw_symbol'] = df[symbol_col].astype(str).str.strip().str.upper()
        else:
            if not fallback_id:
                return False, "CSV 中未发现代码列，且未提供备用代码。"
            cleaned_data['raw_symbol'] = fallback_id.strip().upper()

        # 匹配可选列
        for col in ['open', 'high', 'low']:
            match = next((c for c in df.columns if any(k == c for k in mapping[col])), None)
            cleaned_data[col] = pd.to_numeric(df[match], errors='coerce') if match else cleaned_data['close']
            
        vol_match = next((c for c in df.columns if any(k == c for k in mapping['volume'])), None)
        cleaned_data['volume'] = pd.to_numeric(df[vol_match], errors='coerce') if vol_match else 0

        # 新增指标映射支持 (v2 同步扩展)
        extended_metrics = {
            'pe': ['pe', 'pe_static', '市盈率', '静态市盈率'],
            'pe_ttm': ['pe_ttm', 'ttm_pe', '动态PE', '动态市盈率', '市盈率TTM'],
            'pb': ['pb', 'pb_ratio', '市净率'],
            'ps': ['ps', 'ps_ttm', '市销率'],
            'eps': ['eps', 'eps_ttm', '每股收益'],
            'dividend_yield': ['dividend_yield', '股息率'],
            'turnover': ['turnover', '换手率'],
            'market_cap': ['market_cap', '市值', '总市值'],
            'pct_change': ['pct_change', '百分比涨跌', '涨跌幅'],
            'prev_close': ['prev_close', '前收盘价']
        }
        for col, keys in extended_metrics.items():
            match = next((c for c in df.columns if any(k == c for k in keys)), None)
            if match:
                cleaned_data[col] = pd.to_numeric(df[match], errors='coerce')
            else:
                cleaned_data[col] = None
        
        # 清洗无效行
        cleaned_data = cleaned_data.dropna(subset=['trade_date', 'close', 'raw_symbol'])
        
        # Date Range Filtering
        if start_date:
            cleaned_data = cleaned_data[cleaned_data['trade_date'] >= str(start_date)]
        if end_date:
            cleaned_data = cleaned_data[cleaned_data['trade_date'] <= str(end_date)]

        
        if cleaned_data.empty:
            return False, "清洗后数据为空，请检查 CSV 内容格式。"

        # 3. 解析所有symbol到canonical ID（通过已有映射）
        conn = get_connection()
        try:
            symbols_in_csv = cleaned_data['raw_symbol'].unique()
            symbol_resolution = {}  # {raw_symbol: canonical_id or None}
            
            for raw_sym in symbols_in_csv:
                try:
                    canonical = resolve_canonical_symbol(conn, raw_sym)
                    symbol_resolution[raw_sym] = canonical
                except:
                    symbol_resolution[raw_sym] = None  # 未找到映射
            
            # Asset Filter Logic
            if target_assets:
                # Only keep mappings where the canonical ID is in the target list
                symbol_resolution = {k: v for k, v in symbol_resolution.items() if v in target_assets}

            
            # 统计
            mapped_symbols = {k: v for k, v in symbol_resolution.items() if v}
            unmapped_symbols = {k for k, v in symbol_resolution.items() if not v}
            
            # 过滤：只保留已映射的数据
            cleaned_data['canonical_id'] = cleaned_data['raw_symbol'].map(symbol_resolution)
            valid_data = cleaned_data[cleaned_data['canonical_id'].notna()].copy()
            skipped_data = cleaned_data[cleaned_data['canonical_id'].isna()]
            
            if valid_data.empty:
                return False, f"❌ 所有代码均未在系统中注册，无法导入。\n\n未注册代码: {', '.join(unmapped_symbols)}\n\n请先在「资产管理」中注册这些资产。"
            
            # 准备写入数据
            valid_data['symbol'] = valid_data['canonical_id']  # price_cache使用canonical作为symbol
            valid_data['source'] = 'User_Upload_CSV'
            
            # 动态选择列，确保新字段被包含
            cols_to_save = ['symbol', 'trade_date', 'open', 'high', 'low', 'close', 'volume', 'source',
                            'pe', 'pe_ttm', 'pb', 'ps', 'eps', 'dividend_yield', 'turnover', 'market_cap', 
                            'pct_change', 'prev_close']
            # 只取 valid_data 中存在的列
            actual_cols = [c for c in cols_to_save if c in valid_data.columns]
            valid_data = valid_data[actual_cols]
            
            # 4. 写入数据库（分批避免 SQL 变量超限）
            BATCH_SIZE = 100  # 每批100行，避免超过SQLite 999变量限制
            
            # 统计每个资产的新增和重复
            asset_stats = {}  # {canonical_id: {'total': X, 'inserted': Y, 'duplicate': Z}}
            
            for canonical_id, group in valid_data.groupby('symbol'):
                total_rows = len(group)
                inserted = 0
                duplicated = 0
                
                # 分批插入
                for i in range(0, len(group), BATCH_SIZE):
                    batch = group.iloc[i:i+BATCH_SIZE]
                    
                    # 使用 INSERT OR IGNORE 并检查实际插入行数 (动态构建 SQL 以适配新字段)
                    cursor = conn.cursor()
                    col_names = ", ".join(actual_cols)
                    placeholders = ", ".join(["?"] * len(actual_cols))
                    
                    # Mode-dependent SQL logic
                    if mode == "incremental":
                        # Incremental: Skip existing records
                        sql = f"""
                            INSERT OR IGNORE INTO vera_price_cache ({col_names})
                            VALUES ({placeholders})
                        """
                    else:
                        # Overwrite: Update existing records
                        update_clause = ", ".join([f"{c} = excluded.{c}" for c in actual_cols if c not in ['symbol', 'trade_date']])
                        sql = f"""
                            INSERT INTO vera_price_cache ({col_names})
                            VALUES ({placeholders})
                            ON CONFLICT(symbol, trade_date) DO UPDATE SET
                            {update_clause}
                        """
                    
                    cursor.executemany(sql, [tuple(row) for _, row in batch.iterrows()])
                    
                    actual_inserted = cursor.rowcount
                    inserted += actual_inserted
                    duplicated += (len(batch) - actual_inserted)
                
                asset_stats[canonical_id] = {
                    'total': total_rows,
                    'inserted': inserted,
                    'duplicate': duplicated
                }
            
            conn.commit()
            
            # 5. 生成详细报告
            total_inserted = sum(s['inserted'] for s in asset_stats.values())
            total_duplicate = sum(s['duplicate'] for s in asset_stats.values())
            
            mode_label = "全覆盖" if mode == "overwrite" else "增量添加"
            report_lines = [f"✅ CSV 导入完成 (模式: {mode_label})\n"]
            
            # 先显示汇总
            report_lines.append(f"**📊 汇总**")
            report_lines.append(f"  - 成功导入资产: **{len(mapped_symbols)}** 个")
            report_lines.append(f"  - 新增记录: **{total_inserted}** 条")
            
            if mode == "incremental":
                report_lines.append(f"  - 跳过已存在: **{total_duplicate}** 条")
            else:
                report_lines.append(f"  - 更新已有: **{total_duplicate}** 条")
            report_lines.append("")  # 空行分隔
            
            # 再显示分项
            if len(mapped_symbols) > 0:
                report_lines.append(f"**📋 分项详情**\n")
                for raw, canonical in mapped_symbols.items():
                    stats = asset_stats.get(canonical, {'total': 0, 'inserted': 0, 'duplicate': 0})
                    report_lines.append(f"**{raw}** → `{canonical}`")
                    report_lines.append(f"  - CSV总行数: {stats['total']}")
                    report_lines.append(f"  - 新增: {stats['inserted']} 条")
                    if stats['duplicate'] > 0:
                        report_lines.append(f"  - 重复: {stats['duplicate']} 条")
                    report_lines.append("")  # 空行分隔
            
            if unmapped_symbols:
                report_lines.append(f"⚠️ **未能导入代码** ({len(unmapped_symbols)} 个):")
                report_lines.append(f"  {', '.join(sorted(unmapped_symbols))}")
                report_lines.append(f"\n💡 **建议**: 请先在「资产管理」页面注册这些资产，然后重新导入 CSV。")
            
            # # 补充财务数据（已注释：当前CSV文件已包含PE/PB/EPS数据）
            # if len(mapped_symbols) > 0:
            #     report_lines.append(f"\n📊 **正在补充财务数据...**")
            #     try:
            #         from utils.financial_supplement import batch_supplement_financials
            #         
            #         unique_canonical_ids = list(set(mapped_symbols.values()))
            #         fin_stats = batch_supplement_financials(unique_canonical_ids, verbose=False)
            #         
            #         report_lines.append(f"  - 成功: {fin_stats['success']} 个")
            #         report_lines.append(f"  - 失败: {fin_stats['failed']} 个")
            #         report_lines.append(f"  - 跳过（已有数据）: {fin_stats['skipped']} 个")
            #         
            #         if fin_stats['failed'] > 0:
            #             report_lines.append(f"\n💡 **提示**: 部分资产可能在 Yahoo Finance 中无财务数据")
            #     except Exception as e:
            #         report_lines.append(f"  ⚠️ 财务数据补充失败: {str(e)}")
            
            return True, "\n".join(report_lines)
            
        except Exception as e:
            return False, f"数据库操作失败: {str(e)}"
        finally:
            conn.close()
            
    except Exception as e:
        return False, f"CSV 解析失败: {str(e)}"



def parse_and_import_financials_csv(uploaded_file, unit_scale=100_000_000, mode="overwrite", start_date=None, end_date=None, target_assets=None):
    """
    Parse and import financial historical data from CSV.
    Populates financial_history and financial_fundamentals.
    
    Args:
        mode: "overwrite" (更新已有记录) or "incremental" (仅插入新记录)
        target_assets (list): Optional. List of canonical IDs to strictly filter import data.
    """
    try:
        df = pd.read_csv(uploaded_file)
        df.columns = [c.strip().lower() for c in df.columns]
        
        conn = get_connection()
        try:
            # Column mapping
            mapping = {
                'symbol': ['symbol', 'ticker', 'code', '代码', '标的'],
                'date': ['as_of_date', 'date', 'report_date', '日期', '截止日期'],
                'revenue': ['revenue', 'revenue_ttm', '营收', '营业收入'],
                'net_income': ['net_income', 'net_profit', 'net_income_ttm', 'net_profit_ttm', '净利润'],
                'currency': ['currency', '货币', '币种']
            }
            
            # Simple column resolver
            def find_col(keys):
                for c in df.columns:
                    if any(k in c for k in keys): return c
                return None
            
            sym_col = find_col(mapping['symbol'])
            date_col = find_col(mapping['date'])
            rev_col = find_col(mapping['revenue'])
            ni_col = find_col(mapping['net_income'])
            cur_col = find_col(mapping['currency'])
            
            if not sym_col or not date_col:
                return False, f"CSV 缺少必需列 (需包含代码和日期)。已发现列: {list(df.columns)}"
            
            # 更全面的新字段映射
            ext_mapping = {
                'op_cf': ['operating_cashflow_ttm', '经营现金流', '经营活动产生的现金流量净额'],
                'free_cf': ['free_cashflow_ttm', '自由现金流'],
                'total_assets': ['total_assets', '总资产', '资产总计'],
                'total_liabs': ['total_liabilities', '总负债', '负债合计'],
                'total_debt': ['total_debt', '总债务', '有息负债'],
                'cash': ['cash_and_equivalents', '现金', '货币资金'],
                'net_debt': ['net_debt', '净债务'],
                'de_ratio': ['debt_to_equity', '产权比率', '负债权益比'],
                'ic_ratio': ['interest_coverage', '利息保障倍数'],
                'curr_ratio': ['current_ratio', '流动比率'],
                'div_yield': ['dividend_yield', '股息率'],
                'payout': ['payout_ratio', '分红率', '股利支付率'],
                'buyback': ['buyback_ratio', '回购率']
            }
            
            def find_ext_val(row, keys):
                match = next((c for c in df.columns if any(k == c for k in keys)), None)
                return row.get(match) if match else None

            def scale_it(val):
                if pd.isna(val) or val == '': return None
                try:
                    return float(val) * unit_scale
                except:
                    return None
            
            def get_raw(val):
                if pd.isna(val) or val == '': return None
                return val

            inserted = 0
            updated = 0
            errors = 0
            
            for _, row in df.iterrows():
                try:
                    raw_symbol = str(row[sym_col]).strip()
                    as_of_date = str(row[date_col]).strip()
                    if not as_of_date or as_of_date == 'nan': continue
                    
                    # Convert to YYYY-MM-DD for comparison and storage consistency
                    try:
                        report_date_obj = pd.to_datetime(as_of_date)
                        as_of_date_str = report_date_obj.strftime('%Y-%m-%d')
                    except:
                        # Continue if date parse fails, let original logic handle or skip
                        continue

                    # Date Range Filtering
                    if start_date and as_of_date_str < str(start_date): continue
                    if end_date and as_of_date_str > str(end_date): continue
                    
                    # Use standarized date string
                    as_of_date = as_of_date_str

                    
                    # Resolve Canonical
                    asset_id = resolve_canonical_symbol(conn, raw_symbol)
                    if not asset_id: asset_id = raw_symbol
                    
                    # Asset Filter Logic
                    if target_assets and asset_id not in target_assets:
                        continue
                    
                    revenue = scale_it(row.get(rev_col)) if rev_col else None
                    net_profit = scale_it(row.get(ni_col)) if ni_col else None
                    currency = str(row.get(cur_col)).strip() if cur_col and not pd.isna(row.get(cur_col)) else 'CNY'
                    
                    # Optional Fundamental metrics (Using scale_it/get_raw with find_ext_val)
                    op_cf = scale_it(find_ext_val(row, ext_mapping['op_cf']))
                    free_cf = scale_it(find_ext_val(row, ext_mapping['free_cf']))
                    t_assets = scale_it(find_ext_val(row, ext_mapping['total_assets']))
                    t_liab = scale_it(find_ext_val(row, ext_mapping['total_liabs']))
                    t_debt = scale_it(find_ext_val(row, ext_mapping['total_debt']))
                    cash = scale_it(find_ext_val(row, ext_mapping['cash']))
                    n_debt = scale_it(find_ext_val(row, ext_mapping['net_debt']))
                    d_e = get_raw(find_ext_val(row, ext_mapping['de_ratio']))
                    int_cov = get_raw(find_ext_val(row, ext_mapping['ic_ratio']))
                    curr_ratio = get_raw(find_ext_val(row, ext_mapping['curr_ratio']))
                    div_yield = get_raw(find_ext_val(row, ext_mapping['div_yield']))
                    payout = get_raw(find_ext_val(row, ext_mapping['payout']))
                    buyback = get_raw(find_ext_val(row, ext_mapping['buyback']))
                    
                    cursor = conn.cursor()
                    
                    # 1. Update/Insert financial_history
                    # 列映射：数据库字段名与提取变量名一致
                    fh_raw = {
                        "revenue_ttm": revenue,
                        "net_profit_ttm": net_profit,  # 原有标准
                        "net_income_ttm": net_profit,  # 新增兼容
                        "currency": currency,
                        "operating_cashflow_ttm": op_cf,
                        "free_cashflow_ttm": free_cf,
                        "total_assets": t_assets,
                        "total_liabilities": t_liab,
                        "total_debt": t_debt,
                        "cash_and_equivalents": cash,
                        "net_debt": n_debt,
                        "debt_to_equity": d_e,
                        "interest_coverage": int_cov,
                        "current_ratio": curr_ratio,
                        "dividend_yield": div_yield,
                        "payout_ratio": payout,
                        "buyback_ratio": buyback
                    }
                    
                    # 获取表实际字段以避免错误 (仅限执行 ALTER 后的字段)
                    cursor.execute("PRAGMA table_info(financial_history)")
                    fh_actual_cols = [r[1] for r in cursor.fetchall()]
                    fh_data = {k: v for k, v in fh_raw.items() if k in fh_actual_cols and v is not None}
                    
                    if fh_data:
                        fh_cols = ["asset_id", "report_date"] + list(fh_data.keys())
                        fh_vals = [asset_id, as_of_date] + list(fh_data.values())
                        fh_placeholders = ", ".join(["?"] * len(fh_vals))
                        fh_update = ", ".join([f"{k} = excluded.{k}" for k in fh_data.keys()])
                        
                        if mode == "incremental":
                            sql_fh = f"""
                                INSERT OR IGNORE INTO financial_history ({', '.join(fh_cols)})
                                VALUES ({fh_placeholders})
                            """
                        else:
                            sql_fh = f"""
                                INSERT INTO financial_history ({', '.join(fh_cols)})
                                VALUES ({fh_placeholders})
                                ON CONFLICT(asset_id, report_date) DO UPDATE SET {fh_update}
                            """
                        
                        cursor.execute(sql_fh, fh_vals)
                        inserted += 1
                        
                    # 2. Update/Insert financial_fundamentals (适配其独特的 net_income_ttm 命名)
                    ff_raw = {
                        "revenue_ttm": revenue,
                        "net_income_ttm": net_profit, # 关键：fundamentals 使用 income
                        "operating_cashflow_ttm": op_cf, 
                        "free_cashflow_ttm": free_cf,
                        "total_assets": t_assets,
                        "total_liabilities": t_liab,
                        "total_debt": t_debt,
                        "cash_and_equivalents": cash,
                        "net_debt": n_debt,
                        "debt_to_equity": d_e,
                        "interest_coverage": int_cov,
                        "current_ratio": curr_ratio,
                        "dividend_yield": div_yield,
                        "payout_ratio": payout,
                        "buyback_ratio": buyback,
                        "currency": currency,
                        "data_source": "csv-import"
                    }
                    
                    cursor.execute("PRAGMA table_info(financial_fundamentals)")
                    ff_actual_cols = [r[1] for r in cursor.fetchall()]
                    ff_data = {k: v for k, v in ff_raw.items() if k in ff_actual_cols and v is not None}
                    
                    if ff_data:
                        ff_cols = ["asset_id", "as_of_date"] + list(ff_data.keys())
                        ff_vals = [asset_id, as_of_date] + list(ff_data.values())
                        ff_placeholders = ", ".join(["?"] * len(ff_vals))
                        ff_update = ", ".join([f"{k} = excluded.{k}" for k in ff_data.keys()])
                        
                        if mode == "incremental":
                            sql_ff = f"""
                                INSERT OR IGNORE INTO financial_fundamentals ({', '.join(ff_cols)})
                                VALUES ({ff_placeholders})
                            """
                        else:
                            sql_ff = f"""
                                INSERT INTO financial_fundamentals ({', '.join(ff_cols)})
                                VALUES ({ff_placeholders})
                                ON CONFLICT(asset_id, as_of_date) DO UPDATE SET {ff_update}
                            """
                        
                        cursor.execute(sql_ff, ff_vals)
                except Exception as row_e:
                    print(f"Error row: {row_e}")
                    errors += 1
            
            conn.commit()
            mode_label = "全覆盖" if mode == "overwrite" else "增量添加"
            return True, f"✅ 财报数据导入完成 (模式: {mode_label})\n- 新增记录: {inserted}\n- 更新记录: {updated}\n- 错误: {errors}"
        finally:
            conn.close()
    except Exception as e:
        return False, f"财报 CSV 解析失败: {str(e)}"
