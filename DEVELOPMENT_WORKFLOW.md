# 开发和部署工作流程规范

**项目**: TOP_N 推广平台
**制定日期**: 2025-12-15
**适用范围**: 所有代码修改和功能开发

---

## 📋 核心原则

1. ✅ **所有修改必须在本地完成**
2. ✅ **Git 是唯一的代码真实来源**
3. ✅ **部署前必须提交到 Git**
4. ✅ **部署后必须验证功能**
5. ❌ **永远不要直接在服务器上修改代码**

---

## 🔄 标准工作流程

### 日常开发流程

```bash
# 1. 开始工作前，确保代码是最新的
git pull origin main

# 2. 在本地修改代码
# （使用 VS Code、Claude Code 等工具）

# 3. 本地测试
# - 如果是前端，在浏览器中测试
# - 如果是后端，运行本地服务测试

# 4. 检查修改的文件
git status

# 5. 添加修改到暂存区
git add <file1> <file2> ...
# 或添加所有修改
git add .

# 6. 提交修改（写清楚提交信息）
git commit -m "描述你做了什么修改"

# 7. 推送到远程仓库（可选，但推荐）
git push origin main

# 8. 部署到服务器
./deploy.sh  # 使用部署脚本
# 或手动部署：
scp <files> u_topn@39.105.12.124:/home/u_topn/TOP_N/<path>

# 9. 验证部署
curl http://39.105.12.124/<页面路径>
# 或在浏览器中访问测试
```

---

## 📝 提交信息规范

### 好的提交信息示例

```bash
✅ git commit -m "Add AI model selector to analysis page"
✅ git commit -m "Fix user logout session clearing issue"
✅ git commit -m "Update homepage background image"
✅ git commit -m "Refactor prompt template API for better error handling"
```

### 避免的提交信息

```bash
❌ git commit -m "fix"
❌ git commit -m "update"
❌ git commit -m "修改"
❌ git commit -m "111"
```

### 提交信息格式建议

```
<动词> <具体内容>

动词选择：
- Add: 新增功能
- Fix: 修复 bug
- Update: 更新功能
- Refactor: 重构代码
- Remove: 删除功能
- Optimize: 性能优化
- Document: 文档更新
```

---

## 🚀 部署检查清单

### 部署前检查

```bash
# 1. 确认所有修改已提交
git status
# 应该显示：nothing to commit, working tree clean

# 2. 检查关键文件是否一致
# 如果修改了 HTML，检查对应的 JS/CSS
# 如果修改了 API，检查前端调用代码

# 3. 确认没有语法错误
# Python 后端：
python -m py_compile backend/<文件>.py

# JavaScript 前端：
# 在浏览器控制台查看是否有错误
```

### 部署文件映射

| 本地路径 | 服务器路径 |
|---------|-----------|
| `templates/*.html` | `/home/u_topn/TOP_N/templates/` |
| `static/*.js` | `/home/u_topn/TOP_N/static/` |
| `static/*.css` | `/home/u_topn/TOP_N/static/` |
| `backend/**/*.py` | `/home/u_topn/TOP_N/backend/` |

### 常用部署命令

```bash
# 上传单个文件
scp <本地文件> u_topn@39.105.12.124:/home/u_topn/TOP_N/<路径>

# 上传多个文件
scp file1 file2 file3 u_topn@39.105.12.124:/home/u_topn/TOP_N/<路径>

# 上传整个目录
scp -r <目录> u_topn@39.105.12.124:/home/u_topn/TOP_N/<路径>

# 重启服务（如果修改了 Python 后端）
ssh u_topn@39.105.12.124 "killall -9 gunicorn && cd /home/u_topn/TOP_N && ./start_service.sh"
```

### 部署后验证

```bash
# 1. 检查页面是否可访问
curl -I http://39.105.12.124/<页面路径>
# 应该返回 200 OK

# 2. 检查服务是否运行（如果是后端修改）
ssh u_topn@39.105.12.124 "ps aux | grep gunicorn"

# 3. 在浏览器中实际测试功能
# - 打开开发者工具（F12）
# - 查看 Console 是否有错误
# - 测试修改的功能是否正常
# - 清除缓存后再测试一次
```

---

## 🔧 常见场景处理

### 场景 1: 修改页面样式

