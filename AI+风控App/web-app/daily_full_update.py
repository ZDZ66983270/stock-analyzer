#!/usr/bin/env python3
"""
VERA Protocol - Daily Full Update Pipeline
Orchestrates the end-to-end data refresh process:
1. Import Symbols (Optional)
2. Download Historical Data (Incremental)
3. Process Raw Data (ETL)
4. Fetch Financials (Quarterly/Annual)
5. Calculate Historical PE (The VERA Core)
6. Export CSV (Consumable Output)

Design Goal: Robust, institution-grade reliability.
"""
import sys
import os
import subprocess
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('daily_update.log', mode='w')
    ]
)
logger = logging.getLogger("DailyPipeline")

INTERPRETER = sys.executable
CWD = os.path.dirname(os.path.abspath(__file__)) # web-app root

def run_step(step_name, command, ignore_error=False):
    """Executes a pipeline step as a subprocess."""
    logger.info("=" * 60)
    logger.info(f"▶️ START STEP: {step_name}")
    logger.info(f"   Command: {command}")
    logger.info("=" * 60)
    
    start_time = datetime.now()
    try:
        # Run command
        cmd_list = command.split()
        # If command starts with python3, replace with current interpreter
        if cmd_list[0] == 'python3':
            cmd_list[0] = INTERPRETER
            
        process = subprocess.run(
            cmd_list,
            cwd=CWD,
            check=True,
            text=True,
            capture_output=False # Stream output to console
        )
        duration = datetime.now() - start_time
        logger.info(f"✅ STEP COMPLETED: {step_name} (Duration: {duration})")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ STEP FAILED: {step_name} (Exit Code: {e.returncode})")
        if not ignore_error:
            logger.error("🛑 Pipeline Stopped due to critical error.")
            sys.exit(e.returncode)
        else:
            logger.warning("⚠️ Ignoring error and continuing...")
            return False

def main():
    logger.info("🚀 VERA PROTOCOL - DAILY FULL UPDATE STARTED")
    overall_start = datetime.now()
    
    # --- Step 0: User Interaction Mode ---
    print("\n🌍 选择运行模式 / Select Mode:")
    print("  [1] ⚡️ 全自动 (Auto) - 下载所有配置 (CN/HK/US + OHLCV)")
    print("  [2] 🖐️ 手动 (Manual) - 进入下载菜单选择特定资产")
    mode = input("  请输入 (默认 1): ").strip()
    
    dl_cmd = "python3 download_full_history.py --auto"
    if mode == '2':
        dl_cmd = "python3 download_full_history.py"
    
    # --- Step 1: Download Market Data ---
    run_step("Download Market Data", dl_cmd)
    
    # --- Step 2: ETL Process ---
    # Process valid raw data into MarketDataDaily tables
    # CRITICAL: Must calculate before Valuation to avoid overwrite
    run_step(
        "ETL Process (Optimized)",
        "python3 process_raw_data_optimized.py"
    )
    
    # --- Step 3: Fetch Financials ---
    run_step("Fetch Financials", "python3 fetch_financials.py")

    # --- Step 3.1: Fetch Enhanced Financials (EPS TTM) ---
    # Supplement with high-quality TTM data from AkShare (HK Report Period / CN Manual Calc)
    run_step("Fetch Enhanced Financials", "python3 scripts/fetch_missing_financials.py --market ALL")

    # --- Step 4: Valuation (PE/PB/Yield) ---
    # Fetches PE/PB from external sources (AkShare/Baidu/FMP)
    # Must run AFTER ETL
    run_step("Fetch Valuation History", "python3 fetch_valuation_history.py")

    # --- Step 4.1: Recalc PE TTM (Internal) ---
    # Use locally fetched EPS to backfill/correct PE TTM
    run_step("Recalc PE TTM History", "python3 scripts/recalc_historical_pe.py")
    
    # --- Step 5: Export ---
    run_step("Export Financials", "python3 export_financials_formatted.py")
    run_step("Export Daily CSV", "python3 export_daily_csv.py")
    
    logger.info("=" * 60)
    logger.info(f"🏁 PIPELINE COMPLETED SUCCESSFULLY (Total Time: {datetime.now() - overall_start})")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
