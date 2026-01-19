CREATE TABLE IF NOT EXISTS vera_price_cache (
    symbol TEXT,
    trade_date DATE,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    source TEXT,
    PRIMARY KEY (symbol, trade_date)
);

CREATE TABLE IF NOT EXISTS vera_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT,
    anchor_date DATE,
    created_at DATETIME
);

CREATE TABLE IF NOT EXISTS vera_risk_metrics (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,

    snapshot_id        INTEGER NOT NULL,
    metric_name        TEXT NOT NULL,     -- max_drawdown / volatility
    metric_value       REAL NOT NULL,

    window             INTEGER,           -- 252 / 60 / 5 等
    parameters         TEXT,              -- JSON 字符串

    unit               TEXT,              -- %, days, ratio
    computed_at        DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (snapshot_id)
        REFERENCES vera_snapshot(id)
        ON DELETE CASCADE
);

-- 1. 资产表 (assets)
CREATE TABLE IF NOT EXISTS assets (
    asset_id           TEXT PRIMARY KEY,  -- 标的代码 (如 AAPL, 00700.HK)
    symbol_name        TEXT,              -- 名称
    market             TEXT,              -- 市场 (US/HK/CN)
    industry           TEXT,              -- 行业 (用于估值锚定)
    created_at         DATETIME DEFAULT CURRENT_TIMESTAMP
);


-- 3. 财务历史表 (financial_history) (新增)
CREATE TABLE IF NOT EXISTS financial_history (
    asset_id           TEXT,
    report_date        DATE,
    eps_ttm            REAL,              -- 用于计算 PE
    bps                REAL,              -- 用于计算 PB
    revenue_ttm        REAL,              -- 用于计算 PS
    net_profit_ttm     REAL,              -- 用于计算 利润率
    dividend_amount    REAL,              -- 年度分红总额
    buyback_amount     REAL,              -- 年度回购总额
    
    -- 银行股专属字段 (Bank Specific Metrics)
    npl_ratio                REAL,        -- 不良贷款率
    special_mention_ratio    REAL,        -- 关注类贷款占比
    provision_coverage       REAL,        -- 拨备覆盖率
    allowance_to_loan        REAL,        -- 拨贷比
    overdue_90_loans         REAL,        -- 逾期 90 天以上贷款余额
    npl_balance              REAL,        -- 不良贷款余额
    
    PRIMARY KEY (asset_id, report_date),
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
);

-- 4. 分析快照表 (analysis_snapshot) - 核心表，原 vera_snapshot 升级版
CREATE TABLE IF NOT EXISTS analysis_snapshot (
    snapshot_id        TEXT PRIMARY KEY,  -- UUID
    asset_id           TEXT NOT NULL,
    as_of_date         DATE NOT NULL,     -- 评估日期
    risk_level         TEXT,              -- 风险等级 (High/Medium/Low)
    valuation_anchor   TEXT,              -- 选用的估值锚 (PE/PB/PS)
    valuation_status   TEXT,              -- 估值状态 (Undervalued/Fair/Overvalued)
    payout_score       INTEGER,           -- 价值兑现分 (-2 到 +2)
    is_value_trap      BOOLEAN,           -- 是否触发价值陷阱
    created_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
);

-- 5. 指标明细表 (metric_details)
CREATE TABLE IF NOT EXISTS metric_details (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id        TEXT NOT NULL,
    metric_key         TEXT NOT NULL,     -- 指标名 (e.g., max_drawdown, pe_ratio)
    value              REAL NOT NULL,     -- 绝对值
    percentile         REAL,              -- 历史分位 (0.0 - 1.0)
    FOREIGN KEY (snapshot_id) REFERENCES analysis_snapshot(snapshot_id) ON DELETE CASCADE
);

