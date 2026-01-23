import sys
import logging
from pathlib import Path
sys.path.append('backend')
from sqlmodel import Session, select
from backend.database import engine
from backend.models import Watchlist
from backend.symbol_utils import get_canonical_id

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("Import")

def import_and_show():
    print(f"\n{'='*60}")
    print(f"📥 正在从 imports/symbols.txt 导入并生成典范 ID...")
    print(f"{'='*60}")
    
    symbols_file = Path("imports/symbols.txt")
    if not symbols_file.exists():
        logger.error(f"❌ 文件未找到: {symbols_file}")
        return

    with Session(engine) as session:
        # Read file
        with open(symbols_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        current_market = None
        current_type = None
        imported_assets = []
        
        # Section mapping
        section_patterns = {
            'A股指数 (CN Indices)': ('CN', 'INDEX'),
            '港股指数 (HK Indices)': ('HK', 'INDEX'),
            '美股指数 (US Indices)': ('US', 'INDEX'),
            'A股 (CN Stocks)': ('CN', 'STOCK'),
            'A股 ETF (CN ETFs)': ('CN', 'ETF'),
            '港股 (HK Stocks)': ('HK', 'STOCK'),
            '港股 ETF (HK ETFs)': ('HK', 'ETF'),
            '美股 (US Stocks)': ('US', 'STOCK'),
            '美股 ETF (US ETFs)': ('US', 'ETF'),
            '指数 (Indices)': (None, 'INDEX'),
            '加密货币 (Crypto)': ('CRYPTO', 'CRYPTO'),
        }
        
        print(f"{'Input Code':<15} | {'Market':<8} | {'Type':<8} | {'Canonical ID (Output)':<30}")
        print("-" * 75)
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Parse Header
            if line.startswith('#'):
                for pattern, (mkt, typ) in section_patterns.items():
                    if pattern in line:
                        current_market = mkt
                        current_type = typ
                        break
                continue
            
            # Process Symbol
            market = current_market
            asset_type = current_type
            
            # Special handling for Indices if market is None (Old format compatibility)
            if asset_type == 'INDEX' and market is None:
                 if line.startswith('^') or line.isalpha(): 
                     if line in ['HSI', 'HSTECH', 'HSCC', 'HSCE']:
                         market = 'HK'
                     elif line in ['000001', '000300', '000016', '000905']: 
                         market = 'CN'
                     else:
                         market = 'US'
                 elif line.isdigit():
                     market = 'CN'
            
            try:
                # Generate Canonical ID
                if not market:
                     # Skip lines that are not under any valid section
                     continue

                # get_canonical_id returns (id, market)
                # Pass asset_type explicitly to override inference
                canonical_id, inferred_market = get_canonical_id(line, market, asset_type)
                
                # Check duplication
                existing = session.exec(select(Watchlist).where(Watchlist.symbol == canonical_id)).first()
                if not existing:
                    wl = Watchlist(symbol=canonical_id, market=market or inferred_market, name=line)
                    session.add(wl)
                    status = "✅ Added"
                else:
                    status = "⚠️ Exists"
                
                imported_assets.append((line, market, asset_type, canonical_id))
                print(f"{line:<15} | {str(market):<8} | {str(asset_type):<8} | {canonical_id:<30}")
                
            except Exception as e:
                logger.error(f"Error processing {line}: {e}")
        
        session.commit()
    
    print("-" * 75)
    print(f"Total processed: {len(imported_assets)}")

if __name__ == "__main__":
    import_and_show()
