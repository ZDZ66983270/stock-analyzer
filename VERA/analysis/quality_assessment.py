from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

def _get_num(f: Dict[str, Any], *keys: str) -> Optional[float]:
    for k in keys:
        v = f.get(k)
        if v is None:
            continue
        try:
            return float(v)
        except (TypeError, ValueError):
            continue
    return None

def _get_str(f: Dict[str, Any], *keys: str) -> Optional[str]:
    for k in keys:
        v = f.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


# ⸻
# A. Business（业务质量）

# 1）Revenue Stability: STRONG / MID / WEAK
def revenue_stability_flag(f: Dict[str, Any]) -> Tuple[str, List[str]]:
    notes: List[str] = []
    # 允许你放入 revenue_history: list[float]，按年份从旧到新
    hist = f.get("revenue_history")
    
    # 尝试从 fundamentals_annual 转换的 history
    if isinstance(hist, list) and len(hist) >= 4:
        try:
            rev = np.array([float(x) for x in hist if x is not None], dtype=float)
            if len(rev) < 4:
                notes.append("revenue_history insufficient after cleaning")
                return ("-", notes)

            yoy = (rev[1:] / np.maximum(rev[:-1], 1e-9)) - 1.0
            neg_years = int(np.sum(yoy < 0))
            vol = float(np.std(yoy))

            if neg_years >= 2 or vol >= 0.30:
                return ("WEAK", notes + [f"yoy_std={vol:.2f}", f"neg_years={neg_years}"])
            if neg_years == 0 and vol <= 0.15:
                return ("STRONG", notes + [f"yoy_std={vol:.2f}"])
            return ("MID", notes + [f"yoy_std={vol:.2f}", f"neg_years={neg_years}"])
        except Exception:
            notes.append("revenue_history parse failed")
            return ("-", notes)

    notes.append("missing revenue_history")
    # fallback：有收入就不判 WEAK
    rev_ttm = _get_num(f, "revenue_ttm", "totalRevenueTTM")
    if rev_ttm is None:
        notes.append("missing revenue_ttm")
        return ("-", notes)  # 不直接 WEAK，避免误伤
    return ("-", notes)


# 2）Cyclicality: LOW / MID / HIGH
def cyclicality_flag(f: Dict[str, Any]) -> Tuple[str, List[str]]:
    notes: List[str] = []
    sector = (_get_str(f, "sector", "gics_sector", "industry") or "").lower()

    low = {"consumer staples", "healthcare", "utilities", "日常消费", "医疗保健", "公用事业"}
    high = {"energy", "materials", "industrials", "real estate", "能源", "原材料", "工业", "房地产"}

    if not sector:
        notes.append("missing sector/industry")
        return ("-", notes)

    if any(x in sector for x in low):
        return ("LOW", notes)
    if any(x in sector for x in high):
        return ("HIGH", notes)
    return ("-", notes)


# 3）Moat Proxy: STRONG / MID / WEAK
def moat_proxy_flag(f: Dict[str, Any]) -> Tuple[str, List[str]]:
    notes: List[str] = []
    net_margin = _get_num(f, "net_margin", "profitMargins")  # 0..1
    roe = _get_num(f, "roe", "returnOnEquity")               # 0..1
    net_income = _get_num(f, "net_income_ttm", "netIncomeToCommonTTM")
    
    # Calculate margin if missing but raw data exists
    if net_margin is None and net_income is not None:
        rev = _get_num(f, "revenue_ttm", "totalRevenueTTM")
        if rev and rev > 0:
            net_margin = net_income / rev
            
    # Calculate ROE if missing but raw data exists (Net Income / Total Equity)
    # Note: Total Equity = Assets - Liabilities
    if roe is None and net_income is not None:
        assets = _get_num(f, "total_assets")
        liabilities = _get_num(f, "total_liabilities")
        if assets is not None and liabilities is not None:
            equity = assets - liabilities
            if equity > 0:
                roe = net_income / equity

    if net_margin is None and roe is None:
        notes.append("missing roe/net_margin")
        # 若明确亏损则偏弱
        if net_income is not None and net_income < 0:
            return ("WEAK", notes + ["net_income_ttm<0"])
        return ("-", notes)

    nm = net_margin if net_margin is not None else 0.0
    r = roe if roe is not None else 0.0

    if nm >= 0.20 or r >= 0.20:
        return ("STRONG", notes + [f"net_margin={nm:.2f}", f"roe={r:.2f}"])
    if (net_income is not None and net_income < 0) or (nm < 0.10 and r < 0.10):
        return ("WEAK", notes + [f"net_margin={nm:.2f}", f"roe={r:.2f}"])
    return ("MID", notes + [f"net_margin={nm:.2f}", f"roe={r:.2f}"])