-- 6. 决策日志表 (decision_log)
CREATE TABLE IF NOT EXISTS decision_log (
    decision_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id        TEXT NOT NULL,     -- 必须关联当时的快照，用于后续复盘
    action             TEXT NOT NULL,     -- 操作 (Buy/Sell/Hold)
    context_note       TEXT,              -- 当时想法记录
    created_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (snapshot_id) REFERENCES analysis_snapshot(snapshot_id) ON DELETE CASCADE
);
-- 7. 状态机历史表 (drawdown_state_history)
CREATE TABLE IF NOT EXISTS drawdown_state_history (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id                TEXT NOT NULL,
    trade_date              DATE NOT NULL,
    
    -- 原始计算状态（未经转移规则验证）
    raw_state               TEXT NOT NULL,      -- D0-D6
    raw_metrics_snapshot    TEXT,               -- JSON: {peak, trough, recovery, current_dd}
    
    -- 确认后的状态（经过转移规则和确认期验证）
    confirmed_state         TEXT NOT NULL,      -- D0-D6
    confirm_counter         INTEGER DEFAULT 0,  -- 连续满足当前 raw_state 的天数
    days_in_state           INTEGER DEFAULT 0,  -- 在 confirmed_state 停留天数
    
    -- 转移标记
    is_transition           BOOLEAN DEFAULT 0,  -- 是否发生状态转移
    prev_state              TEXT,               -- 前一状态
    
    -- 版本控制
    state_version           TEXT DEFAULT 'v1.0', -- 状态规则版本
    
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(asset_id, trade_date),
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_state_history_asset_date ON drawdown_state_history(asset_id, trade_date DESC);

-- 8. 风险事件表 (risk_events)
CREATE TABLE IF NOT EXISTS risk_events (
    event_id                INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id                TEXT NOT NULL,
    event_type              TEXT NOT NULL,      -- SECONDARY_DRAWDOWN / FAILED_RECOVERY / STRUCTURAL_COLLAPSE
    event_start_date        DATE NOT NULL,
    event_end_date          DATE,               -- NULL if ongoing
    
    -- 状态转移信息
    state_from              TEXT NOT NULL,      -- 起始状态
    state_to                TEXT NOT NULL,      -- 目标状态
    
    -- 风险评级
    severity_level          TEXT NOT NULL,      -- 极危险 / 危险 / 警示
    
    -- 上下文快照
    volatility_at_event     REAL,
    volume_change           REAL,               -- 成交量变化
    
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_risk_events_asset ON risk_events(asset_id, event_start_date DESC);

-- 9. 用户风险画像表 (user_risk_profiles)
CREATE TABLE IF NOT EXISTS user_risk_profiles (
    profile_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    risk_tolerance_level   TEXT NOT NULL,     -- CONSERVATIVE / BALANCED / AGGRESSIVE
    
    -- 得分明细 (JSON 存储或直接分数字段)
    total_score            INTEGER NOT NULL,
    answer_set             TEXT,              -- JSON: {"Q1": "A", ...}
    
    -- 展示层偏好
    drawdown_emphasis      TEXT,              -- HIGH / MEDIUM / LOW
    warning_verbosity      TEXT,              -- DETAILED / STANDARD / MINIMAL
    color_intensity        TEXT,              -- LOW / NORMAL / GRAYSCALE
    
    profile_version        TEXT DEFAULT 'v1',
    created_at             DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 10. 风险模型快照表 (risk_card_snapshot)
CREATE TABLE IF NOT EXISTS risk_card_snapshot (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id            TEXT NOT NULL,
    asset_id               TEXT NOT NULL,
    anchor_date            DATE NOT NULL,

    -- 位置风险 (Position Risk)
    price_percentile       REAL,          -- 0 ~ 1 (历史价位分位)
    position_zone          TEXT,          -- LOW / MID / HIGH
    position_interpretation TEXT,

    -- 价格路径风险 (Path Risk)
    max_drawdown           REAL,          -- 历史最大回撤
    drawdown_stage         REAL,          -- 当前在回撤区间中的位置 (0~1)
    volatility_percentile  REAL,          -- 波动率分位 (0~1)
    path_zone              TEXT,          -- LOW / MID / HIGH
    path_interpretation    TEXT,

    -- 风险象限
    risk_quadrant          TEXT,          -- Q1 / Q2 / Q3 / Q4
    system_notes           TEXT,          -- JSON 数组：备注信息

    created_at             DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(snapshot_id) REFERENCES analysis_snapshot(snapshot_id) ON DELETE CASCADE
);

-- 11. 行为护栏标记表 (behavior_flags)
CREATE TABLE IF NOT EXISTS behavior_flags (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id            TEXT NOT NULL,
    risk_card_id           INTEGER NOT NULL,
    asset_id               TEXT NOT NULL,
    anchor_date            DATE NOT NULL,

    flag_code              TEXT NOT NULL, -- e.g. FOMO_RISK
    flag_level             TEXT NOT NULL, -- INFO / WARN / ALERT
    flag_dimension         TEXT NOT NULL, -- POSITION / PATH / COMBINED

    flag_title             TEXT NOT NULL,
    flag_description       TEXT NOT NULL,

    trigger_context        TEXT,          -- JSON：触发时的指标快照
    created_at             DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(snapshot_id) REFERENCES analysis_snapshot(snapshot_id) ON DELETE CASCADE,
    FOREIGN KEY(risk_card_id) REFERENCES risk_card_snapshot(id) ON DELETE CASCADE
);

-- 13. 基础财务事实表 (fundamentals_facts) - Standardized Source of Truth
CREATE TABLE IF NOT EXISTS fundamentals_facts (
    asset_id            TEXT NOT NULL,
    as_of_date          DATE NOT NULL,      -- 对应财报期 / 报告期
    currency            TEXT,

    -- 核心原始指标（来自财报 / 数据源）
    net_income_ttm      REAL,               -- TTM 净利润
    shares_outstanding  REAL,               -- 总股本（摊薄）
    book_value_per_sh   REAL,               -- 每股净资产（最近一期）

    -- 可选：如果数据源直接给了 ratio，就顺手存一份
    pe_ttm_raw          REAL,               -- 数据源原始 P/E (TTM)
    pb_raw              REAL,               -- 数据源原始 P/B

    -- VERA 规范化后的指标
    eps_ttm             REAL,               -- 归一化后的每股收益 (calculated)
    pe_ttm              REAL,               -- calculated: price / eps_ttm
    pb                  REAL,               -- calculated: price / bvps

    source              TEXT,               -- 'yahoo', 'akshare', etc.
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (asset_id, as_of_date)
);
