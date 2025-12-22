# P6: 归档清理执行计划

**前置条件**: P5 48小时监控通过
**预计执行时间**: 2025-12-24 20:10+ (监控期结束后)
**预计耗时**: 1-2小时
**风险等级**: 低

---

## 执行条件检查

在执行P6之前，必须确认以下条件：

### 必需条件

- [ ] P5 监控期已完成 (48小时)
- [ ] 累计错误率 < 0.1%
- [ ] 服务稳定运行 48+ 小时
- [ ] 无严重问题记录
- [ ] 无用户投诉
- [ ] 所有新路由正常工作

### 推荐条件

- [ ] 24小时中期评估通过
- [ ] 新路由已被实际使用
- [ ] 性能指标稳定
- [ ] 团队成员确认

**如果任何必需条件未满足，考虑延长监控期或回滚。**

---

## P6 任务清单

### 阶段1: 备份验证 (10分钟)

**目的**: 确认所有备份完整可用

```bash
# 1. 列出所有备份
ssh u_topn@39.105.12.124 "ls -lh /home/u_topn/backups/"

# 2. 验证最新备份
ssh u_topn@39.105.12.124 "tar -tzf /home/u_topn/backups/pre_cleanup_*.tar.gz | head -20"

# 3. 检查备份完整性
ssh u_topn@39.105.12.124 "gzip -t /home/u_topn/backups/pre_cleanup_*.tar.gz && echo 'Backup integrity OK'"
```

**检查点**:
- [ ] 备份文件存在
- [ ] 备份完整性验证通过
- [ ] 备份包含正确的文件

---

### 阶段2: 创建归档目录 (5分钟)

**目的**: 准备归档存储位置

```bash
ssh u_topn@39.105.12.124 << 'EOF'
# 创建归档目录
cd /home/u_topn/TOP_N
ARCHIVE_DIR="archive/migration_$(date +%Y%m%d)"
mkdir -p "$ARCHIVE_DIR"

echo "归档目录已创建: $ARCHIVE_DIR"
ls -la archive/
EOF
```

**检查点**:
- [ ] 归档目录创建成功
- [ ] 目录权限正确

---

### 阶段3: 归档遗留文件 (10分钟)

**目的**: 移动不再使用的遗留代码到归档目录

```bash
ssh u_topn@39.105.12.124 << 'EOF'
cd /home/u_topn/TOP_N/backend
ARCHIVE_DIR="../archive/migration_$(date +%Y%m%d)"

# 归档主要遗留文件
echo "归档 app_with_upload.py..."
mv app_with_upload.py "$ARCHIVE_DIR/" 2>/dev/null || echo "文件不存在或已移动"

# 归档备份文件
echo "归档备份文件..."
mv app_with_upload.py.backup "$ARCHIVE_DIR/" 2>/dev/null || echo "备份文件不存在"
mv blueprints/api.py.backup_* "$ARCHIVE_DIR/" 2>/dev/null || echo "无api.py备份"
mv blueprints/api.py.before_* "$ARCHIVE_DIR/" 2>/dev/null || echo "无api.py临时文件"

# 列出归档内容
echo ""
echo "归档内容:"
ls -lh "$ARCHIVE_DIR/"

echo ""
echo "✓ 归档完成"
EOF
```

**归档的文件**:
- `app_with_upload.py` (1,740行遗留代码)
- `app_with_upload.py.backup`
- `blueprints/api.py.backup_*`
- `blueprints/api.py.before_*`

**检查点**:
- [ ] 遗留文件已移动到归档目录
- [ ] 原位置文件已不存在
- [ ] 归档目录包含所有预期文件

---

### 阶段4: 创建归档说明 (10分钟)

**目的**: 记录归档内容和保留信息

