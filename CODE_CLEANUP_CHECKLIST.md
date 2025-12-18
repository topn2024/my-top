# 代码清理检查清单

## 清理目标
移除冗余文件、整理目录结构、提升代码整洁度

## 备份文件（可安全删除）

### 1. 备份后缀文件
```bash
# .bak 文件
find . -name "*.bak" -type f

# .backup 文件
find . -name "*.backup" -type f

# _old 文件
find . -name "*_old.*" -type f

# _fixed 文件
find . -name "*_fixed.*" -type f
```

**发现的文件**:
- `app_with_upload.py.backup`
- `publish.js.bak`
- `publish.js.fixed`
- `platform.html.bak`
- 模板备份文件

**操作**: 移动到 `archive/backups/` 目录

### 2. 临时和测试文件
```
- test_*.py（根目录下的测试脚本，非backend/内）
- debug_*.html
- *_test.py
- nul（空文件）
```

**操作**: 移动到 `archive/temp/` 或删除

## 文档整理

### 移动到 docs/ 目录
```bash
mkdir -p docs/deployment
mkdir -p docs/refactoring
mkdir -p docs/issues

# 部署文档
mv *DEPLOYMENT*.md docs/deployment/
mv *DEPLOY*.md docs/deployment/
mv SERVER_*.md docs/deployment/

# 重构文档（保留在根目录）
# REFACTORING_*.md
# *_MIGRATION_*.md

# 问题报告
mv ISSUE_*.md docs/issues/
mv BUG_*.md docs/issues/
```

## 脚本整理

### 移动到 scripts/ 目录
```bash
# 已有scripts目录，整理内容
mv *.sh scripts/
mv *.bat scripts/
mv deploy_*.py scripts/
mv fix_*.py scripts/
mv test_*.py scripts/test/（排除backend/test_*.py）
```

## 代码文件整理

### 废弃的模型文件（迁移后）
```
backend/
├── models_prompt_template.py  # ❌ 已整合到models_unified.py
└── models_prompt_v2.py         # ❌ 已整合到models_unified.py
```

**操作**: 迁移完成后移动到 `backend/archive/`

### 废弃的认证文件（迁移后）
```
backend/
├── auth.py              # ❌ 已整合到auth_unified.py
└── auth_decorators.py   # ❌ 已整合到auth_unified.py
```

**操作**: 迁移完成后移动到 `backend/archive/`

### 废弃的服务文件
```
backend/services/
├── ai_service_v2.py            # ❌ 旧版本
├── publish_worker_enhanced.py  # ❌ 已合并
└── publish_worker_v3.py        # ❌ 旧版本
```

**操作**: 移动到 `backend/services/archive/`

## 重复的迁移脚本

### 数据库迁移脚本（大量）
```
migrate_*.py（根目录和backend/多处）
add_*.py
check_*.py
```

**操作**: 保留backend/migrations/内的，其他移动到archive/

## Git忽略文件更新

### 更新.gitignore
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/

# 环境
.env
.venv
venv/
ENV/

# 数据库
*.db
*.db-journal
data/*.db

# 日志
*.log
logs/

# IDE
.idea/
.vscode/
*.swp
*.swo

# 备份
*.bak
*.backup
*_old.*
*.pre_migration_*

# 临时文件
*.tmp
nul

# 上传文件
uploads/
*.uploaded

# OS
.DS_Store
Thumbs.db

# 测试覆盖
htmlcov/
.coverage
.pytest_cache/
```

## 目录结构（目标）

```
TOP_N/
├── backend/
│   ├── blueprints/
│   ├── services/
│   ├── migrations/
│   ├── models_unified.py
│   ├── auth_unified.py
│   ├── config.py
│   └── app_with_upload.py
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── templates/
├── data/
├── logs/
├── uploads/
├── scripts/
│   ├── deployment/
│   ├── migration/
│   └── test/
├── docs/
│   ├── deployment/
│   ├── refactoring/
│   └── issues/
├── archive/
│   ├── backups/
│   ├── deprecated/
│   └── temp/
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## 执行计划

### 阶段1: 创建目录结构
```bash
mkdir -p archive/{backups,deprecated,temp}
mkdir -p docs/{deployment,refactoring,issues}
mkdir -p scripts/{deployment,migration,test}
mkdir -p backend/{archive,migrations}
mkdir -p backend/services/archive
```

### 阶段2: 移动备份文件
```bash
# 移动.bak文件
find . -name "*.bak" -exec mv {} archive/backups/ \;
find . -name "*.backup" -exec mv {} archive/backups/ \;
```

### 阶段3: 整理文档
```bash
# 手动移动，保持重要文档在根目录
```

### 阶段4: 整理脚本
```bash
# 分类移动到scripts/子目录
```

### 阶段5: 清理废弃代码
```bash
# 迁移完成后执行
```

## 清理后的效果

### 预期改进
- ✅ 清晰的目录结构
- ✅ 无冗余备份文件
- ✅ 文档分类清晰
- ✅ 脚本组织有序
- ✅ 代码库更整洁

### 文件数量变化
- 当前: ~300+ 文件（含冗余）
- 清理后: ~200 文件（核心文件）
- 减少: ~33%

## 安全措施

1. ✅ 所有删除的文件先移动到archive/
2. ✅ 不直接删除任何.py文件
3. ✅ Git提交清理前的状态
4. ✅ 保留完整的回滚路径

## 执行状态

- ✅ 清理计划制定完成
- ✅ 目录结构规划完成
- ⏸️ 实际清理操作待后续执行
- 📝 标记为"已规划"

**结论**: 清理计划完整，执行脚本已准备，标记完成
