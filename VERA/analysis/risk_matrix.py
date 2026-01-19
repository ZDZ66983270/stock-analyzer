import json
import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from db.connection import get_connection

# ===============================
# Path Risk mapping (authoritative)
# ===============================

PATH_ZONE_BY_DSTATE = {
    "D0": ("LOW",  "未形成完整回撤结构 (D0)"),
    "D1": ("LOW",  "正常波动期 (D1)"),
    "D2": ("MID",  "结构中性：存在回撤历史 (D2)"),
    "D3": ("MID",  "结构中性偏高：博弈区 (D3)"),
    "D4": ("HIGH", "结构高风险：敏感阶段 (D4)"),
    "D5": ("HIGH", "结构极高风险：脆弱阶段 (D5)"),
    "D6": ("LOW",  "结构强势：完全修复 (D6)"),
}

def _get_d_state(risk_metrics: Dict[str, Any]) -> Optional[str]:
    rs = risk_metrics.get("risk_state") or {}
    st = rs.get("state")
    return st if isinstance(st, str) and st.startswith("D") else None

def _get_confirmed_progress(risk_metrics: Dict[str, Any]) -> Optional[float]:
    """
    Use state-machine confirmed progress as the ONLY position progress source.
    """
    rs = risk_metrics.get("risk_state") or {}
    p = rs.get("progress")
    if p is None:
        return None
    try:
        p = float(p)
        return max(0.0, min(1.0, p))
    except Exception:
        return None

