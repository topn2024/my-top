# 备份说明文档 - 2025-12-15

## 备份概述

**备份时间**: 2025-12-15 13:58
**备份原因**: Blueprints 架构部署和管理员权限修复完成后的稳定版本备份
**备份状态**: ✅ 完成

---

## 备份内容

### 1. 本地 Git 备份
**提交 ID**: `1704487`
**分支**: main
**提交信息**: "完成 Blueprints 架构部署和管理员权限修复"

**包含的更改**:
- 40 个文件修改
- 7699 行新增
- 212 行删除

**主要修复文件**:
- `backend/auth_decorators.py` - 增强管理员权限检查
- `backend/blueprints/auth.py` - 完整设置 session 数据
- `backend/services/ai_service_v2.py` - 修正 import 顺序
- `backend/services/analysis_prompt_service.py` - 添加容错导入
- `backend/services/article_prompt_service.py` - 添加容错导入
- `backend/app.py` - 使用 blueprints 架构

**新增文档**:
- `DEPLOYMENT_SUCCESS_REPORT.md` - 部署成功报告
- `blueprints_fix_summary.md` - 详细技术文档
- `SERVER_DEPLOYMENT_GUIDE.md` - 服务器部署指南
- `deploy_to_server.bat/.sh` - 一键部署脚本
- `test_blueprints_app.py` - Blueprints 测试脚本

### 2. 服务器代码备份
**文件名**: `TOP_N_backup_blueprints_fix_20251215_135800.tar.gz`
**位置**: `/home/u_topn/TOP_N_backup_blueprints_fix_20251215_135800.tar.gz`
**大小**: 1023 KB (1.0 MB)

**备份内容**:
- backend/ - 后端代码（所有 Python 文件）
- templates/ - 模板文件
- static/ - 静态资源
- data/ - 数据文件
- *.py - 根目录 Python 脚本
- *.sh - Shell 脚本
- *.md - 文档文件
- gunicorn_config.py - Gunicorn 配置
- requirements.txt - 依赖列表

**排除内容**:
- venv/ - 虚拟环境
- venv_new/ - 新虚拟环境
- __pycache__/ - Python 缓存
- *.pyc - 编译文件
- logs/*.log - 日志文件
- .git/ - Git 仓库

### 3. 数据库备份
**文件名**: `topn_backup_20251215_135800.db`
**位置**: `/home/u_topn/TOP_N/data/topn_backup_20251215_135800.db`
**大小**: 376 KB

**数据库内容**:
- 用户表（包含 admin 用户）
- 提示词模板
- 平台配置
- 发布历史
- 其他业务数据

---

## 恢复方法

### 本地恢复

#### 方法 1: Git 回退
```bash
# 查看提交历史
git log --oneline

# 回退到此备份版本
git reset --hard 1704487

# 或者创建新分支
git checkout -b backup-20251215 1704487
```

#### 方法 2: Git Revert
```bash
# 如果要撤销后续的某个提交
git revert <commit_id>
```

### 服务器恢复

#### 恢复代码文件
```bash
# SSH 登录服务器
ssh u_topn@39.105.12.124

# 停止服务
killall -9 gunicorn

# 备份当前版本（可选）
cd ~/TOP_N
tar -czf ~/TOP_N_backup_before_restore_$(date +%Y%m%d_%H%M%S).tar.gz .

# 解压备份文件
cd ~
tar -xzf TOP_N_backup_blueprints_fix_20251215_135800.tar.gz -C TOP_N/

# 重启服务
cd ~/TOP_N
./start_service.sh

# 验证
ps aux | grep gunicorn
curl http://localhost:8080/api/auth/login
```

#### 恢复数据库
```bash
# SSH 登录服务器
ssh u_topn@39.105.12.124

# 停止服务
killall -9 gunicorn

# 备份当前数据库
cd ~/TOP_N/data
cp topn.db topn_backup_before_restore_$(date +%Y%m%d_%H%M%S).db

# 恢复备份的数据库
cp topn_backup_20251215_135800.db topn.db

# 重启服务
cd ~/TOP_N
./start_service.sh
```

---

## 备份验证

### 服务器备份文件检查
```bash
# 检查备份文件是否存在
ssh u_topn@39.105.12.124 "ls -lh ~/TOP_N_backup_blueprints_fix_20251215_135800.tar.gz"

# 查看备份内容（不解压）
ssh u_topn@39.105.12.124 "tar -tzf ~/TOP_N_backup_blueprints_fix_20251215_135800.tar.gz | head -20"

# 验证数据库备份
ssh u_topn@39.105.12.124 "ls -lh ~/TOP_N/data/topn_backup_20251215_135800.db"
```

### Git 备份验证
```bash
# 查看提交详情
git show 1704487

# 查看修改的文件
git diff 1704487^..1704487 --stat

# 查看某个文件的变化
git diff 1704487^..1704487 backend/auth_decorators.py
```

---

## 系统状态

### 当前运行状态
- **架构**: Blueprints (模块化)
- **应用**: app:app (不是 app_with_upload:app)
- **进程**: 1 master + 6 workers
- **端口**: 8080
- **状态**: ✅ 正常运行

### 关键功能验证
- ✅ 用户登录正常
- ✅ Admin 权限检查正常
- ✅ 管理控制台可访问
- ✅ API 接口正常
- ✅ Session 持久化正常

---

## 下载备份到本地

### 下载服务器备份
```bash
# 下载代码备份
scp u_topn@39.105.12.124:~/TOP_N_backup_blueprints_fix_20251215_135800.tar.gz ./backups/

# 下载数据库备份
scp u_topn@39.105.12.124:~/TOP_N/data/topn_backup_20251215_135800.db ./backups/
```

### 解压查看
```bash
# 创建临时目录
mkdir -p backups/extracted

# 解压查看
tar -xzf backups/TOP_N_backup_blueprints_fix_20251215_135800.tar.gz -C backups/extracted/
```

---

## 备份保留策略

### 服务器备份
- **保留时间**: 建议保留 30 天
- **清理命令**:
```bash
# 查看所有备份
ssh u_topn@39.105.12.124 "ls -lh ~/TOP_N_backup_*.tar.gz"

# 删除 30 天前的备份
ssh u_topn@39.105.12.124 "find ~ -name 'TOP_N_backup_*.tar.gz' -mtime +30 -delete"
```

### Git 备份
- **保留时间**: 永久（在 Git 历史中）
- **标签建议**:
```bash
# 为重要版本打标签
git tag -a v1.0-blueprints-fix -m "Blueprints 架构修复稳定版本" 1704487
git push origin v1.0-blueprints-fix
```

---

## 重要提醒

1. **定期备份**: 建议每次重大更新后都创建备份
2. **异地备份**: 将服务器备份下载到本地保存
3. **测试恢复**: 定期测试备份恢复流程
4. **文档更新**: 每次备份后更新此文档

---

## 相关文档

- `DEPLOYMENT_SUCCESS_REPORT.md` - 本次部署报告
- `blueprints_fix_summary.md` - 技术修复文档
- `SERVER_DEPLOYMENT_GUIDE.md` - 部署指南

---

**备份创建者**: Claude Code Assistant
**备份日期**: 2025-12-15
**备份版本**: v1.0-blueprints-fix
