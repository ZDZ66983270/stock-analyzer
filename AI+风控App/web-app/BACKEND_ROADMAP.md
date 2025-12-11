# 后台开发路线图

## 当前架构概览

### 已实现的功能

**技术栈**:
- **框架**: FastAPI + SQLModel + SQLite
- **数据获取**: akshare (免费行情数据)
- **定时任务**: APScheduler
- **技术指标**: pandas (MACD, RSI, KDJ计算)

**核心API**:
1. `/api/watchlist` - 自选列表管理
2. `/api/market-data/{symbol}` - 历史行情数据
3. `/api/save-analysis` - 保存AI分析结果
4. `/api/latest-analysis/{symbol}` - 获取最新分析
5. `/api/sync-market` - 手动同步市场数据
6. `/api/fetch-stock` - 添加股票并获取数据

**数据模型**:
- `Watchlist` - 自选列表
- `MarketData` - 市场行情数据
- `AssetAnalysisHistory` - AI分析历史记录
- `MacroData` - 宏观数据(待完善)

---

## 后台开发优先级路线图

### 阶段一:核心AI分析引擎 (高优先级)

#### 1.1 实现真实的AI分析模型

**目标**: 替换前端的mock AI,实现后端真实分析

**任务**:
- [ ] 创建 `analysis_engine.py` 模块
- [ ] 实现乔治·达格尼诺周期模型
  - 宏观经济指标获取(GDP、CPI、利率等)
  - 库存周期分析
  - 信贷脉冲计算
- [ ] 实现股票分析模型
  - 技术分析模型(基于已有的MACD/KDJ/RSI)
  - 基本面分析(PE、PB、ROE等)
  - 舆情分析(新闻、社交媒体)
- [ ] 实现基金分析模型
  - 风格漂移分析
  - 费用效率分析
  - 持仓集中度分析
  - 跟踪误差分析
  - 资金流向分析

**API端点**:
```python
POST /api/analyze/{symbol}
{
  "enabled_models": ["dagnino", "technical", "fundamental"],
  "asset_type": "stock" | "fund"
}

Response:
{
  "status": "success",
  "analysis": {
    "stockCycle": "筑底期",
    "sectorCycle": "复苏确认",
    "macroCycle": "宽信用初期",
    "total_score": 78,
    "weighted_score": 82,
    "signal_value": 1.8,
    "summary": "...",
    "model_details": [...]
  }
}
```

**技术选型**:
- **AI模型**: 可选择OpenAI API、本地LLM(如Llama)或规则引擎
- **数据源**: akshare + yfinance + 自定义爬虫
- **缓存**: Redis(可选,提升性能)

---

#### 1.2 图片识别与数据提取

**目标**: 实现用户上传截图补充数据的功能

**任务**:
- [ ] 创建 `image_processor.py` 模块
- [ ] 集成OCR引擎(Tesseract或云服务)
- [ ] 实现表格识别和数据提取
- [ ] 数据验证和清洗
- [ ] 保存到数据库

**API端点**:
```python
POST /api/upload-screenshot
Content-Type: multipart/form-data

{
  "file": <image_file>,
  "symbol": "600519.sh",
  "data_type": "financial_report" | "price_chart" | "other"
}

Response:
{
  "status": "success",
  "extracted_data": {
    "revenue": 123.45,
    "net_profit": 45.67,
    ...
  },
  "confidence": 0.95
}
```

**技术选型**:
- **OCR**: Tesseract (开源) 或 Google Cloud Vision API
- **图像处理**: OpenCV + PIL
- **表格识别**: PaddleOCR (支持中文表格)
- **存储**: 图片存储在本地或云存储(如S3)

---

### 阶段二:数据增强与管理 (中优先级)

#### 2.1 扩展数据源

**任务**:
- [ ] 集成更多免费数据源
  - iFinance API集成
  - 东方财富网爬虫
  - 新浪财经API
- [ ] 实现数据源优先级和fallback机制
- [ ] 数据质量监控和告警

#### 2.2 基金数据专项支持

**任务**:
- [ ] 基金净值历史数据获取
- [ ] 基金持仓数据获取
- [ ] 基金费用数据获取
- [ ] 基准指数数据获取(MSCI、S&P 500、Nasdaq 100)