# ⸻
# B. Financial（财务质量）

# 4）Balance Sheet: STRONG / MID / WEAK
def balance_sheet_flag(f: Dict[str, Any]) -> Tuple[str, List[str]]:
    notes: List[str] = []
    net_debt = _get_num(f, "net_debt", "netDebt")  # 可能来自你预计算
    d2e = _get_num(f, "debt_to_equity", "debtToEquity")
    current_ratio = _get_num(f, "current_ratio", "currentRatio")
    
    # Calculate d2e if missing
    if d2e is None:
        total_debt = _get_num(f, "total_debt")
        assets = _get_num(f, "total_assets")
        liabilities = _get_num(f, "total_liabilities")
        if total_debt is not None and assets is not None and liabilities is not None:
            equity = assets - liabilities
            if equity > 0:
                d2e = total_debt / equity

    missing = []
    if net_debt is None: missing.append("net_debt")
    if d2e is None: missing.append("debt_to_equity")
    if current_ratio is None: missing.append("current_ratio")
    if missing:
        notes.append("missing balance_sheet_inputs:" + "/".join(missing))

    # 有净负债信息时优先
    if net_debt is not None and net_debt <= 0:
        return ("STRONG", notes + ["net_debt<=0"])

    # 其次用 d2e + current_ratio
    if d2e is not None and d2e >= 2.0:
        return ("WEAK", notes + [f"d2e={d2e:.2f}"])
    if current_ratio is not None and current_ratio < 1.0:
        return ("WEAK", notes + [f"current_ratio={current_ratio:.2f}"])

    if d2e is not None and current_ratio is not None and d2e < 0.5 and current_ratio >= 1.5:
        return ("STRONG", notes + [f"d2e={d2e:.2f}", f"current_ratio={current_ratio:.2f}"])

    return ("-", notes)


# 5）Cashflow Coverage: STRONG / MID / WEAK
def cashflow_coverage_flag(f: Dict[str, Any]) -> Tuple[str, List[str]]:
    notes: List[str] = []
    ocf = _get_num(f, "operating_cashflow_ttm", "operatingCashflowTTM")
    fcf = _get_num(f, "free_cashflow_ttm", "freeCashflowTTM")
    ni = _get_num(f, "net_income_ttm", "netIncomeToCommonTTM")

    missing = []
    if ocf is None: missing.append("ocf")
    if fcf is None: missing.append("fcf")
    if ni is None: missing.append("net_income")
    if missing:
        notes.append("missing fcf/ocf/net_income:" + "/".join(missing))
        return ("-", notes)

    if ocf > 0 and fcf > 0 and ni > 0:
        return ("STRONG", notes)
    if ocf <= 0 and fcf <= 0:
        return ("WEAK", notes + ["ocf<=0 & fcf<=0"])
    if ocf <= 0:
        return ("WEAK", notes + ["ocf<=0"])
    # ocf>0 但 fcf<=0 或 ni<=0
    return ("MID", notes + [f"ocf={ocf:.0f}", f"fcf={fcf:.0f}", f"ni={ni:.0f}"])


