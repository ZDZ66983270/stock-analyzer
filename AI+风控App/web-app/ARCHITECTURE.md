# 笨 AI 投资风险评价 - 系统架构设计

## 系统概览

本系统采用前后端分离架构,支持灵活的部署方式和多端访问。

```mermaid
graph TB
    subgraph "前端 Frontend"
        A[PC管理端<br/>Electron/Web]
        B[移动端<br/>iOS/Android App]
        C[移动Web<br/>浏览器访问]
    end
    
    subgraph "后端 Backend"
        D[FastAPI服务器<br/>本地/云端]
        E[SQLite/PostgreSQL<br/>数据库]
        F[数据获取服务<br/>akshare/iFinance]
        G[AI分析引擎<br/>模型管理]
    end
    
    subgraph "外部服务"
        H[应用商店<br/>App Store/Google Play]
        I[云服务<br/>AWS/阿里云]
    end
    
    A --> D
    B --> D
    C --> D
    D --> E
    D --> F
    D --> G
    B -.发布.-> H
    D -.部署.-> I
```

---

## 一、后端架构

### 1.1 部署方案

后端支持两种部署模式:

#### 方案A: 本地部署 (开发/个人使用)

**适用场景**:
- 开发调试
- 个人使用
- 数据隐私要求高

**部署方式**:
```bash
# 本地运行
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**特点**:
- ✅ 数据完全本地化
- ✅ 无服务器成本
- ✅ 快速开发迭代
- ❌ 仅限局域网访问
- ❌ 需要电脑常开

**数据库**: SQLite (轻量级,单文件)

---

#### 方案B: 云端部署 (生产环境)

**适用场景**:
- 正式发布
- 多用户访问
- 移动端App

**部署方式**:

**选项1: 使用Docker容器**
```bash
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**选项2: 云平台部署**
- **AWS**: EC2 + RDS (PostgreSQL)
- **阿里云**: ECS + RDS
- **Heroku**: 一键部署(适合小规模)
- **Railway/Render**: 简化部署

**特点**:
- ✅ 全球访问
- ✅ 高可用性
- ✅ 自动扩展
- ✅ 专业数据库
- ❌ 需要服务器成本
- ❌ 需要运维知识

**数据库**: PostgreSQL (生产级)

**推荐配置**:
```yaml
# 小规模(< 1000用户)
- 服务器: 2核4G
- 数据库: PostgreSQL 基础版
- 存储: 50GB SSD
- 成本: ~$20-50/月

# 中等规模(1000-10000用户)
- 服务器: 4核8G + 负载均衡
- 数据库: PostgreSQL 标准版
- 存储: 200GB SSD
- 成本: ~$100-200/月
```

---

### 1.2 后端功能模块

```
backend/
├── main.py                 # FastAPI主应用
├── analysis_engine.py      # AI分析引擎
├── models.py              # 数据模型
├── database.py            # 数据库连接
├── data_fetcher.py        # 数据获取
├── image_processor.py     # 图片OCR(待开发)
├── auth.py                # 用户认证(待开发)
├── admin_api.py           # 管理员API(待开发)
└── requirements.txt       # 依赖包
```

**核心API分类**:

1. **公共API** (移动端和PC端都可访问)
   - `GET /api/watchlist` - 获取自选列表
   - `GET /api/market-data/{symbol}` - 获取行情数据
   - `POST /api/analyze/{symbol}` - 执行AI分析
   - `POST /api/upload-screenshot` - 上传截图

2. **管理员API** (仅PC管理端)
   - `POST /api/admin/models` - 新增/修改分析模型
   - `GET /api/admin/system-status` - 系统监控
   - `POST /api/admin/data-sync` - 手动同步数据
   - `GET /api/admin/logs` - 查看系统日志

---

## 二、前端架构

### 2.1 PC管理端 (Admin Dashboard)

**技术栈**: React + Electron (桌面应用)

**角色定位**: 系统管理员

**核心功能**:

1. **系统监控**
   - 实时查看后端运行状态
   - 数据同步状态监控
   - API调用统计
   - 错误日志查看

2. **模型管理** (与AI助手协作)
   - 查看现有分析模型
   - 新增自定义模型
   - 修改模型参数
   - 测试模型效果
   - 模型版本管理

