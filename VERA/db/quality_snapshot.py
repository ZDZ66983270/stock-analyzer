# db/quality_snapshot.py
from __future__ import annotations

import json
from typing import Dict, Any, Optional
from db.connection import get_connection

BQ_FLAG = {"STRONG", "MID", "WEAK", "-"}
CYCL_FLAG = {"LOW", "MID", "HIGH", "-"}
GOV_FLAG = {"POSITIVE", "NEUTRAL", "NEGATIVE", "-"}
DIL_FLAG = {"LOW", "MID", "HIGH", "-"}
BUFFER_LEVEL = {"STRONG", "MODERATE", "WEAK", "-"}

def _assert_enum(name: str, value: Optional[str], allowed: set):
    if value is None:
        raise ValueError(f"[quality_snapshot] {name} is None (must be one of {sorted(allowed)})")
    v = value.strip().upper()
    if v not in allowed:
        raise ValueError(f"[quality_snapshot] {name}='{value}' not in {sorted(allowed)}")
    return v

def save_quality_snapshot(
    *,
    snapshot_id: str,
    asset_id: str,
    revenue_stability_flag: str,
    cyclicality_flag: str,
    moat_proxy_flag: str,
    balance_sheet_flag: str,
    cashflow_coverage_flag: str,
    leverage_risk_flag: str,
    payout_consistency_flag: str,
    dilution_risk_flag: str,
    regulatory_dependence_flag: str,
    quality_buffer_level: str,
    quality_summary: str,
    notes: Optional[Dict[str, Any]] = None,
):
    # ---- Enum validation (hard) ----
    revenue_stability_flag = _assert_enum("revenue_stability_flag", revenue_stability_flag, BQ_FLAG)
    cyclicality_flag = _assert_enum("cyclicality_flag", cyclicality_flag, CYCL_FLAG)
    moat_proxy_flag = _assert_enum("moat_proxy_flag", moat_proxy_flag, BQ_FLAG)

    balance_sheet_flag = _assert_enum("balance_sheet_flag", balance_sheet_flag, BQ_FLAG)
    cashflow_coverage_flag = _assert_enum("cashflow_coverage_flag", cashflow_coverage_flag, BQ_FLAG)
    leverage_risk_flag = _assert_enum("leverage_risk_flag", leverage_risk_flag, CYCL_FLAG)

    payout_consistency_flag = _assert_enum("payout_consistency_flag", payout_consistency_flag, GOV_FLAG)
    dilution_risk_flag = _assert_enum("dilution_risk_flag", dilution_risk_flag, DIL_FLAG)
    regulatory_dependence_flag = _assert_enum("regulatory_dependence_flag", regulatory_dependence_flag, CYCL_FLAG)

    quality_buffer_level = _assert_enum("quality_buffer_level", quality_buffer_level, BUFFER_LEVEL)

    # ---- Notes handling ----
    # 如果你未来愿意加 quality_notes TEXT：直接落库 notes_json
    notes_json = json.dumps(notes or {}, ensure_ascii=False)
    # 不改表时：把 notes 的摘要拼到 summary（已在 quality_assessment.py 做过 line2）
    # 这里不重复拼接，避免重复。

    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        # 尝试写入带 quality_notes 的版本；若表没有该字段则回退（兼容 MVP 不 ALTER）
        try:
            cur.execute(
                """
                INSERT OR REPLACE INTO quality_snapshot (
                    snapshot_id, asset_id,
                    revenue_stability_flag, cyclicality_flag, moat_proxy_flag,
                    balance_sheet_flag, cashflow_coverage_flag, leverage_risk_flag,
                    payout_consistency_flag, dilution_risk_flag, regulatory_dependence_flag,
                    quality_buffer_level, quality_summary,
                    quality_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot_id, asset_id,
                    revenue_stability_flag, cyclicality_flag, moat_proxy_flag,
                    balance_sheet_flag, cashflow_coverage_flag, leverage_risk_flag,
                    payout_consistency_flag, dilution_risk_flag, regulatory_dependence_flag,
                    quality_buffer_level, quality_summary,
                    notes_json
                )
            )
        except Exception:
            # 回退：不含 quality_notes 的 schema
            cur.execute(
                """
                INSERT OR REPLACE INTO quality_snapshot (
                    snapshot_id, asset_id,
                    revenue_stability_flag, cyclicality_flag, moat_proxy_flag,
                    balance_sheet_flag, cashflow_coverage_flag, leverage_risk_flag,
                    payout_consistency_flag, dilution_risk_flag, regulatory_dependence_flag,
                    quality_buffer_level, quality_summary
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot_id, asset_id,
                    revenue_stability_flag, cyclicality_flag, moat_proxy_flag,
                    balance_sheet_flag, cashflow_coverage_flag, leverage_risk_flag,
                    payout_consistency_flag, dilution_risk_flag, regulatory_dependence_flag,
                    quality_buffer_level, quality_summary
                )
            )

        conn.commit()
    finally:
        if conn:
            conn.close()