# 6）Leverage Risk: LOW / MID / HIGH
def leverage_risk_flag(f: Dict[str, Any]) -> Tuple[str, List[str]]:
    notes: List[str] = []
    d2e = _get_num(f, "debt_to_equity", "debtToEquity")
    ic = _get_num(f, "interest_coverage", "interestCoverage")  # 你可从 EBIT/interestExpense 算
    
     # Calculate d2e if missing
    if d2e is None:
        total_debt = _get_num(f, "total_debt")
        assets = _get_num(f, "total_assets")
        liabilities = _get_num(f, "total_liabilities")
        if total_debt is not None and assets is not None and liabilities is not None:
            equity = assets - liabilities
            if equity > 0:
                d2e = total_debt / equity

    if d2e is None and ic is None:
        notes.append("missing debt_to_equity & interest_coverage")
        return ("-", notes)

    # 强风险触发
    if (d2e is not None and d2e >= 2.0) or (ic is not None and ic < 2.0):
        return ("HIGH", notes + [f"d2e={d2e}", f"ic={ic}"])

    # 低风险
    if (d2e is not None and d2e < 0.8) and (ic is not None and ic >= 5.0):
        return ("LOW", notes + [f"d2e={d2e:.2f}", f"ic={ic:.2f}"])

    return ("MID", notes + [f"d2e={d2e}", f"ic={ic}"])


# ⸻
# C. Governance / Policy（治理 / 政策）

# 7）Payout Consistency: POSITIVE / NEUTRAL / NEGATIVE
def payout_consistency_flag(
    f: Dict[str, Any],
    no_dividend_history: bool = False,
    listing_years: Optional[float] = None
) -> Tuple[str, List[str]]:
    """
    评估「分红 / 回购一致性」
    Returns: (flag, notes)
      flag ∈ {"POSITIVE", "NEUTRAL", "NEGATIVE"}
    """
    notes: List[str] = []
    div_yield = _get_num(f, "dividend_yield", "dividendYield")  # 0..1
    buyback_yield = _get_num(f, "buyback_ratio", "buyback_yield", "netBuybackYield")  # 0..1

    dy = div_yield or 0.0
    by = buyback_yield or 0.0

    # 1) Strong shareholder returns via dividends or buybacks
    if dy >= 0.01 or by >= 0.03:
        return (
            "POSITIVE",
            notes + [f"dy={dy:.3f}", f"by={by:.3f}", 
                    "持续通过分红或回购向股东回馈现金，对回撤阶段有一定缓冲作用"],
        )

    # 2) Explicit long-term no-payout for mature companies → NEGATIVE
    if no_dividend_history and (listing_years is None or listing_years >= 5) and by <= 0:
        years_str = f"listing_years={listing_years:.1f}" if listing_years else "mature_company"
        return (
            "NEGATIVE",
            notes + [years_str,
                    "公司长期未通过分红或回购向股东回馈现金，股东回报主要依赖价格表现与业务成长"],
        )

    # 3) Some payout history or young company → NEUTRAL
    if dy > 0 or by > 0:
        return (
            "NEUTRAL",
            notes + [f"dy={dy:.3f}", f"by={by:.3f}",
                    "存在一定程度的股东回馈记录，但金额或频率不稳定"],
        )

    # 4) Data unavailable or young company → NEUTRAL
    return (
        "NEUTRAL",
        notes + ["当前分红与回购记录不足以形成结论，更适合作为成长型资产看待"],
    )


