# TOP_N 生产环境监控指南 (P5)

**监控期**: 部署后 48 小时
**负责人**: 部署执行人
**服务器**: 39.105.12.124
**监控开始**: 部署完成时间

---

## 监控计划概览

| 时间点 | 检查项目 | 工具/命令 |
|-------|---------|----------|
| 0小时 (部署后) | 立即验证 | verify_production.sh |
| 6小时 | 定期检查 | 手动检查日志和指标 |
| 12小时 | 定期检查 | 手动检查日志和指标 |
| 24小时 | 定期检查 | 手动检查日志和指标 |
| 36小时 | 定期检查 | 手动检查日志和指标 |
| 48小时 | 最终评估 | 完整报告 |

---

## 监控指标和成功标准

### 1. 错误率

**目标**: < 0.1%
**测量方法**: 检查日志中的错误条目

```bash
ssh u_topn@39.105.12.124
cd /home/u_topn/TOP_N/backend

# 统计最近1000行日志中的错误
tail -1000 logs/all.log | grep -i error | wc -l

# 查看错误详情
tail -1000 logs/all.log | grep -i error | tail -10
```

**判断标准**:
- ✅ 优秀: 0 错误
- ✅ 良好: 1-2 个错误（非关键功能）
- ⚠️ 警告: 3-5 个错误
- ❌ 失败: >5 个错误或任何严重错误

### 2. 新路由调用情况

**目标**: 所有新路由至少被成功调用 1 次
**测量方法**: 分析访问日志

```bash
# 检查新路由的访问记录
cd /home/u_topn/TOP_N/backend

# 账号测试路由
grep "accounts/.*/test" logs/all.log | tail -5

# 账号导入路由
grep "accounts/import" logs/all.log | tail -5

# CSDN 路由
grep "csdn/" logs/all.log | tail -10

# 平台列表路由
grep "platforms" logs/all.log | tail -5

# 重试发布路由
grep "retry_publish" logs/all.log | tail -5
```

**判断标准**:
- ✅ 理想: 所有路由都有成功调用记录（HTTP 200）
- ✅ 良好: 大部分路由有调用记录
- ⚠️ 警告: 部分路由未被调用（可能功能未使用）
- ❌ 失败: 路由调用全部失败（404 或 500）

### 3. 响应时间

**目标**: 与部署前基线持平（±10%）
**测量方法**: 检查日志中的响应时间

```bash
# 查看最近的API请求响应时间
tail -500 logs/all.log | grep "ms" | tail -20

# 统计平均响应时间（如果日志格式支持）
tail -500 logs/all.log | grep -oP '\d+ms' | sed 's/ms//' | awk '{sum+=$1; count++} END {print "平均响应时间:", sum/count, "ms"}'
```

**判断标准**:
- ✅ 优秀: 响应时间减少或持平
- ✅ 良好: 响应时间增加 < 10%
- ⚠️ 警告: 响应时间增加 10-20%
- ❌ 失败: 响应时间增加 > 20%

### 4. 系统资源使用

**目标**: CPU < 70%, 内存 < 80%, 磁盘 < 90%
**测量方法**: 系统监控命令

```bash
ssh u_topn@39.105.12.124

# CPU 和内存使用
top -bn1 | head -20

# 查看 Gunicorn 进程资源使用
ps aux | grep gunicorn

# 磁盘使用
df -h /home/u_topn

# 检查日志文件大小
du -sh /home/u_topn/TOP_N/backend/logs/
```

**判断标准**:
- ✅ 正常: 所有指标在目标范围内
- ⚠️ 警告: 某个指标接近阈值
- ❌ 失败: 某个指标超过阈值

### 5. 用户反馈

**目标**: 零用户报错
**测量方法**:
- 检查用户提交的问题
- 主动询问用户使用情况
- 监控用户活跃度

**判断标准**:
- ✅ 优秀: 零用户投诉，正面反馈
- ✅ 良好: 零用户投诉，无反馈
- ⚠️ 警告: 1-2 个轻微问题报告
- ❌ 失败: 多个用户报告严重问题

---

## 定期检查流程 (每 6 小时)

### 检查清单