3. **数据管理**
   - 手动触发数据同步
   - 数据质量检查
   - 数据导入导出
   - 用户上传截图审核

4. **用户管理** (未来功能)
   - 用户列表
   - 权限管理
   - 使用统计

**界面布局**:
```
┌─────────────────────────────────────────┐
│  Logo    系统监控  模型管理  数据管理    │
├─────────────────────────────────────────┤
│ 侧边栏    │  主内容区                   │
│           │                             │
│ - 仪表盘  │  [实时数据图表]            │
│ - 模型    │  [系统状态卡片]            │
│ - 数据    │  [AI助手对话框]            │
│ - 日志    │                             │
│           │                             │
└───────────┴─────────────────────────────┘
```

**开发路径**:
```bash
# 当前已有Electron基础
npm run electron:dev

# 未来需要添加管理界面
src/
├── admin/              # 新增管理端页面
│   ├── Dashboard.jsx
│   ├── ModelManager.jsx
│   ├── DataManager.jsx
│   └── SystemLogs.jsx
└── components/
    └── AIAssistant.jsx # AI助手组件
```

---

### 2.2 移动端 (Mobile App)

**技术栈**: React + Capacitor (跨平台)

**角色定位**: 普通用户

**访问方式**:

#### 方式1: 原生App (推荐,最终目标)
- iOS App (通过App Store发布)
- Android App (通过Google Play发布)

#### 方式2: 移动浏览器
- Safari (iOS)
- Chrome (Android)
- 通过URL直接访问

**核心功能**:

1. **资产浏览**
   - 自选列表
   - 股票/基金详情
   - 实时行情(有延时)

2. **AI分析**
   - 一键分析
   - 查看分析结果
   - 历史分析记录

3. **数据补充**
   - 上传截图
   - 手动输入数据

4. **个人设置**
   - 颜色约定(中国/美国)
   - 默认模型选择
   - 通知设置

**界面特点**:
- 响应式设计
- 手势操作
- 离线缓存
- 推送通知(App版本)

---

## 三、应用商店发布路线图

### 3.1 iOS App Store 发布

**准备工作**:

1. **Apple Developer账号**
   - 个人账号: $99/年
   - 企业账号: $299/年

2. **应用配置**
   - Bundle ID: `com.airisk.app`
   - App名称: "笨AI投资助手"
   - 版本号: 1.0.0

3. **必需资产**
   - App图标 (1024x1024)
   - 启动屏幕
   - 截图 (多种尺寸)
   - 隐私政策URL
   - 应用描述

**发布步骤**:

```bash
# 1. 构建生产版本
npm run build

# 2. 同步到iOS
npx cap sync ios

# 3. 在Xcode中配置
# - 设置Bundle ID
# - 配置签名证书
# - 设置版本号

# 4. 归档并上传
# Product > Archive
# Distribute App > App Store Connect

# 5. 在App Store Connect中提交审核
```

**审核要点**:
- ✅ 应用功能完整
- ✅ 无崩溃和重大bug
- ✅ 遵守App Store审核指南
- ✅ 提供测试账号(如需要)
- ✅ 隐私政策完整

**预计时间**: 首次审核 1-2周

---

### 3.2 Google Play 发布

**准备工作**:

1. **Google Play开发者账号**
   - 一次性费用: $25

2. **应用配置**
   - Package名: `com.airisk.app`
   - 版本号: 1.0.0

3. **必需资产**
   - 应用图标
   - 特色图片
   - 截图
   - 隐私政策

**发布步骤**:

```bash
# 1. 添加Android平台
npx cap add android

# 2. 构建生产版本
npm run build
npx cap sync android

# 3. 在Android Studio中
# - 生成签名密钥
# - 构建Release APK/AAB
# Build > Generate Signed Bundle/APK

# 4. 上传到Google Play Console
```

**审核要点**:
- ✅ 应用符合政策
- ✅ 提供隐私政策
- ✅ 内容分级
- ✅ 目标受众设置

**预计时间**: 首次审核 1-3天

---

### 3.3 发布前检查清单

**技术准备**:
- [ ] 后端已部署到云服务器
- [ ] 数据库已配置(PostgreSQL)
- [ ] API已测试通过
- [ ] 移动端已完整测试
- [ ] 性能优化完成
- [ ] 错误处理完善