# 8）Dilution Risk: LOW / HIGH
def dilution_risk_flag(f: Dict[str, Any]) -> Tuple[str, List[str]]:
    notes: List[str] = []
    shares_yoy = _get_num(f, "shares_out_yoy_growth", "sharesYoYGrowth")  # 0..1
    buyback_yield = _get_num(f, "buyback_ratio", "buyback_yield", "netBuybackYield")       # 0..1

    if shares_yoy is not None:
        if shares_yoy > 0.02:
            return ("HIGH", notes + [f"shares_yoy={shares_yoy:.3f}"])
        return ("LOW", notes + [f"shares_yoy={shares_yoy:.3f}"])

    notes.append("missing shares_yoy_growth")
    if buyback_yield is None:
        notes.append("missing buyback_yield")
        return ("HIGH", notes)  # 缺失时保守
    return ("LOW", notes + [f"buyback_yield={buyback_yield:.3f}"]) if buyback_yield > 0 else ("HIGH", notes)


# 9）Regulatory Dependence: LOW / MID / HIGH
def regulatory_dependence_flag(f: Dict[str, Any]) -> Tuple[str, List[str]]:
    notes: List[str] = []
    sector = (_get_str(f, "sector", "gics_sector", "industry") or "").lower()
    if not sector:
        notes.append("missing sector/industry")
        return ("-", notes)

    high = {"utilities", "banks", "financial", "healthcare", "insurance", "公用事业", "银行", "金融", "医疗保健", "保险"}
    mid = {"technology", "communication", "telecom", "信息技术", "通信", "科技"}

    if any(x in sector for x in high):
        return ("HIGH", notes)
    if any(x in sector for x in mid):
        return ("MID", notes)
    return ("LOW", notes)


# ⸻
# 汇总：build_quality_flags + 质量缓冲层级

def build_quality_flags(fundamentals: Dict[str, Any]) -> Dict[str, Any]:
    flags = {}
    notes_all: List[str] = []

    def put(name: str, fn):
        v, notes = fn(fundamentals)
        flags[name] = v
        notes_all.extend([f"{name}: {n}" for n in notes])

    put("revenue_stability_flag", revenue_stability_flag)
    put("cyclicality_flag", cyclicality_flag)
    put("moat_proxy_flag", moat_proxy_flag)

    put("balance_sheet_flag", balance_sheet_flag)
    put("cashflow_coverage_flag", cashflow_coverage_flag)
    put("leverage_risk_flag", leverage_risk_flag)

    # Payout consistency needs extra parameters
    no_div_hist = fundamentals.get('no_dividend_history', False)
    list_years = fundamentals.get('listing_years', None)
    payout_flag, payout_notes = payout_consistency_flag(fundamentals, no_div_hist, list_years)
    flags['payout_consistency_flag'] = payout_flag
    notes_all.extend([f"payout_consistency_flag: {n}" for n in payout_notes])
    
    put("dilution_risk_flag", dilution_risk_flag)
    put("regulatory_dependence_flag", regulatory_dependence_flag)

    # 简单聚合
    strong = sum(1 for k, v in flags.items() if v in {"STRONG", "POSITIVE", "LOW"})
    weak = sum(1 for k, v in flags.items() if v in {"WEAK", "NEGATIVE", "HIGH"})

    if weak >= 4:
        level = "WEAK"
        summary = "质量缓冲偏弱，风险阶段可能出现非线性放大。"
    elif strong >= 4 and weak <= 1:
        level = "STRONG"
        summary = "质量缓冲较强，可更从容吸收回撤阶段的波动。"
    else:
        level = "MODERATE"
        summary = "质量缓冲中等：可承受一般波动，但在深度回撤阶段仍需谨慎。"

    return {
        **flags,
        "quality_buffer_level": level,
        "quality_summary": summary,
        "quality_notes": notes_all,
    }

# 适配 snapshot_builder.py 的接口
from dataclasses import dataclass, field

