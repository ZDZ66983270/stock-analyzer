from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime

class MacroData(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    country: str = Field(index=True)  # CN or US
    month: str = Field(index=True)    # YYYY-MM
    indicator: str                    # e.g., "10y_bond"
    value: float
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AssetAnalysisHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    analysis_date: datetime = Field(default_factory=datetime.utcnow)
    full_result_json: str  # Stores the entire JSON result from AI
    screenshot_path: Optional[str] = None

class MarketData(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    market: str = Field(index=True)  # CN, HK, US
    period: str = Field(index=True)  # 1d, 1min, 5min, etc.
    date: str = Field(index=True)    # YYYY-MM-DD HH:MM:SS
    open: float
    high: float
    low: float
    close: float
    volume: int
    volume: int
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Watchlist(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True, unique=True)
    name: Optional[str] = None
    market: Optional[str] = None # CN, HK, US, inferred
    added_at: datetime = Field(default_factory=datetime.utcnow)