```bash
# 1. SSH 连接到生产服务器
ssh u_topn@39.105.12.124

# 2. 导航到项目目录
cd /home/u_topn/TOP_N/backend

# 3. 检查服务状态
if [ -f logs/gunicorn.pid ]; then
    PID=$(cat logs/gunicorn.pid)
    if ps -p $PID > /dev/null; then
        echo "✓ 服务运行正常 (PID: $PID)"
    else
        echo "✗ 服务已停止"
    fi
else
    echo "✗ 未找到 PID 文件"
fi

# 4. 检查最近的错误
echo ""
echo "=== 最近的错误 (最后 50 行) ==="
tail -50 logs/all.log | grep -i error || echo "无错误"

# 5. 检查新路由访问
echo ""
echo "=== 新路由访问统计 ==="
echo "账号测试: $(grep -c 'accounts/.*/test' logs/all.log || echo 0) 次"
echo "账号导入: $(grep -c 'accounts/import' logs/all.log || echo 0) 次"
echo "CSDN登录: $(grep -c 'csdn/login' logs/all.log || echo 0) 次"
echo "CSDN检查: $(grep -c 'csdn/check_login' logs/all.log || echo 0) 次"
echo "CSDN发布: $(grep -c 'csdn/publish' logs/all.log || echo 0) 次"
echo "平台列表: $(grep -c 'GET.*platforms' logs/all.log || echo 0) 次"
echo "重试发布: $(grep -c 'retry_publish' logs/all.log || echo 0) 次"

# 6. 检查系统资源
echo ""
echo "=== 系统资源 ==="
top -bn1 | grep "Cpu(s)" | awk '{print "CPU: " $2}'
free -m | awk 'NR==2{printf "内存: %s/%sMB (%.2f%%)\n", $3,$2,$3*100/$2 }'
df -h /home/u_topn | awk 'NR==2{print "磁盘: " $5 " 已使用"}'

# 7. 检查日志文件大小
echo ""
echo "=== 日志文件大小 ==="
du -sh logs/

# 8. 快速健康检查
echo ""
echo "=== 健康检查 ==="
curl -s http://localhost:8080/api/health | head -20
```

### 记录检查结果

在本地创建监控日志文件: `monitoring_log_YYYYMMDD.md`

```markdown
# 监控日志 - 2025-12-22

## 检查时间: 2025-12-22 18:00

- [x] 服务运行状态: ✅ 正常
- [x] 错误数量: 0
- [x] 新路由访问:
  - 账号测试: 3 次
  - CSDN登录: 5 次
  - 平台列表: 10 次
- [x] 系统资源: CPU 30%, 内存 50%, 磁盘 40%
- [x] 用户反馈: 无投诉

**问题**: 无
**行动**: 无需行动

---

## 检查时间: 2025-12-23 00:00

... (继续记录)
```

---

## 问题响应流程

### 级别 1: 信息 (Info)

**特征**:
- 轻微的日志信息
- 性能在正常范围内
- 无用户影响

**行动**:
- 记录观察结果
- 继续监控

### 级别 2: 警告 (Warning)

**特征**:
- 少量非致命错误
- 性能接近阈值
- 个别用户反馈问题

**行动**:
1. 详细检查日志获取上下文
2. 尝试重现问题
3. 如果可以轻松修复，准备热修复
4. 增加监控频率

### 级别 3: 错误 (Error)

**特征**:
- 多个错误影响功能
- 性能显著下降
- 多个用户报告问题

**行动**:
1. 立即调查根本原因
2. 评估是否需要回滚
3. 如果是新功能问题，考虑禁用新路由
4. 准备修复或回滚

```bash
# 禁用新路由的紧急方法（不推荐，优先回滚）
# 1. SSH 到服务器
# 2. 编辑 app_factory.py 注释掉新蓝图注册
# 3. 重启服务
```

### 级别 4: 严重 (Critical)

**特征**:
- 服务完全不可用
- 数据损坏
- 所有用户无法使用

**行动**:
1. **立即执行回滚** (运行 `rollback_deployment.sh`)
2. 通知所有相关人员
3. 调查根本原因
4. 准备修复方案
5. 重新部署前进行彻底测试

```bash
# 立即回滚
bash rollback_deployment.sh
```

---

## 48 小时后最终评估

### 评估清单

在 48 小时监控期结束后，完成以下评估:

- [ ] **错误率**: ____% (目标: <0.1%)
- [ ] **新路由调用统计**:
  - [ ] `/api/accounts/<id>/test`: ____ 次
  - [ ] `/api/accounts/import`: ____ 次
  - [ ] `/api/csdn/login`: ____ 次
  - [ ] `/api/csdn/check_login`: ____ 次
  - [ ] `/api/csdn/publish`: ____ 次
  - [ ] `/api/platforms`: ____ 次
  - [ ] `/api/retry_publish/<id>`: ____ 次
- [ ] **平均响应时间**: ____ ms (变化: ____%)
- [ ] **系统资源**: CPU: ___%, 内存: ___%, 磁盘: ___%
- [ ] **用户反馈**: ____ 个问题报告
- [ ] **服务稳定性**: ____ 次重启/崩溃

### 决策矩阵

| 结果 | 所有指标正常 | 部分指标警告 | 多个指标失败 | 严重问题 |
|-----|------------|------------|------------|---------|
| **行动** | ✅ 继续 P6 | ⚠️ 修复后继续 | ❌ 回滚重来 | ❌ 立即回滚 |

### 最终报告模板

