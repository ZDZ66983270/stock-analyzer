PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE financial_fundamentals ( asset_id TEXT NOT NULL, as_of_date DATE NOT NULL, revenue_ttm REAL, net_income_ttm REAL, operating_cashflow_ttm REAL, free_cashflow_ttm REAL, total_assets REAL, total_liabilities REAL, total_debt REAL, cash_and_equivalents REAL, net_debt REAL, debt_to_equity REAL, interest_coverage REAL, current_ratio REAL, dividend_yield REAL, payout_ratio REAL, buyback_ratio REAL, data_source TEXT DEFAULT 'yahoo', currency TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (asset_id, as_of_date), FOREIGN KEY (asset_id) REFERENCES assets(asset_id) );
COMMIT;