```bash
# 1. 修改本地文件
编辑 templates/xxx.html 或 static/xxx.css

# 2. 在本地浏览器测试（如果可以）
# 或直接部署测试

# 3. 提交
git add templates/xxx.html static/xxx.css
git commit -m "Update page layout and styling"

# 4. 部署
scp templates/xxx.html u_topn@39.105.12.124:/home/u_topn/TOP_N/templates/
scp static/xxx.css u_topn@39.105.12.124:/home/u_topn/TOP_N/static/

# 5. 清除浏览器缓存后验证
```

### 场景 2: 修改 JavaScript 功能

```bash
# 1. 修改本地 JS 文件
编辑 static/xxx.js

# 2. 在浏览器控制台测试代码逻辑

# 3. 提交
git add static/xxx.js
git commit -m "Add new feature to xxx.js"

# 4. 部署
scp static/xxx.js u_topn@39.105.12.124:/home/u_topn/TOP_N/static/

# 5. 验证
# - 清除浏览器缓存（Ctrl+Shift+Delete）
# - 强制刷新页面（Ctrl+F5）
# - 打开控制台查看是否有错误
```

### 场景 3: 修改 Python 后端

```bash
# 1. 修改本地文件
编辑 backend/xxx.py

# 2. 检查语法
python -m py_compile backend/xxx.py

# 3. 提交
git add backend/xxx.py
git commit -m "Fix API endpoint response format"

# 4. 部署
scp backend/xxx.py u_topn@39.105.12.124:/home/u_topn/TOP_N/backend/

# 5. 重启服务
ssh u_topn@39.105.12.124 "killall -9 gunicorn && cd /home/u_topn/TOP_N && ./start_service.sh"

# 6. 验证
curl http://39.105.12.124/api/xxx
```

### 场景 4: 添加新功能（涉及多个文件）

```bash
# 例如：添加新的 API 接口

# 1. 修改相关文件
# - backend/blueprints/xxx.py (后端接口)
# - static/xxx.js (前端调用)
# - templates/xxx.html (页面展示，如果需要)

# 2. 测试所有相关功能

# 3. 一起提交（保持原子性）
git add backend/blueprints/xxx.py static/xxx.js templates/xxx.html
git commit -m "Add new API endpoint and frontend integration for xxx feature"

# 4. 部署所有相关文件
scp backend/blueprints/xxx.py u_topn@39.105.12.124:/home/u_topn/TOP_N/backend/blueprints/
scp static/xxx.js u_topn@39.105.12.124:/home/u_topn/TOP_N/static/
scp templates/xxx.html u_topn@39.105.12.124:/home/u_topn/TOP_N/templates/

# 5. 重启服务并验证
```

---

## 🆘 紧急情况处理

### 如果必须在服务器上临时修复

**原则**: 极力避免，但如果确实必须：

```bash
# 1. 在服务器上修复
ssh u_topn@39.105.12.124
vi /home/u_topn/TOP_N/<文件路径>

# 2. 立即记录
echo "$(date): 在服务器上修改了 <文件> - <原因>" >> ~/urgent_fixes.log

# 3. 立即备份服务器版本
scp u_topn@39.105.12.124:/home/u_topn/TOP_N/<文件> ./backup_from_server_<日期>.backup

# 4. 同步到本地（必须在24小时内完成）
scp u_topn@39.105.12.124:/home/u_topn/TOP_N/<文件> ./<本地路径>

# 5. 提交到 Git
git add <文件>
git commit -m "Sync urgent fix from server: <描述修复内容>"

# 6. 删除服务器上的临时备份
```

### 如果发现本地和服务器不一致

```bash
# 1. 下载服务器版本对比
scp u_topn@39.105.12.124:/home/u_topn/TOP_N/<文件> /tmp/server_version

# 2. 对比差异
diff -u <本地文件> /tmp/server_version

# 3. 决定保留哪个版本
# - 如果服务器版本更新：同步到本地并提交
# - 如果本地版本更新：部署到服务器
# - 如果都有修改：手动合并

# 4. 同步并提交
git add <文件>
git commit -m "Sync file from server/local with <描述>"
```

---

## 🛠️ 实用工具脚本

### 快速部署脚本

创建 `quick_deploy.sh`:

```bash
#!/bin/bash
# 快速部署指定文件

if [ $# -eq 0 ]; then
    echo "用法: ./quick_deploy.sh <文件路径>"
    echo "示例: ./quick_deploy.sh templates/index.html"
    exit 1
fi

FILE=$1
SERVER="u_topn@39.105.12.124"
REMOTE_PATH="/home/u_topn/TOP_N"

echo "部署 $FILE 到服务器..."

# 检查文件是否存在
if [ ! -f "$FILE" ]; then
    echo "错误: 文件不存在 - $FILE"
    exit 1
fi

# 检查是否已提交到 Git
if git status --porcelain | grep -q "$FILE"; then
    echo "警告: 文件未提交到 Git"
    read -p "是否继续部署? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 上传文件
scp "$FILE" "$SERVER:$REMOTE_PATH/$FILE"

echo "✓ 部署完成"
echo "验证: http://39.105.12.124/$(basename $FILE .html)"
```

使用方法：
```bash
chmod +x quick_deploy.sh
./quick_deploy.sh templates/index.html
```

### 文件同步检查脚本

创建 `check_sync.sh`:

```bash
#!/bin/bash
# 检查本地和服务器文件是否一致

SERVER="u_topn@39.105.12.124"
REMOTE_PATH="/home/u_topn/TOP_N"

FILES=(
    "templates/index.html"
    "templates/analysis.html"
    "templates/admin_dashboard.html"
    "static/analysis.js"
    "static/input.js"
    "backend/app_factory.py"
)

echo "检查文件同步状态..."
echo "========================"

for file in "${FILES[@]}"; do
    echo -n "检查 $file ... "

    # 下载服务器版本
    scp -q "$SERVER:$REMOTE_PATH/$file" "/tmp/server_$(basename $file)" 2>/dev/null

    if [ $? -ne 0 ]; then
        echo "❌ 服务器文件不存在"
        continue
    fi

    # 对比
    if diff -q "$file" "/tmp/server_$(basename $file)" > /dev/null 2>&1; then
        echo "✓ 一致"
    else
        echo "⚠️  不一致！"
        echo "  运行以下命令查看差异:"
        echo "  diff -u $file /tmp/server_$(basename $file)"
    fi

    rm "/tmp/server_$(basename $file)"
done

echo "========================"
echo "检查完成"
```

使用方法：
```bash
chmod +x check_sync.sh
./check_sync.sh
```

---

## 📚 参考文档

- [ISSUE_REPORT_AI_MODEL_LOADING.md](./ISSUE_REPORT_AI_MODEL_LOADING.md) - AI 模型加载问题分析
- [CODE_SYNC_ISSUE_ROOT_CAUSE.md](./CODE_SYNC_ISSUE_ROOT_CAUSE.md) - 代码不同步问题根因
- [BACKUP_README_20251215.md](./BACKUP_README_20251215.md) - 备份说明文档

---

## ✅ 日常检查清单

### 每天开始工作前

- [ ] `git pull` 获取最新代码
- [ ] 检查是否有未提交的修改 `git status`
- [ ] 查看最近的提交记录 `git log -5 --oneline`

### 每次修改后

- [ ] 本地测试功能
- [ ] 提交到 Git
- [ ] 部署到服务器
- [ ] 验证功能正常

### 每周维护

- [ ] 运行 `check_sync.sh` 检查文件一致性
- [ ] 清理不需要的备份文件
- [ ] 检查服务器日志是否有错误
- [ ] 更新文档（如果有新功能）

---

## 🚫 禁止操作

1. ❌ 直接在服务器上用 vi/nano 编辑代码文件
2. ❌ 在服务器上测试完不同步到 Git
3. ❌ 跳过 Git 提交直接部署
4. ❌ 部署后不验证功能
5. ❌ 写无意义的提交信息
6. ❌ 提交包含敏感信息的文件（密码、密钥等）

---

## 💡 最佳实践

1. ✅ 频繁提交，每个功能点提交一次
2. ✅ 提交信息清晰描述做了什么
3. ✅ 部署前检查 Git 状态
4. ✅ 部署后立即验证
5. ✅ 遇到问题先查日志
6. ✅ 重要修改前先备份
7. ✅ 定期运行同步检查

---

**记住**: 规范的工作流程虽然看起来繁琐，但能避免99%的问题，节省大量调试时间！

**最后更新**: 2025-12-15
