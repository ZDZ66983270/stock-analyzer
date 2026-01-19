from datetime import datetime
from db.connection import get_connection

def save_risk_overlay_snapshot(
    snapshot_id: str, 
    asset_id: str, 
    as_of_date: str,
    ind: dict, 
    sec: dict, 
    mkt: dict, 
    summary: str, 
    flags_json: str
):
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO risk_overlay_snapshot (
                snapshot_id, asset_id, as_of_date,
                ind_dd_state, ind_path_risk, ind_vol_regime, ind_position_pct,
                sector_etf_id, sector_dd_state, sector_path_risk, stock_vs_sector_rs_3m, sector_alignment,
                market_index_id, market_dd_state, market_path_risk, growth_vs_market_rs_3m, value_vs_market_rs_3m, market_regime_label,
                overlay_summary, overlay_flags, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot_id, 
            asset_id, 
            as_of_date,
            ind.get("ind_dd_state"), 
            ind.get("ind_path_risk"), 
            ind.get("ind_vol_regime"), 
            ind.get("ind_position_pct"),
            
            sec.get("sector_etf_id"), 
            sec.get("sector_dd_state"), 
            sec.get("sector_path_risk"), 
            sec.get("stock_vs_sector_rs_3m"), 
            sec.get("sector_alignment"),
            
            mkt.get("market_index_id"), 
            mkt.get("market_dd_state"), 
            mkt.get("market_path_risk"), 
            mkt.get("growth_vs_market_rs_3m"), 
            mkt.get("value_vs_market_rs_3m"), 
            mkt.get("market_regime_label"),
            
            summary, 
            flags_json, 
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
    finally:
        conn.close()
