#!/usr/bin/env python3
"""
一键式个股管理程序 (Add New Asset Orchestrator)
用法: python3 add_new_asset_complete.py --symbol 00700.HK --name 腾讯控股 --market HK
"""
import sys
import os
import argparse
import subprocess
import pandas as pd
from datetime import datetime
from sqlmodel import Session, select

# 添加后端路径
sys.path.append('backend')
from database import engine
from models import Watchlist, MarketDataDaily, FinancialFundamentals

def run_step(name, command):
    print(f"\n--- [步骤]: {name} ---")
    print(f"执行: {command}")
    try:
        # 使用当前 Python 解释器运行
        subprocess.run([sys.executable] + command.split(), check=True)
        print(f"✅ {name} 完成")
        return True
    except Exception as e:
        print(f"❌ {name} 失败: {e}")
        return False

def get_auto_name(symbol, market):
    """通过 yfinance 自动获取公司名称"""
    yf_symbol = symbol
    if market == 'HK' and len(symbol.split('.')[0]) == 5: yf_symbol = symbol[1:]
    elif market == 'CN': yf_symbol = symbol.replace('.SH', '.SS')
    try:
        t = yf.Ticker(yf_symbol)
        return t.info.get('longName') or t.info.get('shortName') or symbol
    except:
        return symbol

def main():
    parser = argparse.ArgumentParser(description="一键批量新增个股并更新全量数据")
    parser.add_argument("--symbols", help="股票代码列表, 逗号分隔, 如 '09988.HK, NVDA' (可选)")
    parser.add_argument("--names", help="股票名称列表, 逗号分隔 (可选, 与代码一一对应)")
    parser.add_argument("--market", choices=['CN', 'HK', 'US'], help="强制指定市场 (可选)")
    parser.add_argument("--history_years", type=int, default=10, help="同步行情历史的年数 (默认 10)")
    
    args = parser.parse_args()
    
    # 解析目标标的
    targets = []
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',')]
        names = [n.strip() for n in args.names.split(',')] if args.names else []
        
        for i, sym in enumerate(symbols):
            name = names[i] if i < len(names) else None
            # 自动推断市场
            market = args.market
            if not market:
                if sym.endswith('.HK') or sym.isdigit() and len(sym) <= 5: market = 'HK'
                elif sym.endswith('.SH') or sym.endswith('.SZ') or sym.isdigit() and len(sym) == 6: market = 'CN'
                else: market = 'US'
            
            # 如果没有名称，尝试通过 API 获取
            if not name:
                print(f"🔍 正在为 {sym} 获取自动名称...")
                try:
                    import yfinance as yf
                    ticker = yf.Ticker(sym)
                    name = ticker.info.get('longName', sym)
                except:
                    name = sym
            
            targets.append({'symbol': sym, 'name': name, 'market': market})

    print(f"\n🚀 准备为以下 {len(targets)} 个标的执行全流程更新 (历史深度: {args.history_years} 年):")
    for t in targets:
        print(f"   - {t['symbol']} | {t['name']} ({t['market']})")
    print("=" * 60)

    # 初始化简报数据
    report = {
        'targets': targets,
        'steps': []
    }

    # 1. 加入下载列表
    watchlist_results = []
    with Session(engine) as session:
        for t in targets:
            existing = session.exec(select(Watchlist).where(Watchlist.symbol == t['symbol'])).first()
            if not existing:
                new_item = Watchlist(symbol=t['symbol'], name=t['name'], market=t['market'])
                session.add(new_item)
                watchlist_results.append(f"新增: {t['symbol']}")
            else:
                watchlist_results.append(f"已存在: {t['symbol']}")
        session.commit()
    report['steps'].append(("1. Watchlist 更新", "成功", "\n".join(watchlist_results)))

    # 2. 财报下载
    success = run_step("下载财报数据", "fetch_financials.py")
    report['steps'].append(("2. 财报获取", "通过" if success else "异常", "获取财务利润基数"))

    # 3. 行情同步
    success = run_step(f"同步 {args.history_years} 年行情历史", "download_raw_data.py")
    report['steps'].append(("3. 行情同步", "通过" if success else "异常", f"追溯至 2015 年 ({args.history_years}年)"))
    
    # 4. 指标计算与 ETL
    m_success = run_step("计算高级指标", "backend/advanced_metrics.py")
    e_success = run_step("同步生产快照 (ETL)", "run_etl.py")
    report['steps'].append(("4. 指标与同步", "通过" if (m_success and e_success) else "异常", "PE/EPS 计算及快照更新"))

    # 5. 导出
    print("\n--- [步骤]: 导出 CSV 数据 ---")
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    export_msg = ""
    try:
        with Session(engine) as session:
            # 导出财报历史
            fins = session.exec(select(FinancialFundamentals).order_by(FinancialFundamentals.symbol, FinancialFundamentals.as_of_date.desc())).all()
            if fins:
                fin_df = pd.DataFrame([f.model_dump() for f in fins])
                num_cols = ['revenue_ttm', 'net_income_ttm', 'total_assets', 'total_liabilities', 'total_debt', 'cash_and_equivalents']
                for c in num_cols:
                    if c in fin_df.columns: fin_df[c] = (fin_df[c] / 100_000_000).round(4)
                fin_df.to_csv(f"{output_dir}/financial_history.csv", index=False, encoding='utf-8-sig')
                export_msg += "✅ 财报历史导出成功\n"
            
            # 导出日线表 (最近 100 条)
            daily = session.exec(select(MarketDataDaily).order_by(MarketDataDaily.symbol, MarketDataDaily.timestamp.desc())).all()
            if daily:
                daily_df = pd.DataFrame([d.model_dump() for d in daily])
                daily_df.to_csv(f"{output_dir}/market_daily.csv", index=False, encoding='utf-8-sig')
                export_msg += "✅ 行情历史导出成功"
    except Exception as e:
        export_msg = f"❌ 导出失败: {e}"
    
    report['steps'].append(("5. 数据导出", "完成", export_msg))

    # --- 最终简报 ---
    print("\n" + "=" * 60)
    print("📊 任务执行简报 (Final Summary)")
    print("=" * 60)
    print(f"处理对象: {', '.join([t['symbol'] for t in targets])}")
    print("-" * 60)
    for step, status, detail in report['steps']:
        print(f"[{status}] {step}")
        if detail:
            for line in detail.split('\n'):
                print(f"      > {line}")
    
    # 检查数据留存检查 (如果是全系统同步，显示 Watchlist 全量标的)
    with Session(engine) as session:
        print("-" * 60)
        print("🔍 核心数据留存检查 (Data Audit):")
        
        check_list = targets if targets else []
        if not check_list:
            # 如果没有新增目标，则检查 Watchlist 中最近活跃的标的快照
            all_w = session.exec(select(Watchlist)).all()
            check_list = [{'symbol': w.symbol, 'name': w.name} for w in all_w]

        # 仅显示摘要，前 10 个或全部
        for t in check_list[:15]:
            count = session.exec(select(MarketDataDaily).where(MarketDataDaily.symbol == t['symbol'])).all()
            status = "✅ 成功" if len(count) > 0 else "❌ 缺失"
            print(f"   - {t['symbol']}: 历史行情 {len(count)} 条 | {status}")
        
        if len(check_list) > 15:
            print(f"   ... 以及其余 {len(check_list)-15} 个标的")
    
    print("=" * 60)
    print(f"🏁 全流程完成! 生成文件: outputs/")
    print("=" * 60)

if __name__ == "__main__":
    main()
