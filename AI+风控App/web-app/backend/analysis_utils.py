import pandas as pd
from typing import List, Optional
from datetime import datetime
try:
    from models import SplitFact
except ImportError:
    # Fallback/Mock for testing if models not in path
    class SplitFact:
        effective_date: str
        split_factor: float

def build_split_adjusted_close(
    df_price: pd.DataFrame,    # columns: trade_date/index, close (raw)
    splits: List[SplitFact],   # 拆股事件列表
) -> pd.Series:
    """
    输入原始收盘价 + 拆股事实，返回只调整拆股/合并后的价格序列。
    约定：保持“尾端对齐”，即最新价格与原始 close 基本一致，历史价格反向复权。
    
    Args:
        df_price: DataFrame with 'close' column and datetime index (or 'trade_date' col)
        splits: List of SplitFact objects
        
    Returns:
        pd.Series: Split-Adjusted Close Price
    """
    if df_price.empty:
        return pd.Series(dtype=float)

    # 1. 确保索引为 datetime
    df = df_price.copy()
    if 'trade_date' in df.columns and not isinstance(df.index, pd.DatetimeIndex):
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df = df.set_index('trade_date')
    
    if not isinstance(df.index, pd.DatetimeIndex):
         # 尝试转换 index
         df.index = pd.to_datetime(df.index)
         
    if 'close' not in df.columns:
        # Fallback for Series input
        if isinstance(df, pd.Series):
             s = df.sort_index().astype(float)
        else:
             raise ValueError("Input must have 'close' column")
    else:
        s = df['close'].sort_index().astype(float)

    if not splits:
        return s

    # 2. 按生效日从近到远处理 (Reverse Order)
    # 保持最新价格不变，历史价格根据 split factor 调整
    # 例如：5-for-1 split (factor=5) on 2020-08-31
    # 意味着 2020-08-31 之前的价格看起来只有原来的 1/5
    # 为了保持最新价格不变（对齐当前），我们需要将 2020-08-31 之前的价格 / 5.0
    
    sorted_splits = sorted(splits, key=lambda x: x.effective_date, reverse=True)
    
    for fact in sorted_splits:
        factor = float(fact.split_factor or 0)
        if factor <= 0 or factor == 1.0:
            continue
            
        try:
            split_date = pd.to_datetime(fact.effective_date).date()
            # 找到 split_date 之前的所有记录
            # 注意: effective_date 是生效日，该日及之后已经是新价格
            # 该日之前是旧价格。旧价格需要除以 factor 才能与新价格对齐。
            # Case 1: 5-for-1 split (Split, factor=5) -> Old price (high) / 5 = New price (low scale)
            # Wait, user requirement: "保持最新价格不变"
            # If TSLA splits 5:1, price drops from 2000 to 400.
            # To make history align with 400, old prices (2000) must be divided by 5.
            # Correct.
            
            # Case 2: 1-for-5 reverse split (Merge, factor=0.2) -> Old price (low) / 0.2 = New price (high scale)
            # Correct.
            
            mask = s.index.date < split_date
            s.loc[mask] = s.loc[mask] / factor
            
        except Exception as e:
            print(f"⚠️ Error applying split {fact}: {e}")
            continue

    return s