**新增模型**:
```python
class FundData(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    date: str
    nav: float  # 净值
    accumulated_nav: float  # 累计净值
    dividend: float | None = None
    
class FundHolding(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    date: str
    stock_symbol: str
    stock_name: str
    percentage: float  # 持仓占比
    
class FundFees(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    symbol: str = Field(index=True, unique=True)
    management_fee: float
    subscription_fee: float
    redemption_fee: float
    expense_ratio: float
```

---

#### 2.3 宏观数据完善

**任务**:
- [ ] 实现宏观经济指标获取
  - GDP增长率
  - CPI/PPI
  - 利率(国债收益率)
  - 汇率
  - M2增速
  - 社融数据
- [ ] 定时更新机制
- [ ] 数据可视化API

**API端点**:
```python
GET /api/macro-data?indicators=gdp,cpi,interest_rate&start_date=2023-01-01

Response:
{
  "status": "success",
  "data": [
    {
      "date": "2023-01-01",
      "gdp_growth": 5.2,
      "cpi": 2.1,
      "interest_rate": 2.35
    },
    ...
  ]
}
```

---

### 阶段三:用户体验优化 (中优先级)

#### 3.1 分析历史管理

**任务**:
- [ ] 实现分析历史列表API
- [ ] 分析结果对比功能
- [ ] 分析报告导出(PDF/Excel)

**API端点**:
```python
GET /api/analysis-history/{symbol}?limit=10

POST /api/export-analysis/{analysis_id}
```

#### 3.2 用户偏好设置

**任务**:
- [ ] 用户配置管理(颜色约定、默认模型等)
- [ ] 自定义模型权重
- [ ] 告警阈值设置

**新增模型**:
```python
class UserSettings(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    color_convention: str = "chinese"  # or "us"
    default_models: str  # JSON string
    alert_thresholds: str  # JSON string
```

---

### 阶段四:性能与可靠性 (低优先级,但重要)

#### 4.1 性能优化

**任务**:
- [ ] 添加Redis缓存层
- [ ] 数据库查询优化(索引、分页)
- [ ] 异步任务队列(Celery)
- [ ] API限流和防护

#### 4.2 监控与日志

**任务**:
- [ ] 结构化日志(loguru)
- [ ] 性能监控(Prometheus + Grafana)
- [ ] 错误追踪(Sentry)
- [ ] 健康检查端点增强

#### 4.3 数据备份与恢复

**任务**:
- [ ] 自动数据库备份
- [ ] 数据导入导出工具
- [ ] 灾难恢复方案

---

## 技术选型建议

### AI分析引擎

**方案A: 规则引擎 (推荐起步)**
- 优点: 可控、快速、无外部依赖
- 缺点: 需要手动编写规则
- 适用: MVP阶段

**方案B: OpenAI API**
- 优点: 强大、灵活、快速集成
- 缺点: 成本、需要网络、数据隐私
- 适用: 快速验证想法

**方案C: 本地LLM**
- 优点: 隐私、无成本、可定制
- 缺点: 需要GPU、部署复杂
- 适用: 长期方案

### 图片识别

**方案A: Tesseract (推荐)**
- 优点: 免费、开源、支持中文
- 缺点: 准确率一般
- 适用: MVP阶段

**方案B: PaddleOCR**
- 优点: 中文支持好、表格识别强
- 缺点: 模型较大
- 适用: 生产环境

**方案C: 云服务(Google Vision/百度OCR)**
- 优点: 准确率高、维护少
- 缺点: 成本、网络依赖
- 适用: 高精度需求

---

## 快速开始:第一步实施

### 推荐从这里开始

**目标**: 实现一个最简单的AI分析引擎,替换前端mock

**步骤**:

1. **创建分析引擎模块**
```bash
cd backend
touch analysis_engine.py
```

