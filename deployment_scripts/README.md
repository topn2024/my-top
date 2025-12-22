# TOP_N 生产环境部署脚本

## 概述

这些脚本用于将 TOP_N 从单体 `app_with_upload.py` 架构迁移到模块化 `app_factory.py` 蓝图架构。

## 脚本列表

### 1. backup_before_deploy.sh
**用途**: 在部署前创建完整备份
**执行位置**: 服务器端
**包含内容**:
- 后端代码 (backend/)
- 数据库 (topn.db)
- systemd配置
- Gunicorn配置
- 服务状态快照

### 2. deploy_to_production.sh
**用途**: 执行生产环境部署
**执行位置**: 本地（会SSH到服务器）
**执行步骤**:
1. 创建备份
2. 上传修复的文件 (api.py, models.py, config.py, app_factory.py, app.py)
3. 创建生产环境 .env 文件
4. 更新 systemd 配置 (app_with_upload:app → app:app)
5. 重启服务
6. 健康检查
7. 路由验证

**关键变更**:
- URL前缀修复 (移除6个路由的重复 /api/)
- 模型导入完整 (15个数据库表)
- 配置管理统一 (.env支持)
- 服务入口切换 (app:app)

### 3. rollback_deployment.sh
**用途**: 快速回滚到部署前状态
**执行位置**: 本地（会SSH到服务器）
**回滚速度**: < 5分钟
**恢复内容**: 代码、数据库、配置

### 4. verify_production.sh
**用途**: 验证部署后功能
**执行位置**: 本地（会SSH到服务器）
**验证项**:
- 服务状态
- 进程检查
- 健康检查
- 6个修复路由
- 数据库表
- 错误日志

## 使用方法

### 准备阶段

1. 确保脚本有执行权限:
```bash
cd D:/code/TOP_N/deployment_scripts
chmod +x *.sh
```

2. 确认SSH连接正常:
```bash
ssh u_topn@39.105.12.124 "echo '连接成功'"
```

### 执行部署

#### Step 1: 上传备份脚本到服务器
```bash
scp backup_before_deploy.sh u_topn@39.105.12.124:~/
```

#### Step 2: 执行部署
```bash
bash deploy_to_production.sh
```

部署过程中会：
- 要求确认 (输入 `yes`)
- 显示备份ID（请记录！）
- 自动执行所有步骤
- 如失败会自动回滚

#### Step 3: 验证部署
```bash
bash verify_production.sh
```

### 如需回滚

如果部署后发现问题：

```bash
# 使用部署时记录的备份ID
bash rollback_deployment.sh <BACKUP_ID>

# 例如：
# bash rollback_deployment.sh 20251222_230000
```

## 部署时机建议

**最佳时机**: 低流量时段（凌晨 2:00-4:00）

**原因**:
- 需要重启服务（短暂中断）
- 便于发现问题
- 减少对用户影响

## 预期停机时间

- **正常部署**: 15-30秒（服务重启）
- **如需回滚**: < 5分钟

## 部署检查清单

### 部署前
- [ ] 本地验证已通过 (Phase 2)
- [ ] 代码已推送到Git远程仓库
- [ ] 备份脚本已上传到服务器
- [ ] 确认有服务器sudo权限
- [ ] 选择低流量时段

### 部署中
- [ ] 记录备份ID
- [ ] 观察部署输出
- [ ] 确认健康检查通过
- [ ] 确认路由验证通过

### 部署后
- [ ] 执行 verify_production.sh
- [ ] 测试关键功能
- [ ] 监控错误日志（至少30分钟）
- [ ] 检查用户反馈

## 架构变更总结

| 项目 | 部署前 | 部署后 |
|-----|--------|--------|
| 入口文件 | app_with_upload.py | app.py (使用 app_factory) |
| systemd配置 | app_with_upload:app | app:app |
| URL前缀 | 6个路由有 /api/api/ 错误 | 已修复为 /api/ |
| 数据库表 | 13个 | 15个 |
| 配置管理 | 硬编码 | .env 环境变量 |
| 架构 | 单体 (1,740行) | 蓝图模块化 |

## 关键文件变更

1. **backend/blueprints/api.py** (Line 398, 523, 1069, 1128, 1190, 1322)
   - 移除重复的 `/api` 前缀

2. **backend/models.py** (Line 622)
   - 添加 models_prompt_template 导入

3. **backend/config.py** (Line 7)
   - 添加 .env 文件加载支持

4. **backend/app_factory.py** (Line 211-214)
   - 从环境变量读取配置

5. **backend/app.py** (Line 8-10)
   - 从环境变量读取配置

6. **backend/.env** (新增)
   - 生产环境配置

## 验证标准

部署成功的标准：
- ✅ 服务状态: active (running)
- ✅ 健康检查: {"status": "ok"}
- ✅ 6个修复路由返回 401/400/405 (而非404)
- ✅ 数据库表: 15个
- ✅ 错误日志: < 5个/100行
- ✅ 关键功能正常

## 监控建议

部署后48小时内，建议每4小时检查：

```bash
# 服务状态
ssh u_topn@39.105.12.124 "sudo systemctl status topn.service"

# 错误日志
ssh u_topn@39.105.12.124 "tail -100 /home/u_topn/TOP_N/logs/gunicorn_error.log | grep -i error | wc -l"

# 健康检查
ssh u_topn@39.105.12.124 "curl -s http://localhost:8080/api/health"
```

## 紧急联系

如果遇到无法解决的问题：
1. 立即执行回滚: `bash rollback_deployment.sh <BACKUP_ID>`
2. 检查服务日志
3. 联系技术团队

## 备份保留策略

- 部署备份: 保留30天
- 建议定期检查备份目录大小: `/home/u_topn/TOP_N/backups/`

## 附录：关键命令速查

```bash
# 查看服务状态
ssh u_topn@39.105.12.124 "sudo systemctl status topn.service"

# 重启服务
ssh u_topn@39.105.12.124 "sudo systemctl restart topn.service"

# 查看日志
ssh u_topn@39.105.12.124 "tail -f /home/u_topn/TOP_N/logs/gunicorn_error.log"

# 健康检查
ssh u_topn@39.105.12.124 "curl http://localhost:8080/api/health"

# 列出备份
ssh u_topn@39.105.12.124 "ls -lt /home/u_topn/TOP_N/backups/"
```