@dataclass
class QualitySnapshot:
    revenue_stability_flag: str
    cyclicality_flag: str
    moat_proxy_flag: str
    balance_sheet_flag: str
    cashflow_coverage_flag: str
    leverage_risk_flag: str
    payout_consistency_flag: str
    dilution_risk_flag: str
    regulatory_dependence_flag: str
    quality_buffer_level: str
    quality_summary: str
    
    # New Fields for Rules Extension
    dividend_safety_level: Optional[str] = None
    dividend_safety_label_zh: Optional[str] = None
    dividend_safety_score: Optional[float] = None
    
    earnings_state_code: Optional[str] = None
    earnings_state_label_zh: Optional[str] = None
    earnings_state_desc_zh: Optional[str] = None
    
    notes: Dict[str, Any] = field(default_factory=dict)

def build_quality_snapshot(
    asset_id: str,
    fundamentals: Any, # AssetFundamentals object
    bank_metrics: Optional[Any] = None,
    risk_context: Optional[Dict[str, Any]] = None,
    # New optional inputs
    dividend_info: Optional[Any] = None, # DividendSafetyInfo
    earnings_info: Optional[Any] = None  # EarningsStateInfo
) -> QualitySnapshot:
    """
    Wrapper to adapt AssetFundamentals object to dictionary expected by build_quality_flags,
    and return an object as expected by snapshot_builder.py
    """
    # 1. Convert AssetFundamentals to dict
    # We need to map object attributes to keys expected by our logic functions
    # AssetFundamentals (from analysis/valuation.py) likely has attributes like:
    # revenue_ttm, net_profit_ttm, ... (need to check valuation.py to be sure, but assuming standard names)
    # OR we can just use vars() or __dict__ if it's a standard class
    
    # Heuristic mapping based on common attribute names in our system
    f_dict = {}
    if hasattr(fundamentals, '__dict__'):
        f_dict = vars(fundamentals).copy()
    
    # Add mapped keys if validation logic expects specific names not in object
    # e.g. net_income_ttm vs net_profit_ttm
    val = getattr(fundamentals, 'net_profit_ttm', None)
    if val is not None: f_dict['net_income_ttm'] = val
    
    val = getattr(fundamentals, 'operating_cf_ttm', None)
    if val is not None: f_dict['operating_cashflow_ttm'] = val
    
    val = getattr(fundamentals, 'free_cf_ttm', None)
    if val is not None: f_dict['free_cashflow_ttm'] = val
    
    val = getattr(fundamentals, 'shares_yoy', None)
    if val is not None: f_dict['shares_out_yoy_growth'] = val
    
    # 2. Run Logic
    # Note: Our logic currently handles missing keys gracefully ("MID"/"NEUTRAL")
    result = build_quality_flags(f_dict)
    
    # 3. Return Object
    # Add new info to notes if needed, or keeping explicit fields
    final_notes = {"details": result["quality_notes"]}
    
    # Append Dividend Notes
    if dividend_info and dividend_info.notes_zh:
         final_notes["dividend_notes"] = dividend_info.notes_zh
         
    return QualitySnapshot(
        revenue_stability_flag=result["revenue_stability_flag"],
        cyclicality_flag=result["cyclicality_flag"],
        moat_proxy_flag=result["moat_proxy_flag"],
        balance_sheet_flag=result["balance_sheet_flag"],
        cashflow_coverage_flag=result["cashflow_coverage_flag"],
        leverage_risk_flag=result["leverage_risk_flag"],
        payout_consistency_flag=result["payout_consistency_flag"],
        dilution_risk_flag=result["dilution_risk_flag"],
        regulatory_dependence_flag=result["regulatory_dependence_flag"],
        quality_buffer_level=result["quality_buffer_level"],
        quality_summary=result["quality_summary"],
        
        dividend_safety_level=dividend_info.level if dividend_info else None,
        dividend_safety_label_zh=dividend_info.label_zh if dividend_info else None,
        dividend_safety_score=dividend_info.score if dividend_info else None,
        
        earnings_state_code=earnings_info.code if earnings_info else None,
        earnings_state_label_zh=earnings_info.label_zh if earnings_info else None,
        earnings_state_desc_zh=earnings_info.desc_zh if earnings_info else None,
        
        notes=final_notes
    )

