import sys
import yfinance as yf
from sqlmodel import Session, select
sys.path.append('backend')
from database import engine
from models import FinancialFundamentals, MarketDataDaily
from valuation_calculator import get_ttm_net_income, get_shares_outstanding

def reverse_engineer(symbol, yf_symbol):
    print(f"\n{'='*60}")
    print(f"🪄  正在倒推 {symbol} ({yf_symbol}) 的 PE 公式...")
    print(f"{'='*60}")

    # 1. 获取 Yahoo Finance 数据 (作为 '行情软件' 基准)
    try:
        ticker = yf.Ticker(yf_symbol)
        info = ticker.info
        
        # 获取 Yahoo 的关键数据
        y_pe = info.get('trailingPE')
        y_price = info.get('currentPrice') or info.get('regularMarketPrice')
        y_eps_ttm = info.get('trailingEps')
        
        if not y_pe:
            print(f"❌ 无法从 Yahoo 获取 {yf_symbol} 的 PE 数据")
            return

        print(f"📊 [基准] Yahoo Finance:")
        print(f"   Price: {y_price}")
        print(f"   PE:    {y_pe}")
        print(f"   EPS:   {y_eps_ttm} (Yahoo 宣称的 TTM EPS)")
        
        # 倒推 Yahoo 使用的 EPS
        if y_price and y_pe:
            implied_eps = y_price / y_pe
            print(f"   🔍 倒推 Implied EPS (Price/PE): {implied_eps:.4f}")
    except Exception as e:
        print(f"❌ Yahoo API 错误: {e}")
        return

    # 2. 获取我们数据库的数据
    with Session(engine) as session:
        # 财报
        fins = session.exec(
            select(FinancialFundamentals)
            .where(FinancialFundamentals.symbol == symbol)
            .order_by(FinancialFundamentals.as_of_date.desc())
        ).all()
        
        if not fins:
            print(f"❌ 数据库无 {symbol} 财报数据")
            return

        # 尝试多种计算方式
        print(f"\n🧪 [实验] 尝试匹配我们的数据:")
        
        latest_fin = fins[0]
        curr = latest_fin.currency
        print(f"   最新财报: {latest_fin.as_of_date} ({latest_fin.report_type}, {curr})")
        
        # 场景 A: TTM Net Income / Total Shares (我们目前的逻辑)
        # 注意: 这里的 get_ttm_net_income 已经是我们修复后的版本
        ttm_inc, _ = get_ttm_net_income(fins, '2026-01-08')
        shares = get_shares_outstanding(symbol, symbol.split(':')[0])
        
        if ttm_inc and shares:
            my_eps_a = ttm_inc / shares
            diff_a = abs(my_eps_a - implied_eps) / implied_eps * 100
            print(f"   [公式 A] TTM净利 / 总股本")
            print(f"      输入: NetInc={ttm_inc/1e9:.2f}B, Shares={shares/1e9:.2f}B")
            print(f"      结果: {my_eps_a:.4f} (偏差: {diff_a:.2f}%) {'✅ MATCH' if diff_a < 5 else ''}")
            
        # 场景 B: Basic EPS (TTM) - 直接加总财报里的 eps_ttm (如果数据源提供)
        # AkShare 的 eps_ttm 往往是单季或累计，我们需要自己处理
        # 这里尝试简单的 "最新 eps_ttm" (如果数据源直接提供了做好的 TTM)
        if latest_fin.eps_ttm:
             # 注意：对于 Quarter 类型的 accum 数据，这个 eps_ttm 可能是 accum 值
             my_eps_b = latest_fin.eps_ttm
             diff_b = abs(my_eps_b - implied_eps) / implied_eps * 100
             print(f"   [公式 B] 数据库原始 EPS (Latest)")
             print(f"      输入: {my_eps_b}")
             print(f"      结果: {my_eps_b:.4f} (偏差: {diff_b:.2f}%)")

        # 场景 C: Annualized Quarterly (最新季度 * 4)
        latest_q = next((f for f in fins if f.report_type == 'quarterly'), None)
        if latest_q and latest_q.net_income_ttm: # 这里的 net_income_ttm 在 accum 逻辑下可能是累计值
             # 假设是单季 (粗略) -> 无法简单验证，先跳过复杂的单季拆分
             pass
             
        # 场景 D: Diluted TTM (如果有稀释数据)
        # 目前模型好像没有 explicit diluted eps 字段，通常 eps_ttm 应该是 diluted ?
        pass

if __name__ == "__main__":
    # Test Cases
    targets = [
        ("HK:STOCK:00700", "0700.HK"),    # 腾讯
        ("CN:STOCK:600030", "600030.SS"), # 中信
        ("HK:STOCK:09988", "9988.HK"),    # 阿里
        ("US:STOCK:AAPL", "AAPL")         # Apple
    ]
    
    for local_sym, yf_sym in targets:
        reverse_engineer(local_sym, yf_sym)
