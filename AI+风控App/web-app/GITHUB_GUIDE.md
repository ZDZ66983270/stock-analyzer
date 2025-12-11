# GitHub 代码托管指南

## 一、准备工作

### 1.1 检查Git是否已安装

```bash
git --version
```

如果未安装,请访问 https://git-scm.com/ 下载安装。

### 1.2 配置Git用户信息

```bash
# 设置用户名和邮箱(首次使用)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# 查看配置
git config --list
```

### 1.3 创建GitHub账号

如果还没有GitHub账号,访问 https://github.com 注册。

---

## 二、创建GitHub仓库

### 方法1: 在GitHub网站创建(推荐)

1. 登录GitHub
2. 点击右上角 "+" → "New repository"
3. 填写仓库信息:
   - **Repository name**: `ai-risk-app` (或其他名称)
   - **Description**: "AI投资风险评价应用"
   - **Visibility**: 
     - ✅ Private (私有,推荐) - 代码仅自己可见
     - ⬜ Public (公开) - 任何人可见
   - ⬜ 不勾选 "Initialize this repository with a README" (因为本地已有代码)
4. 点击 "Create repository"

---

## 三、将本地代码推送到GitHub

### 3.1 初始化本地Git仓库

```bash
# 进入项目目录
cd "/Users/zhangzy/My Docs/Privates/22-AI编程/AI+风控App/web-app"

# 初始化Git仓库(如果还没有)
git init

# 查看状态
git status
```

### 3.2 创建.gitignore文件

在推送代码前,需要排除一些不应该上传的文件:

```bash
# 创建.gitignore文件
cat > .gitignore << 'EOF'
# 依赖包
node_modules/
__pycache__/
*.pyc
*.pyo
*.pyd

# 环境变量
.env
.env.local
.env.production
.env.development

# 数据库文件
*.db
*.sqlite
*.sqlite3
database.db

# 日志文件
logs/
*.log
logs_V4/

# 输出文件
output_V4/
dist/
build/

# IDE配置
.vscode/
.idea/
*.swp
*.swo
*~

# macOS
.DS_Store
.AppleDouble
.LSOverride

# Windows
Thumbs.db
ehthumbs.db
Desktop.ini

# 临时文件
*.tmp
*.temp

# Electron
out/

# iOS
ios/App/Pods/
ios/App/App.xcworkspace/xcuserdata/
*.xcuserstate

# Android
android/.gradle/
android/build/
android/app/build/

# 敏感信息(如果有)
secrets/
*.key
*.pem
EOF
```

### 3.3 添加文件到Git

```bash
# 添加所有文件
git add .

# 查看将要提交的文件
git status

# 如果发现不应该添加的文件,可以移除
# git reset HEAD <file>
```

### 3.4 创建首次提交

```bash
# 提交代码
git commit -m "Initial commit: AI投资风险评价应用"
```

### 3.5 关联远程仓库

```bash
# 添加远程仓库(替换为你的GitHub用户名和仓库名)
git remote add origin https://github.com/YOUR_USERNAME/ai-risk-app.git

# 查看远程仓库
git remote -v
```

### 3.6 推送代码到GitHub

```bash
# 推送到main分支(首次推送)
git push -u origin main

# 如果提示分支名是master,使用:
# git branch -M main
# git push -u origin main
```

**首次推送可能需要输入GitHub用户名和密码**

---

## 四、使用Personal Access Token (推荐)

GitHub已不再支持密码认证,需要使用Personal Access Token:

### 4.1 创建Token

1. 登录GitHub
2. 点击右上角头像 → Settings
3. 左侧菜单最下方 → Developer settings
4. Personal access tokens → Tokens (classic)
5. Generate new token (classic)
6. 设置:
   - **Note**: "AI Risk App"
   - **Expiration**: 90 days (或自定义)
   - **Scopes**: 勾选 `repo` (完整仓库访问权限)
7. 点击 "Generate token"
8. **重要**: 复制生成的token(只显示一次!)

### 4.2 使用Token推送

```bash
# 推送时,用户名输入GitHub用户名,密码输入token
git push -u origin main
```

### 4.3 保存凭据(可选)

```bash
# macOS使用Keychain保存
git config --global credential.helper osxkeychain

# 下次推送时输入一次token,之后会自动保存
```

---

## 五、日常使用

### 5.1 查看状态

```bash
# 查看修改的文件
git status

# 查看具体修改内容
git diff
```

### 5.2 提交更改