2. **实现基础分析逻辑**
```python
# analysis_engine.py
from sqlmodel import Session, select
from models import MarketData
import pandas as pd

class AnalysisEngine:
    def __init__(self, session: Session):
        self.session = session
    
    def analyze_stock(self, symbol: str, enabled_models: dict):
        """分析股票"""
        # 1. 获取历史数据
        stmt = select(MarketData).where(
            MarketData.symbol == symbol
        ).order_by(MarketData.date.desc()).limit(250)
        data = self.session.exec(stmt).all()
        
        if not data:
            raise ValueError(f"No data for {symbol}")
        
        # 2. 计算技术指标(已有)
        df = self._to_dataframe(data)
        
        # 3. 运行各个模型
        results = {
            "model_details": []
        }
        
        if enabled_models.get("technical"):
            tech_result = self._technical_analysis(df)
            results["model_details"].append(tech_result)
        
        if enabled_models.get("dagnino"):
            cycle_result = self._cycle_analysis(df)
            results["model_details"].append(cycle_result)
        
        # 4. 综合评分
        results["total_score"] = self._calculate_total_score(results["model_details"])
        results["weighted_score"] = self._calculate_weighted_score(results["model_details"])
        results["signal_value"] = self._calculate_signal(results["model_details"])
        results["summary"] = self._generate_summary(results)
        
        return results
    
    def _technical_analysis(self, df):
        """技术分析模型"""
        latest = df.iloc[-1]
        
        # MACD分析
        macd_signal = "看多" if latest['macd'] > latest['signal'] else "看空"
        
        # RSI分析
        rsi_signal = "超买" if latest['rsi'] > 70 else "超卖" if latest['rsi'] < 30 else "中性"
        
        # 综合评分
        score = 50  # 基础分
        if macd_signal == "看多": score += 20
        if rsi_signal == "中性": score += 10
        
        return {
            "name": "技术分析模型",
            "signal": macd_signal,
            "score": score,
            "weight": 0.2,
            "description": f"MACD {macd_signal}, RSI {rsi_signal}",
            "details": {
                "macd": {
                    "dif": f"{latest['macd']:.2f}",
                    "dea": f"{latest['signal']:.2f}",
                    "bar": f"{latest['hist']:.2f}",
                    "conclusion": f"MACD {macd_signal}"
                },
                "rsi": {
                    "rsi6": f"{latest['rsi']:.1f}",
                    "rsi12": f"{latest['rsi']:.1f}",
                    "rsi24": f"{latest['rsi']:.1f}",
                    "conclusion": f"RSI {rsi_signal}"
                }
            }
        }
    
    def _cycle_analysis(self, df):
        """周期分析模型(简化版)"""
        # 简化:基于价格趋势判断周期
        ma20 = df['close'].rolling(20).mean().iloc[-1]
        ma60 = df['close'].rolling(60).mean().iloc[-1]
        current_price = df['close'].iloc[-1]
        
        if current_price > ma20 > ma60:
            cycle = "复苏期"
            signal = "看多"
            score = 85
        elif current_price > ma60:
            cycle = "扩张期"
            signal = "看多"
            score = 75
        else:
            cycle = "衰退期"
            signal = "看空"
            score = 40
        
        return {
            "name": "乔治·达格尼诺周期模型",
            "signal": signal,
            "score": score,
            "weight": 0.4,
            "description": f"当前处于{cycle},建议{signal}"
        }
    
    # ... 其他辅助方法
```

3. **添加API端点**
```python
# main.py
from analysis_engine import AnalysisEngine

class AnalyzeRequest(BaseModel):
    enabled_models: dict = {
        "dagnino": True,
        "technical": True,
        "fundamental": True,
        "sentiment": True
    }

@app.post("/api/analyze/{symbol}")
def analyze_asset(symbol: str, request: AnalyzeRequest, session: Session = Depends(get_session)):
    try:
        engine = AnalysisEngine(session)
        result = engine.analyze_stock(symbol, request.enabled_models)
        
        # 保存分析结果
        history = AssetAnalysisHistory(
            symbol=symbol,
            full_result_json=json.dumps(result)
        )
        session.add(history)
        session.commit()
        
        return {"status": "success", "analysis": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

4. **前端调用真实API**
```javascript
// FundDetailView.jsx 或 StockDetailView.jsx
const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
        // 调用后端真实API
        const response = await fetch(`http://localhost:8000/api/analyze/${asset.symbol}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                enabled_models: enabledModels
            })
        });
        
        const data = await response.json();
        if (data.status === 'success') {
            setAnalysisResult(data.analysis);
        }
    } catch (e) {
        console.error("Analysis failed", e);
    } finally {
        setAnalyzing(false);
    }
};
```

---

## 总结

**立即可以开始的工作**:
1. ✅ 实现基础AI分析引擎(规则引擎版本)
2. ✅ 完善基金数据模型和API
3. ✅ 集成图片OCR功能

**中期目标**:
- 完善各个分析模型
- 扩展数据源
- 优化性能

**长期目标**:
- 引入真实AI模型
- 构建完整的投资决策系统
- 支持多用户和权限管理

从**阶段一的1.1**开始,先实现一个简单但可用的AI分析引擎,这样前端就可以调用真实的后端分析,而不是mock数据了!
