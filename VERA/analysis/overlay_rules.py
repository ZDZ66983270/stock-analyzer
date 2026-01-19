import json

def _dd_rank(dd: str | None) -> int:
    # D1..D5 -> 1..5，未知 -> 0
    if not dd or not dd.startswith("D"):
        return 0
    try:
        return int(dd[1:])
    except Exception:
        return 0

def run_overlay_rules(ind: dict, sec: dict, mkt: dict) -> tuple[str, list[dict]]:
    """
    返回 (summary, flags)
    flags: [{code, level, title, detail}]
    """
    flags: list[dict] = []
    
    ind_dd = ind.get("ind_dd_state")
    sec_dd = sec.get("sector_dd_state")
    mkt_dd = mkt.get("market_dd_state")
    
    ind_path = ind.get("ind_path_risk")
    mkt_path = mkt.get("market_path_risk")
    # sec_path = sec.get("sector_path_risk") # Unused variable
    
    rs_stock_sector = sec.get("stock_vs_sector_rs_3m")
    regime = mkt.get("market_regime_label")
    
    # ---- Group A: risk source attribution (choose one) ----
    src = None
    if _dd_rank(mkt_dd) >= 4 or mkt_path == "HIGH":
        src = "SYSTEMIC"
        flags.append({
            "code": "SRC_SYSTEMIC",
            "level": "HIGH",
            "title": "系统性风险主导",
            "detail": "市场处于 D4/D5 状态或路径风险为高。"
        })
    elif _dd_rank(ind_dd) >= 4 and _dd_rank(sec_dd) >= 4:
        src = "SECTOR"
        flags.append({
            "code": "SRC_SECTOR",
            "level": "HIGH",
            "title": "板块共振风险",
            "detail": "个股与板块均处于深幅回撤状态。"
        })
    elif _dd_rank(ind_dd) >= 4 and _dd_rank(sec_dd) <= 2 and _dd_rank(mkt_dd) <= 2:
        src = "INDIVIDUAL"
        flags.append({
            "code": "SRC_INDIVIDUAL",
            "level": "HIGH",
            "title": "个股特异性风险",
            "detail": "个股处于深幅回撤，而板块/大盘未见同样压力。"
        })
    else:
        src = "MIXED"
        flags.append({
            "code": "SRC_MIXED",
            "level": "MED",
            "title": "混合风险源",
            "detail": "风险无法由单一层级完全解释。"
        })
        
    # ---- Group B: divergence vs sector ----
    if rs_stock_sector is not None:
        if rs_stock_sector < -0.05:
            flags.append({
                "code": "DIV_NEGATIVE", 
                "level": "MED",
                "title": "弱于板块",
                "detail": f"个股相对板块 RS(3m)={rs_stock_sector:.2%}."
            })
        elif rs_stock_sector > 0.05:
            flags.append({
                "code": "DIV_POSITIVE", 
                "level": "MED",
                "title": "强于板块",
                "detail": f"个股相对板块 RS(3m)={rs_stock_sector:.2%}."
            })

    # ---- Group C: consistency guardrails (UI/semantic) ----
    # 例：PathRisk HIGH 但百分比为 0/None 的 UI 拦截 —— 这里先留 hook
    # flags.append({"code": "CONSISTENCY_BLOCK_PCT", ...})

    # ---- Group D: market regime modifier ----
    # NOTE: regime string is now in Chinese from snapshot_builder
    if regime == "系统性压缩": # Systemic Compression
        flags.append({
            "code": "REGIME_COMPRESSION", 
            "level": "MED",
            "title": "相关性上升 / 选股难度增加",
            "detail": "系统性压缩降低了个股选择的优势。"
        })
    elif regime == "良性分化": # Healthy Differentiation
        flags.append({
            "code": "REGIME_DIFFERENTIATION", 
            "level": "LOW",
            "title": "市场允许多元分化",
            "detail": "个股与板块走势有更大的独立空间。"
        })

    # ---- Summary composer (1-2 sentences) ----
    parts = []
    if src == "SYSTEMIC":
        parts.append("市场处于系统性风险阶段，建议以更保守视角评估个股风险。")
    elif src == "SECTOR":
        parts.append("个股风险与板块周期高度同步。")
    elif src == "INDIVIDUAL":
        parts.append("风险主要来自个股自身，板块与大盘未见显著压力。")
    else:
        parts.append("风险驱动因素在个股、板块与市场间混合分布。")
        
    if rs_stock_sector is not None:
        if rs_stock_sector < -0.05:
            parts.append("个股跑输板块，暗示存在特异性弱势。")
        elif rs_stock_sector > 0.05:
            parts.append("个股跑赢板块；若市场环境恶化，强势可能逆转。")
            
    summary = " ".join(parts[:2])
    return summary, flags

def flags_to_json(flags: list[dict]) -> str:
    return json.dumps(flags, ensure_ascii=False)