```bash
ssh u_topn@39.105.12.124 << 'EOF'
cd /home/u_topn/TOP_N
ARCHIVE_DIR="archive/migration_$(date +%Y%m%d)"

cat > "$ARCHIVE_DIR/README.md" << 'READMEEOF'
# 架构迁移归档 - 2025年12月

## 归档日期
$(date '+%Y-%m-%d %H:%M:%S')

## 归档原因
TOP_N 项目完成了从单体应用到蓝图架构的迁移。
本归档包含已被替代的遗留代码和临时备份文件。

## 归档内容

### 主要文件
- **app_with_upload.py** (1,740行)
  - 原单体应用入口文件
  - 包含22+重复路由定义
  - 已被 app_factory.py + blueprints/ 替代

### 备份文件
- **app_with_upload.py.backup**
  - 迁移前的备份

- **api.py.backup_YYYYMMDD_HHMMSS**
  - 路由迁移过程中的备份

- **api.py.before_***
  - 添加特定功能前的临时备份

## 迁移概要

### 完成的工作
1. **P0**: 修复 auth_decorators 导入错误
2. **P1**: 提取7个缺失路由到蓝图
   - /api/accounts/<id>/test
   - /api/accounts/import
   - /api/csdn/login
   - /api/csdn/check_login
   - /api/csdn/publish
   - /api/platforms
   - /api/retry_publish/<id>
3. **P2**: 配置管理统一（环境变量）
4. **P3**: 测试覆盖
5. **P4**: 生产部署
6. **P5**: 48小时监控验证

### 新架构
- **入口**: app_factory.py (应用工厂模式)
- **路由**: blueprints/ 目录
  - api.py - 主要API路由
  - api_retry.py - 重试发布
  - auth.py - 认证路由
  - pages.py - 页面路由
  - 等等...
- **配置**: config.py + .env
- **测试**: tests/test_migrated_routes.py

## 代码统计

| 项目 | 旧架构 | 新架构 | 变化 |
|------|--------|--------|------|
| 主文件行数 | 1,740 | ~800 (分布在多个蓝图) | 重构 |
| 路由重复 | 22+ | 0 | 消除 |
| 配置方式 | 硬编码 | 环境变量 | 改进 |
| 测试覆盖 | 无 | 15个测试用例 | 新增 |

## 保留期限

**建议保留期**: 90天

**保留至**: $(date -d '+90 days' '+%Y-%m-%d' 2>/dev/null || date -v+90d '+%Y-%m-%d' 2>/dev/null || echo '2026-03-22')

**原因**:
- 作为参考和回滚依据
- 防止意外需求
- 验证新架构稳定性

**90天后可删除条件**:
- 新架构运行稳定
- 无回滚需求
- 无历史代码查询需求

## 恢复方法

如果需要恢复旧代码（不推荐）:

\`\`\`bash
# 1. 停止服务
sudo systemctl stop topn

# 2. 恢复归档文件
cd /home/u_topn/TOP_N/backend
cp ../archive/migration_YYYYMMDD/app_with_upload.py ./

# 3. 修改systemd配置
sudo nano /etc/systemd/system/topn.service
# 修改 ExecStart 指向 app_with_upload:app

# 4. 重启服务
sudo systemctl daemon-reload
sudo systemctl start topn
\`\`\`

## 相关文档

- **迁移完整报告**: `/home/u_topn/TOP_N/ARCHITECTURE_CLEANUP_COMPLETE_REPORT.md`
- **部署报告**: `/home/u_topn/TOP_N/DEPLOYMENT_REPORT_20251222.md`
- **监控日志**: `/home/u_topn/TOP_N/monitoring_log_20251222.md`

## 联系信息

- **执行人**: Claude Code
- **执行日期**: 2025-12-22
- **Git Commit**: 71c88f4

---

**创建时间**: $(date '+%Y-%m-%d %H:%M:%S')
**归档版本**: 1.0
READMEEOF

echo "README.md 已创建"
cat "$ARCHIVE_DIR/README.md"
EOF
```

**检查点**:
- [ ] README.md 创建成功
- [ ] 内容完整准确

---

### 阶段5: 清理临时文件 (5分钟)

**目的**: 删除不需要的临时和备份文件

```bash
ssh u_topn@39.105.12.124 << 'EOF'
cd /home/u_topn/TOP_N

# 清理.pyc文件
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -delete

# 清理临时文件
rm -f backend/*.backup 2>/dev/null || true
rm -f backend/nohup.out 2>/dev/null || true

echo "✓ 临时文件清理完成"
EOF
```

**检查点**:
- [ ] .pyc 文件已清理
- [ ] 临时文件已删除

---

### 阶段6: 更新文档 (10分钟)

**目的**: 更新项目文档反映新架构

**需要更新的文档**:

1. **README.md** (如果存在)
   - 更新架构说明
   - 更新启动命令

2. **开发文档**
   - 更新部署流程
   - 更新开发指南

**检查点**:
- [ ] 文档已更新
- [ ] 新架构说明准确

---

### 阶段7: Git 提交 (10分钟)

**目的**: 将归档更改提交到版本控制

**在本地执行**:

```bash
cd /d/code/TOP_N

# 检查状态
git status

# 添加归档相关文件
git add P6_ARCHIVE_PLAN.md
git add P6_COMPLETION_REPORT.md  # 稍后创建
git add FINAL_PROJECT_SUMMARY.md  # 稍后创建

# 提交
git commit -m "P6: 归档清理完成

归档内容:
- app_with_upload.py → archive/migration_20251222/
- 所有备份文件已归档
- 临时文件已清理

文档更新:
- 创建归档说明 README.md
- 生成P6完成报告
- 生成最终项目总结

项目状态:
✅ P0-P6 全部完成
✅ 架构清理完成
✅ 生产环境稳定运行

保留期: 归档文件保留90天至 2026-03-22"

# 推送到远程
git push origin main
```

