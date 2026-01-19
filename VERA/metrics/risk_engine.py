from metrics.drawdown import max_drawdown, current_drawdown, recovery_time, max_drawdown_details, recovery_details, recovery_progress
from metrics.volatility import annual_volatility
from metrics.tail_risk import worst_n_day_drop
import pandas as pd

class RiskEngine:
    @staticmethod
    def calculate_risk_metrics(prices: pd.Series):
        """
        风险计算引擎
        Input: adj_close series (pandas Series)
        Output: Risk Metrics Set (dict)
        """
        if prices.empty:
            return {}
            
        # Ensure we are working with a Series for date operations
        if not isinstance(prices, pd.Series):
            raise ValueError("RiskEngine requires a pandas Series with DatetimeIndex")

        # Returns for volatility
        returns = prices.pct_change().dropna()
        
        # MDD Details
        mdd, mdd_amount, peak_date, valley_date, peak_price, valley_price = max_drawdown_details(prices)
        
        # Recovery Details
        rec_days, rec_end_date = recovery_details(prices)
        
        # Recovery Progress
        rec_progress = recovery_progress(prices)
        
        # Volatility Calculations
        # 1. Long Term (Full Period, typically 10Y)
        vol_long = annual_volatility(returns)
        
        # 2. Short Term (1Y, last 252 trading days)
        returns_1y = returns.iloc[-252:] if len(returns) > 252 else returns
        vol_1y = annual_volatility(returns_1y)
        
        metrics = {
            "max_drawdown": mdd,
            "max_drawdown_amount": mdd_amount,
            "mdd_peak_price": peak_price,
            "mdd_valley_price": valley_price,
            "mdd_peak_date": peak_date.strftime("%Y-%m-%d") if peak_date else None,
            "mdd_valley_date": valley_date.strftime("%Y-%m-%d") if valley_date else None,
            "current_peak_date": prices.idxmax().strftime("%Y-%m-%d"), # Date of 10y high (reference for current progress)
            "annual_volatility": vol_long,      # Keep legacy key for compatibility (defaulting to Long Term)
            "volatility_1y": vol_1y,            # NEW: 1Y Volatility
            "volatility_10y": vol_long,         # NEW: Explicit Long Term Key
            "volatility_period": f"{prices.index[0].strftime('%Y/%m')} - {prices.index[-1].strftime('%Y/%m')}",
            "current_drawdown": current_drawdown(prices),
            "recovery_time": rec_days,
            "recovery_end_date": rec_end_date.strftime("%Y-%m-%d") if rec_end_date else None,
            "recovery_progress": rec_progress,
            "worst_5d_drop": worst_n_day_drop(prices, window=5),
            "risk_state": RiskEngine.calculate_path_risk_state(prices),
            "price_percentile": prices.rank(pct=True).iloc[-1]
        }
        
        return metrics

    @staticmethod
    def calculate_path_risk_state(prices: pd.Series):
        """
        计算 10年路径风险状态机 (D0-D6)
        Logic: based on Drawdown State Machine
        """
        if prices.empty:
            return None
            
        # 1. 基础指标计算
        peak_10y = prices.max()
        if peak_10y <= 0: return None
        
        peak_date = prices.idxmax()
        
        # trough_10y must be AFTER peak
        post_peak_data = prices[peak_date:]
        if post_peak_data.empty:
            trough_10y = prices.iloc[-1]
        else:
            trough_10y = post_peak_data.min()
            
        current_price = prices.iloc[-1]
        
        # 核心派生指标
        current_dd = (current_price - peak_10y) / peak_10y
        
        # max_dd_cycle (Current Cycle Depth)
        if peak_10y == 0: max_dd_cycle = 0
        else: max_dd_cycle = (trough_10y - peak_10y) / peak_10y
            
        # Recovery
        if (peak_10y - trough_10y) == 0:
            recovery = 1.0
        else:
            recovery = (current_price - trough_10y) / (peak_10y - trough_10y)
            
        # 抽取原始指标快照 (Raw Metrics Snapshot)
        raw_metrics = {
            "peak_10y": float(peak_10y),
            "trough_10y": float(trough_10y),
            "current_dd": float(current_dd),
            "max_dd_cycle": float(max_dd_cycle),
            "recovery": float(recovery)
        }
        
        # 2. 状态机判定 (State Machine Logic)
        
        # New High Check
        # 考虑到浮点数精度，Price >= Peak * 0.999 即可视为新高/接近新高
        has_new_high = current_price >= (peak_10y * 0.999)
        
        # Debug Print
        print(f"\n[D-State Debug] Price: {current_price:.2f}, Peak: {peak_10y:.2f}, Trough: {trough_10y:.2f}")
        print(f"[D-State Debug] Current DD: {current_dd:.2%}, Max DD Cycle: {max_dd_cycle:.2%}, Recovery: {recovery:.2%}, NewHigh: {has_new_high}")

        base_res = {"raw_metrics": raw_metrics, "has_new_high": has_new_high}

        # D0: 无回撤 (Path Stable) - 仅在非深回撤周期有效 (MaxDD > -15%)
        # 如果是深回撤后的修复 (如从 -50% 回到 -3%)，应走 D6 逻辑
        if current_dd > -0.05 and max_dd_cycle > -0.15:
            print("[D-State Make] -> D0 (Stable, DD > -5%, Shallow Cycle)")
            base_res.update({"state": "D0", "desc": "无回撤 (路径稳定)"})
            return base_res
            
        # 浅度回撤循环 (Max DD > -15%) -> D1
        if max_dd_cycle > -0.15:
            print("[D-State Make] -> D1 (Shallow, MaxDD > -15%)")
            base_res.update({"state": "D1", "desc": "浅回撤 (压力初现)"})
            return base_res
            
        # 深度回撤循环 (Structural Damage Occurred, Max DD <= -15%)
        # Refined D6: Recovery >= 95% (was 80%)
        if recovery >= 0.95:
            print("[D-State Make] -> D6 (Recovered, Rec >= 95%)")
            base_res.update({"state": "D6", "desc": "大部分修复 (结构重启)"})
            return base_res
            
        if recovery >= 0.3:
            print("[D-State Make] -> D5 (Mid Recovery, Rec >= 30%)")
            base_res.update({"state": "D5", "desc": "修复中段 (风险下降)"})
            return base_res
            
        if recovery > 0.0:
            print("[D-State Make] -> D4 (Early Recovery, Rec > 0%)")
            base_res.update({"state": "D4", "desc": "反弹早期 (假修复/极高风险)"})
            return base_res
            
        if current_dd <= -0.35:
            print("[D-State Make] -> D3 (Deep DD, CurrDD <= -35%)")
            base_res.update({"state": "D3", "desc": "深度回撤 (脆弱区)"})
            return base_res
        else:
            print("[D-State Make] -> D2 (Mid DD, else)")
            base_res.update({"state": "D2", "desc": "中度回撤 (结构受压)"})
            return base_res