```bash
# 添加修改的文件
git add .

# 或添加特定文件
git add src/components/FundDetailView.jsx

# 提交
git commit -m "feat: 添加基金详情页重构功能"

# 推送到GitHub
git push
```

### 5.3 提交信息规范(推荐)

使用语义化的提交信息:

```bash
# 新功能
git commit -m "feat: 添加AI分析引擎"

# 修复bug
git commit -m "fix: 修复基金数据获取错误"

# 文档更新
git commit -m "docs: 更新README和架构文档"

# 样式调整
git commit -m "style: 优化移动端UI布局"

# 重构
git commit -m "refactor: 重构数据获取模块"

# 性能优化
git commit -m "perf: 优化数据库查询性能"

# 测试
git commit -m "test: 添加单元测试"
```

### 5.4 查看历史

```bash
# 查看提交历史
git log

# 简洁查看
git log --oneline

# 查看最近5条
git log -5
```

---

## 六、分支管理(可选,但推荐)

### 6.1 创建开发分支

```bash
# 创建并切换到开发分支
git checkout -b develop

# 推送开发分支到GitHub
git push -u origin develop
```

### 6.2 功能分支工作流

```bash
# 创建功能分支
git checkout -b feature/ai-analysis-engine

# 开发完成后提交
git add .
git commit -m "feat: 实现AI分析引擎"

# 推送到GitHub
git push -u origin feature/ai-analysis-engine

# 在GitHub上创建Pull Request合并到develop
```

### 6.3 合并分支

```bash
# 切换到主分支
git checkout main

# 合并开发分支
git merge develop

# 推送
git push
```

---

## 七、从GitHub拉取代码(在其他电脑)

### 7.1 克隆仓库

```bash
# 克隆到本地
git clone https://github.com/YOUR_USERNAME/ai-risk-app.git

# 进入目录
cd ai-risk-app

# 安装依赖
npm install
cd backend && pip install -r requirements.txt
```

### 7.2 拉取最新代码

```bash
# 拉取最新代码
git pull

# 或指定分支
git pull origin main
```

---

## 八、常见问题

### Q1: 推送时提示"Permission denied"

**解决**: 检查Personal Access Token是否正确,或使用SSH密钥

### Q2: 如何撤销最后一次提交?

```bash
# 撤销提交但保留修改
git reset --soft HEAD~1

# 撤销提交并丢弃修改(危险!)
git reset --hard HEAD~1
```

### Q3: 如何忽略已经提交的文件?

```bash
# 从Git中移除但保留本地文件
git rm --cached database.db

# 添加到.gitignore
echo "database.db" >> .gitignore

# 提交
git commit -m "chore: 移除数据库文件"
```

### Q4: 如何查看远程仓库地址?

```bash
git remote -v
```

### Q5: 如何修改远程仓库地址?

```bash
git remote set-url origin https://github.com/NEW_USERNAME/new-repo.git
```

---

## 九、最佳实践

### 9.1 提交频率

- ✅ 经常提交,每个功能点一次提交
- ✅ 每天至少推送一次到GitHub
- ❌ 不要积累太多修改才提交

### 9.2 .gitignore规则

- ✅ 排除依赖包(node_modules, __pycache__)
- ✅ 排除数据库文件
- ✅ 排除环境变量文件(.env)
- ✅ 排除日志和临时文件

### 9.3 敏感信息

- ❌ 绝对不要提交API密钥、密码等敏感信息
- ✅ 使用环境变量(.env)存储敏感信息
- ✅ 确保.env在.gitignore中

### 9.4 README.md

- ✅ 保持README更新
- ✅ 包含项目说明、安装步骤、使用方法
- ✅ 添加截图和演示

---

## 十、快速命令参考

```bash
# 初始化
git init
git remote add origin <url>

# 日常工作流
git status                    # 查看状态
git add .                     # 添加所有修改
git commit -m "message"       # 提交
git push                      # 推送到GitHub

# 拉取更新
git pull                      # 拉取最新代码

# 分支操作
git branch                    # 查看分支
git checkout -b <branch>      # 创建并切换分支
git merge <branch>            # 合并分支

# 查看历史
git log                       # 查看提交历史
git diff                      # 查看修改内容
```

---

## 十一、下一步

1. ✅ 创建GitHub仓库
2. ✅ 配置.gitignore
3. ✅ 推送代码到GitHub
4. ✅ 定期提交和推送
5. ✅ 考虑使用分支管理
6. ✅ 添加README和文档

现在您的代码就安全地备份在GitHub上了! 🎉
