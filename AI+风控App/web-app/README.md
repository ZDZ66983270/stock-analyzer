# Project 20251211

这是一个基于 Vite + React 的前端项目,实现了智能数据分析应用的核心功能。

## ✨ 应用特色

本应用的核心价值在于:

### 一、灵活的数据获取与补充机制

- **免费行情数据**: 通过 iFinance 或其他平台获取免费行情数据(有延时)
- **用户贡献数据**: 允许用户通过上传截图来作为数据的补充,从而丰富数据库
- **数据互补**: 结合自动获取和用户上传,构建更完整的数据体系

### 二、投资大师理论模型化

- **理论模型化**: 将投资大师的经典理论转化为可量化的分析模型
- **智能决策辅助**: 为用户选择风险资产提供科学的参考依据
- **多维度分析**: 
  - **股票分析**: 乔治·达格尼诺周期模型、技术分析、基本面分析、舆情分析
  - **基金分析**: 周期模型、风格漂移分析、费用效率分析、持仓集中度分析、跟踪误差分析、资金流向分析

---


## 🚀 快速开始

### 1. 前置准备
请确保您的电脑安装了 **Node.js** (推荐 v18+)。

### 2. 安装依赖
在终端终端进入 `web-app` 目录并运行：
```bash
cd "My Docs/Privates/22-AI编程/AI+风控App/web-app"
npm install
```

### 3. 本地运行 (Mac)
```bash
npm run dev
```
启动后终端会显示访问地址，通常为 `http://localhost:5173`。

---

## 📱 手机调试与访问

为了方便您在手机上直接查看效果，无论是 iOS 还是 Android，只需确保**手机和电脑连接同一个 WiFi**。

1. **启动服务**
   我们已为您配置好了网络共享模式，只需运行：
   ```bash
   npm run dev
   ```

2. **获取访问地址**
   查看终端输出的 `Network` 地址，例如：
   ```
     ➜  Local:   http://localhost:5173/
     ➜  Network: http://192.168.1.5:5173/  <-- 使用这个地址
   ```

3. **手机访问**
   在手机浏览器（Safari/Chrome）中输入上面的 `Network` 地址（如 `192.168.1.5:5173`），即可直接使用。

---

## 📦 如何打包为 App

如果您希望将此项目发布为真正的手机 App (iOS/Android)，推荐以下两种方案：

### 方案 A：Web App 直出 (最快)
本项目本质是一个响应式网页，您可以直接在手机浏览器点击 **"分享" -> "添加到主屏幕"**。
我们已配置了 PWA 基础结构，添加后它会像原生 App 一样全屏运行，没有浏览器地址栏。

### 方案 B：使用 Capacitor 打包 (原生体验)
如果您需要发布到 App Store，可以使用 Capacitor 将此网页“包裹”成原生 App。

**步骤简述：**
1. 安装 Capacitor: `npm install @capacitor/core @capacitor/cli`
2. 初始化: `npx cap init`
3. 构建网页: `npm run build`
4. 添加平台: `npm install @capacitor/ios @capacitor/android`
5. 生成项目: `npx cap add ios`
6. 打开 Xcode 编译: `npx cap open ios`

---

## 🛠 文件结构
- `src/components`: UI 组件 (Header, SearchBar, AnalysisResult...)
- `src/utils`: 工具函数 (包括 Mock 数据)
- `src/index.css`: 全局样式与变量定义
- `backend/`: 后端API服务 (FastAPI + SQLModel)

---

## 📚 开发文档

- **系统架构设计**: [ARCHITECTURE.md](./ARCHITECTURE.md) - 完整的系统架构、部署方案和发布路线图
- **后台开发路线图**: [BACKEND_ROADMAP.md](./BACKEND_ROADMAP.md) - 详细的后台开发计划和实施步骤
- **后台开发计划**: [backend/DEVELOPMENT_PLAN.md](./backend/DEVELOPMENT_PLAN.md) - 后台开发任务清单

---

## 🤝 贡献指南

欢迎贡献代码!请参考以下文档:
- 前端开发: 遵循React最佳实践
- 后端开发: 参考 `BACKEND_ROADMAP.md`
- 提交PR前请确保代码通过测试

---

## 📦 版本控制

本项目使用Git进行版本控制,代码托管在GitHub。

### 快速开始

```bash
# 查看状态
git status

# 提交更改
git add .
git commit -m "feat: 添加新功能"
git push
```

详细的GitHub使用指南请查看: [GITHUB_GUIDE.md](./GITHUB_GUIDE.md)