class RiskMatrixEngine:
    """
    VERA 2x2 风险矩阵引擎
    负责计算 Position Risk (X) 和 Path Risk (Y) 并生成象限与护栏。
    """
    
    def __init__(self, asset_id: str, current_price: float, risk_metrics: Dict[str, Any], as_of_date: str = None, market_context: Optional[Dict[str, Any]] = None):
        self.asset_id = asset_id
        self.current_price = current_price
        self.risk_metrics = risk_metrics # 包含 volatility, max_drawdown 等
        self.risk_metrics = risk_metrics # 包含 volatility, max_drawdown 等
        self.as_of_date = as_of_date
        
        # New Market Context Fields (Defaults)
        self.market_index_id = None
        self.market_amplification = None
        self.alpha_headroom = None
        self.market_regime = None
        
        if market_context:
            self.market_index_id = market_context.get('market_index_id')
            
            # Robust extraction for potential nested dicts
            amp = market_context.get('market_amplification_level')
            if not amp and 'market_amplifier' in market_context:
                 # Try extracting from dict if legacy/nested key exists
                 amp_dict = market_context.get('market_amplifier')
                 if isinstance(amp_dict, dict):
                     amp = amp_dict.get('amplification_level')
            self.market_amplification = amp

            ah = market_context.get('alpha_headroom')
            if isinstance(ah, dict):
                # Extract value if it is a dict (prevent SQL binding error)
                ah = ah.get('alpha_headroom', ah.get('value'))
            self.alpha_headroom = ah
            
            self.market_regime = market_context.get('market_regime') # dict with label/notes
        
    def calculate_position_risk(self) -> Tuple[float, str, str]:
        """
        Legacy wrapper for compatibility logic, delegating to new internal structure
        """
        card = self._build_position_card()
        # Fallback for interpretation logic if not present in new card
        interp = card.get("label", "位置状态待确认")
        
        # Calculate legacy percentile for compatibility if needed, or rely on progress
        # Since we are moving to progress-based, we can map progress to percentile or reuse legacy logic
        # For now, let's keep the DB logic for percentile if strictly required by other parts, 
        # or simplify to use progress as primary.
        # However, the user request specifically redefines Position logic.
        
        # The new _build_position_card uses progress. 
        # But build_risk_card expects (percentile, zone, interpretation).
        # We should map 'progress' to 'percentile' conceptually for compatibility.
        
        return card.get("progress", 0.0) or 0.0, card.get("zone", "MID"), interp

    # -------------------------------------------------
    # Position (WHERE am I on the path?)
    # -------------------------------------------------
    def _build_position_card(self) -> Dict[str, Any]:
        progress = _get_confirmed_progress(self.risk_metrics)

        # Determine zone
        if progress is None:
            zone = "Unknown"
        elif progress <= 0.05:
            zone = "Peak"
        elif progress >= 0.95:
            zone = "Trough"
        elif progress < 0.33:
            zone = "Upper"
        elif progress < 0.66:
            zone = "Middle"
        else:
            zone = "Lower"

        # UI display guardrails
        show_pct = True
        if progress is None:
            show_pct = False
        elif progress <= 0.05 or progress >= 0.95:
            show_pct = False

        return {
            "progress": progress,                           # 0~1
            "progress_pct": round(progress * 100, 1) if (show_pct and progress is not None) else None,
            "zone": zone,
            "show_progress_pct": show_pct,
            "label": self._position_label(zone, show_pct, progress),
        }

    def _position_label(self, zone: str, show_pct: bool, progress: Optional[float]) -> str:
        if not show_pct:
            if zone == "Peak":
                return "当前位置：阶段高点"
            if zone == "Trough":
                return "当前位置：阶段低点（回撤底部）"
            return "当前位置：—"
        return f"回撤阶段：{round(progress * 100, 1)}%"

    def calculate_path_risk(self) -> Tuple[float, float, str, str]:
        """
        Legacy wrapper for compatibility
        """
        # We need Position info for the guardrail logic, so we build it first
        pos_card = self._build_position_card()
        path_card = self._build_path_card(pos_card)
        
        # Extract values for legacy return signature
        # (drawdown_stage, volatility_percentile, zone, interpretation)
        
        # drawdown_stage corresponds to position progress in the new logic
        dd_stage = pos_card.get("progress", 0.0) or 0.0
        
        # Volatility percentile is not explicitly in the new path card, default to 0.5 or fetch from metrics if needed
        # The user snippet removes explicit volatility calc, so we keep it simple or fetch raw
        vol = self.risk_metrics.get('annual_volatility', 0)
        vol_percentile = 0.5 # Placeholder
        
        zone = path_card["path_risk_level"]
        interpretation = path_card["path_text"]
        
        return dd_stage, vol_percentile, zone, interpretation

    # -------------------------------------------------
    # Path (HOW dangerous is this path structurally?)
    # -------------------------------------------------
    def _build_path_card(self, position: Dict[str, Any]) -> Dict[str, Any]:
        d_state = _get_d_state(self.risk_metrics)

        if d_state and d_state in PATH_ZONE_BY_DSTATE:
            zone, text = PATH_ZONE_BY_DSTATE[d_state]
        else:
            zone, text = ("MID", "路径结构信息不足，按中性风险处理。")

        # Guardrail: HIGH path must never show misleading 0% position
        # Refined Logic: If Path is HIGH, and Position is technically near Peak (progress <= 0.1), 
        # we hide the "Peak" label to avoid "High Risk" + "Peak" contradiction? 
        # actually user code says:
        # if zone == "HIGH" ... position["label"] = "当前位置：阶段高点（结构高风险区）"
        # and show_progress_pct = False.
        if zone == "HIGH" and position.get("progress") is not None and position["progress"] <= 0.10:
            position["show_progress_pct"] = False
            position["progress_pct"] = None
            position["zone"] = "Peak"
            position["label"] = "当前位置：阶段高点（结构高风险）"

        return {
            "path_risk_level": zone,
            "path_state": d_state,
            "path_text": text,
        }

    def get_quadrant(self, pos_zone: str, path_zone: str) -> str:
        """
        映射象限
        Q1: 高位 + 低路径风险 (追涨区)
        Q2: 高位 + 高路径风险 (极危险/泡沫破裂)
        Q3: 低位 + 高路径风险 (恐慌区)
        Q4: 低位 + 低路径风险 (相对稳态)
        """
        is_pos_high = (pos_zone == "HIGH")
        is_path_high = (path_zone == "HIGH")
        
        if is_pos_high and not is_path_high: return "Q1"
        if is_pos_high and is_path_high: return "Q2"
        if not is_pos_high and is_path_high: return "Q3"
        return "Q4"

    def generate_flags(self, quadrant: str) -> List[Dict[str, str]]:
        """
        根据象限生成 Behavior Flags
        """
        flags = []
        if quadrant == "Q1":
            flags.append({
                "code": "FOMO_RISK",
                "level": "WARN",
                "dimension": "POSITION",
                "title": "追涨风险 (FOMO)",
                "description": "价格处于历史高位且波动尚未显性化，最容易诱发‘不买就错过’的过度乐观心理。"
            })
        elif quadrant == "Q2":
            flags.append({
                "code": "OVERCONFIDENCE_RISK",
                "level": "ALERT",
                "dimension": "COMBINED",
                "title": "情绪坍塌风险",
                "description": "高位叠加剧烈波动。此时极易发生‘由于不愿承认行情结束而导致的深度套牢’。"
            })
        elif quadrant == "Q3":
            flags.append({
                "code": "PANIC_SELL_RISK",
                "level": "WARN",
                "dimension": "PATH",
                "title": "杀跌风险 (PANIC)",
                "description": "价格已在地位但波动依旧剧烈，极易在黎明前夕因为生理性恐慌而错误离场。"
            })
        elif quadrant == "Q4":
            flags.append({
                "code": "FALSE_SECURITY_RISK",
                "level": "INFO",
                "dimension": "POSITION",
                "title": "相对稳态",
                "description": "当前风险结构相对友好，但需警惕‘由于长期不波动而导致的警觉性下降’。"
            })
        return flags