**内容准备**:
- [ ] App图标设计完成
- [ ] 应用截图准备完成
- [ ] 应用描述撰写完成
- [ ] 隐私政策页面创建
- [ ] 用户协议准备完成

**法律准备**:
- [ ] 隐私政策合规
- [ ] 数据使用说明
- [ ] 免责声明
- [ ] 金融信息披露

---

## 四、开发优先级

### 阶段1: MVP (最小可行产品) - 1-2个月

**目标**: 实现核心功能,本地部署

- [x] 前端基础UI (已完成)
- [x] 后端基础API (已完成)
- [ ] AI分析引擎(规则版本)
- [ ] 移动端优化
- [ ] 本地部署测试

**里程碑**: 可以在本地运行并进行基础分析

---

### 阶段2: Beta版本 - 2-3个月

**目标**: 完善功能,云端部署

- [ ] 后端云端部署
- [ ] PC管理端开发
- [ ] 图片OCR功能
- [ ] 用户认证系统
- [ ] 数据备份机制

**里程碑**: 可以通过互联网访问,支持多用户

---

### 阶段3: 正式版本 - 3-4个月

**目标**: 应用商店发布

- [ ] 完整测试(功能、性能、安全)
- [ ] 应用商店资产准备
- [ ] 隐私政策和法律文档
- [ ] iOS App提交审核
- [ ] Android App提交审核

**里程碑**: 在App Store和Google Play上线

---

### 阶段4: 持续迭代

**目标**: 优化和扩展

- [ ] AI模型优化
- [ ] 更多数据源
- [ ] 社区功能
- [ ] 付费功能(可选)

---

## 五、技术架构细节

### 5.1 认证与授权

**方案**: JWT (JSON Web Token)

```python
# backend/auth.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
import jwt

security = HTTPBearer()

def verify_token(credentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

def verify_admin(payload = Depends(verify_token)):
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return payload
```

**用户角色**:
- `user`: 普通用户(移动端)
- `admin`: 管理员(PC端)

---

### 5.2 数据库迁移方案

**从SQLite迁移到PostgreSQL**:

```python
# database.py
import os
from sqlmodel import create_engine

# 根据环境变量选择数据库
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./database.db"  # 默认本地SQLite
)

# 生产环境使用PostgreSQL
# DATABASE_URL = "postgresql://user:password@host:5432/dbname"

engine = create_engine(DATABASE_URL)
```

---

### 5.3 环境配置

**开发环境** (.env.development):
```env
DATABASE_URL=sqlite:///./database.db
API_BASE_URL=http://localhost:8000
ENVIRONMENT=development
```

**生产环境** (.env.production):
```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
API_BASE_URL=https://api.airisk.com
ENVIRONMENT=production
SECRET_KEY=your-secret-key
```

---

## 六、成本估算

### 6.1 开发成本

- **开发时间**: 4-6个月(全职)
- **开发者账号**: 
  - Apple: $99/年
  - Google: $25(一次性)

### 6.2 运营成本(月度)

**小规模(< 1000用户)**:
- 云服务器: $20-30
- 数据库: $10-20
- 存储: $5-10
- **总计**: ~$35-60/月

**中等规模(1000-10000用户)**:
- 云服务器: $50-100
- 数据库: $30-50
- 存储: $20-30
- CDN: $10-20
- **总计**: ~$110-200/月

---

## 七、风险与挑战

### 7.1 技术风险

- **数据准确性**: 免费数据源可能有延时或错误
- **AI模型质量**: 需要持续优化和验证
- **性能瓶颈**: 大量用户时的并发处理

**应对措施**:
- 多数据源验证
- 模型A/B测试
- 缓存和负载均衡

### 7.2 合规风险

- **金融监管**: 投资建议可能需要牌照
- **数据隐私**: GDPR、个人信息保护法
- **应用商店政策**: 金融类App审核严格

**应对措施**:
- 添加免责声明
- 明确"仅供参考"
- 咨询法律顾问

---

## 八、总结

本系统采用灵活的架构设计,支持:
- ✅ 本地和云端双模式部署
- ✅ PC管理端和移动端双端支持
- ✅ 应用商店发布路径清晰
- ✅ 可扩展的模块化设计

**下一步行动**:
1. 完成AI分析引擎开发
2. 开发PC管理端界面
3. 准备云端部署环境
4. 准备应用商店发布资产