```markdown
# TOP_N 架构清理 - 48小时监控报告

**监控期**: 2025-12-22 18:00 ~ 2025-12-24 18:00
**部署版本**: [Git commit hash]
**监控人**: [Your name]

## 执行概要

✅/⚠️/❌ 部署成功/有问题/失败

## 关键指标

- **错误率**: X.X% (目标: <0.1%)
- **平均响应时间**: XXX ms (变化: ±XX%)
- **服务可用性**: XX.X%
- **用户满意度**: ✅ 无投诉

## 新功能使用情况

| 路由 | 调用次数 | 成功率 |
|-----|---------|-------|
| /api/accounts/<id>/test | XX | XX% |
| /api/accounts/import | XX | XX% |
| /api/csdn/* | XX | XX% |
| /api/platforms | XX | XX% |
| /api/retry_publish/<id> | XX | XX% |

## 发现的问题

1. [问题描述]
   - 影响: [高/中/低]
   - 状态: [已修复/监控中/待修复]

## 建议

- [建议 1]
- [建议 2]

## 结论

✅ **建议继续执行 P6 阶段（归档清理）**

或

⚠️ **建议修复问题后再继续**

或

❌ **建议回滚部署**
```

---

## 监控工具和脚本

### 1. 实时日志监控

```bash
ssh u_topn@39.105.12.124
cd /home/u_topn/TOP_N/backend
tail -f logs/all.log | grep --color=auto -E "error|ERROR|Error|WARNING|CRITICAL|CSDN|retry_publish|accounts/test|accounts/import|platforms"
```

### 2. 错误统计脚本

创建文件 `monitor_errors.sh`:

```bash
#!/bin/bash
echo "=== 错误统计报告 ==="
echo "生成时间: $(date)"
echo ""

cd /home/u_topn/TOP_N/backend

echo "最近 1 小时的错误:"
find logs/ -name "*.log" -mmin -60 -exec grep -h "ERROR" {} \; | wc -l

echo ""
echo "最近 24 小时的错误:"
find logs/ -name "*.log" -mmin -1440 -exec grep -h "ERROR" {} \; | wc -l

echo ""
echo "错误类型分布:"
tail -5000 logs/all.log | grep -i error | cut -d'-' -f5- | sort | uniq -c | sort -rn | head -10
```

### 3. 性能监控脚本

创建文件 `monitor_performance.sh`:

```bash
#!/bin/bash
echo "=== 性能监控报告 ==="
echo "生成时间: $(date)"
echo ""

# Gunicorn 进程
echo "Gunicorn 进程:"
ps aux | grep gunicorn | grep -v grep

echo ""
echo "CPU 和内存:"
top -bn1 | head -20 | tail -15

echo ""
echo "网络连接:"
netstat -an | grep :8080 | wc -l
echo "个活动连接"

echo ""
echo "磁盘使用:"
df -h /home/u_topn
```

### 4. 快速检查脚本

创建文件 `quick_check.sh`:

```bash
#!/bin/bash
# 快速检查所有关键指标

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "TOP_N 快速健康检查"
echo "===================="

# 服务状态
if ps aux | grep -v grep | grep gunicorn > /dev/null; then
    echo -e "${GREEN}✓${NC} Gunicorn 运行中"
else
    echo -e "${RED}✗${NC} Gunicorn 未运行"
fi

# 健康检查
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/api/health)
if [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}✓${NC} API 健康检查通过"
else
    echo -e "${RED}✗${NC} API 健康检查失败 (HTTP $STATUS)"
fi

# 错误数量
ERRORS=$(tail -100 logs/all.log | grep -i error | wc -l)
if [ "$ERRORS" -lt 5 ]; then
    echo -e "${GREEN}✓${NC} 最近错误数量: $ERRORS"
else
    echo -e "${RED}✗${NC} 最近错误数量过多: $ERRORS"
fi

# 磁盘空间
DISK_USAGE=$(df -h /home/u_topn | awk 'NR==2{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 90 ]; then
    echo -e "${GREEN}✓${NC} 磁盘使用: ${DISK_USAGE}%"
else
    echo -e "${RED}✗${NC} 磁盘空间不足: ${DISK_USAGE}%"
fi
```

---

## 总结

按照此监控指南，您应该能够:

1. ✅ 及时发现部署后的问题
2. ✅ 跟踪新功能的使用情况
3. ✅ 维持服务稳定性
4. ✅ 收集数据支持 P6 阶段决策

**关键原则**:
- **预防优于治疗**: 定期检查避免问题累积
- **快速响应**: 发现问题立即行动
- **数据驱动**: 基于指标做决策，不凭感觉
- **用户第一**: 用户体验是最终标准

如有任何疑问，参考回滚脚本随时准备回滚。

---

**监控开始时间**: ____________
**预计结束时间**: ____________
**监控负责人**: ____________