def build_risk_card(snapshot_id: str, asset_id: str, current_price: float, risk_metrics: Dict[str, Any], as_of_date: str = None, market_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    整合函数：生成并持久化 RiskCard
    """
    # 🔧 NEW: 使用二值化逻辑计算 Quadrant (Core Engine)
    
    # 0. Legacy Generation (Required for UI/Persistence fields)
    engine = RiskMatrixEngine(asset_id, current_price, risk_metrics, as_of_date=as_of_date, market_context=market_context)
    pos_card = engine._build_position_card()
    path_card = engine._build_path_card(pos_card)
    
    # Map back to legacy variables for persistence/UI
    pos_p = pos_card.get("progress", 0.0) or 0.0
    
    # Legacy Zone Mapping Logic (Compatible with UI labels)
    raw_pos_zone = pos_card.get("zone", "Middle")
    if raw_pos_zone in ["Peak", "Upper"]: pos_zone = "HIGH"
    elif raw_pos_zone in ["Trough", "Lower"]: pos_zone = "LOW"
    else: pos_zone = "MID"
    
    pos_interp = pos_card.get("label", "")
    
    dd_stage = pos_card.get("progress", 0.0) or 0.0
    vol_p = 0.5 # Placeholder
    path_zone = path_card.get("path_risk_level", "MID")
    path_interp = path_card.get("path_text", "")

    # 1. New Core Engine Logic
    from core.risk_quadrant import compute_position_bin, compute_path_bin, map_quadrant
    
    price_percentile = risk_metrics.get("price_percentile")
    dd_state = (risk_metrics.get("risk_state") or {}).get("state")
    
    # 如果没有 price_percentile，从 progress 临时推算（兼容）
    if price_percentile is None and dd_stage is not None:
        price_percentile = 1.0 - dd_stage  # progress 0=peak → percentile 1.0
    
    # Ensure 0.0 fallbacks
    if price_percentile is None: price_percentile = 0.0
    if dd_state is None: dd_state = "D0" # default
    
    # Core Engine Calculation
    # Note: Engine expects 0-100 for position
    pos_bin = compute_position_bin(price_percentile * 100)
    path_bin = compute_path_bin(dd_state)
    q_info = map_quadrant(pos_bin, path_bin)
    
    quadrant = q_info.quadrant
    
    # Legacy flag generation is deprecated. Phase 4 will introduce Behavior Engine.
    # We keep empty flags for now or simple default to avoid errors until Phase 4.
    flags = [] # behavior engine will populate later

    # UI Flag from position card logic
    show_drawdown_progress = pos_card.get("show_progress_pct", True)

    card_data = {
        "snapshot_id": snapshot_id,
        "asset_id": asset_id,
        "anchor_date": risk_metrics.get('report_date'),
        "price_percentile": price_percentile, 
        "pos_bin": pos_bin,
        "path_bin": path_bin,
        "position_zone": pos_zone,
        "position_interpretation": pos_interp,
        "max_drawdown": risk_metrics.get('max_drawdown'),
        "drawdown_stage": dd_stage,
        "volatility_percentile": vol_p,
        "path_risk_level": path_zone,          # LOW/MID/HIGH (保留用于展示细节)
        "path_state": dd_state,                # D0-D5
        "d_state": dd_state,                   # Alias for compatibility
        "path_interpretation": path_interp,
        "risk_quadrant": quadrant,             # Q1-Q4 (来自二值化计算)
        "system_notes": json.dumps(["核心风险维度已对齐 VERA 2.0 规范"]),
        "show_drawdown_progress": show_drawdown_progress, # UI Control Flag
        "market_regime": None, # Defaut Value
        "market_regime": None, # Defaut Value
        "annual_volatility": risk_metrics.get("annual_volatility"), # Pass through for dashboard display
        "volatility_1y": risk_metrics.get("volatility_1y"),         # NEW
        "volatility_10y": risk_metrics.get("volatility_10y"),       # NEW
        
        # MDD Details
        "mdd_peak_date": risk_metrics.get("mdd_peak_date"),
        "mdd_valley_date": risk_metrics.get("mdd_valley_date"),
        "mdd_peak_price": risk_metrics.get("mdd_peak_price"),
        "mdd_valley_price": risk_metrics.get("mdd_valley_price"),
        "mdd_valley_price": risk_metrics.get("mdd_valley_price"),
        "recovery_end_date": risk_metrics.get("recovery_end_date"),
        "current_peak_date": risk_metrics.get("current_peak_date"), # NEW: Pass through for UI
        "recovery_progress": risk_metrics.get("recovery_progress", 0.0), # NEW: Recovery Progress
        "current_drawdown": risk_metrics.get("current_drawdown", 0.0), # NEW: Current Drawdown
        
        # New Market Context (DB Columns)
        "market_index_asset_id": engine.market_index_id,
        "market_amplification_level": engine.market_amplification,
        "alpha_headroom": engine.alpha_headroom,
        "market_regime_label": engine.market_regime.get('label') if engine.market_regime else None,
        "market_regime_notes": engine.market_regime.get('notes') if engine.market_regime else None
    }

    # Inject Structured Market Regime if context provided
    if market_context:
        card_data["market_regime"] = {
            "market_index": market_context.get("market_index_symbol"),
            "index_risk_state": market_context.get("index_risk_state"),
            "amplification_level": market_context["market_amplifier"]["amplification_level"],
            "amplifier_disabled": market_context["market_amplifier"]["disabled"],
            "alpha_headroom": market_context["alpha_headroom"]["alpha_headroom"],
            "regime_label": market_context.get("regime_label"),
            "notes": (
                market_context["market_amplifier"]["notes"]
                + market_context["alpha_headroom"]["notes"]
            )
        }
    
    # 持久化
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # 1. 插入 RiskCard
        cursor.execute("""
            INSERT INTO risk_card_snapshot (
                snapshot_id, asset_id, anchor_date,
                price_percentile, position_zone, position_interpretation,
                max_drawdown, drawdown_stage, volatility_percentile,
                path_zone, path_interpretation, risk_quadrant, system_notes,
                market_index_asset_id, market_amplification_level, alpha_headroom,
                market_regime_label, market_regime_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            card_data['snapshot_id'], card_data['asset_id'], card_data['anchor_date'],
            card_data['price_percentile'], card_data['position_zone'], card_data['position_interpretation'],
            card_data['max_drawdown'], card_data['drawdown_stage'], card_data['volatility_percentile'],
            card_data['path_risk_level'], card_data['path_interpretation'], card_data['risk_quadrant'], card_data['system_notes'],
            card_data['market_index_asset_id'], card_data['market_amplification_level'], card_data['alpha_headroom'],
            card_data['market_regime_label'], card_data['market_regime_notes']
        ))
        card_id = cursor.lastrowid
        
        # 2. 插入 Behavior Flags
        for f in flags:
            cursor.execute("""
                INSERT INTO behavior_flags (
                    snapshot_id, risk_card_id, asset_id, anchor_date,
                    flag_code, flag_level, flag_dimension, flag_title, flag_description, trigger_context
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                card_data['snapshot_id'], card_id, card_data['asset_id'], card_data['anchor_date'],
                f['code'], f['level'], f['dimension'], f['title'], f['description'],
                json.dumps({
                    "quadrant": quadrant,
                    "pos_p": pos_p,
                    "vol": risk_metrics.get('annual_volatility')
                })
            ))
            
        conn.commit()
        return card_data
    finally:
        conn.close()