**检查点**:
- [ ] 所有更改已提交
- [ ] 已推送到远程仓库
- [ ] Git 历史清晰

---

### 阶段8: 服务验证 (5分钟)

**目的**: 确认归档后服务仍正常

```bash
# 验证服务
ssh u_topn@39.105.12.124 "bash /home/u_topn/quick_check.sh"

# 完整验证
ssh u_topn@39.105.12.124 << 'EOF'
# 服务状态
sudo systemctl status topn

# 健康检查
curl http://localhost:8080/api/health

# 测试新路由
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8080/api/platforms
EOF
```

**检查点**:
- [ ] 服务正常运行
- [ ] 健康检查通过
- [ ] 新路由可访问

---

## 完成标准

### 技术标准

- [ ] 所有遗留文件已归档
- [ ] 归档目录结构清晰
- [ ] README.md 说明完整
- [ ] 临时文件已清理
- [ ] 服务验证通过
- [ ] Git 提交完成

### 文档标准

- [ ] 归档说明文档完整
- [ ] P6 完成报告已生成
- [ ] 最终项目总结已生成
- [ ] 所有文档已提交Git

---

## 回滚方案

如果P6执行过程中出现问题：

### 快速恢复归档文件

```bash
ssh u_topn@39.105.12.124 << 'EOF'
cd /home/u_topn/TOP_N
ARCHIVE_DIR="archive/migration_$(date +%Y%m%d)"

# 恢复文件
cp "$ARCHIVE_DIR/app_with_upload.py" backend/ 2>/dev/null

echo "文件已恢复"
EOF
```

**注意**: P6阶段风险很低，因为只是移动文件到归档目录，不影响运行中的服务。

---

## 后续维护

### 定期检查 (推荐)

**30天后**:
- 检查新架构稳定性
- 评估是否仍需归档文件

**60天后**:
- 再次评估
- 决定是否提前删除归档

**90天后**:
- 如果一切正常，安全删除归档
- 保留 README.md 作为历史记录

### 删除归档命令

```bash
# 90天后，如果确认不再需要
ssh u_topn@39.105.12.124 << 'EOF'
cd /home/u_topn/TOP_N
ARCHIVE_DIR="archive/migration_20251222"

# 保留 README.md
cp "$ARCHIVE_DIR/README.md" archive/migration_20251222_README.md

# 删除归档文件
rm -rf "$ARCHIVE_DIR"

echo "归档已删除，README已保留"
EOF
```

---

## 执行检查清单

### 执行前

- [ ] P5 监控期完成
- [ ] 监控结果符合标准
- [ ] 团队确认可以执行
- [ ] 备份已验证

### 执行中

- [ ] 阶段1: 备份验证 ✓
- [ ] 阶段2: 创建归档目录 ✓
- [ ] 阶段3: 归档遗留文件 ✓
- [ ] 阶段4: 创建归档说明 ✓
- [ ] 阶段5: 清理临时文件 ✓
- [ ] 阶段6: 更新文档 ✓
- [ ] 阶段7: Git 提交 ✓
- [ ] 阶段8: 服务验证 ✓

### 执行后

- [ ] 生成P6完成报告
- [ ] 生成最终项目总结
- [ ] 通知团队成员
- [ ] 更新项目状态

---

## 时间估算

| 阶段 | 预计时间 | 累计时间 |
|------|---------|----------|
| 1. 备份验证 | 10分钟 | 10分钟 |
| 2. 创建归档目录 | 5分钟 | 15分钟 |
| 3. 归档遗留文件 | 10分钟 | 25分钟 |
| 4. 创建归档说明 | 10分钟 | 35分钟 |
| 5. 清理临时文件 | 5分钟 | 40分钟 |
| 6. 更新文档 | 10分钟 | 50分钟 |
| 7. Git 提交 | 10分钟 | 60分钟 |
| 8. 服务验证 | 5分钟 | 65分钟 |
| **总计** | **65分钟** | - |

**预留缓冲**: 30分钟
**预计总时间**: 1.5-2小时

---

## 成功标志

完成P6后，项目将达到以下状态：

✅ **代码库清洁**
- 无遗留代码
- 无重复文件
- 无临时备份

✅ **架构统一**
- 单一应用入口 (app_factory.py)
- 蓝图化路由结构
- 环境变量配置

✅ **文档完整**
- 归档说明清晰
- 历史可追溯
- 维护指南完备

✅ **服务稳定**
- 48+ 小时稳定运行
- 零重大问题
- 用户满意

---

**计划版本**: 1.0
**创建时间**: 2025-12-22
**预计执行**: 2025-12-24 20:10+
**预计完成**: 2025-12-24 22:00
