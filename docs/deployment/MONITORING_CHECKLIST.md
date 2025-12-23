# TOP_N P5 监控提醒清单

**监控期**: 2025-12-22 20:10 至 2025-12-24 20:10
**服务器**: 39.105.12.124
**当前状态**: 🟢 监控进行中

---

## 快速参考

### 紧急联系方式
- **快速回滚**: `bash rollback_deployment.sh`
- **快速检查**: SSH后运行 `bash /home/u_topn/quick_check.sh`
- **日志查看**: `sudo journalctl -u topn.service -n 100`

### 关键文件位置
- 监控日志: `monitoring_log_20251222.md`
- 监控时间表: `MONITORING_SCHEDULE.md`
- 首次检查报告: `MONITORING_REPORT_0H.md`
- 回滚脚本: `rollback_deployment.sh`

---

## 检查点日程

### ✅ 检查点 0 - 已完成
**时间**: 2025-12-22 20:10 (已完成)
**状态**: ✅ 优秀 - 零错误
**下次检查**: 6小时后

---

### ⏰ 检查点 1 - 第6小时
**预定时间**: **2025-12-23 02:10** (周一凌晨)
**倒计时**: ~6小时

#### 提醒
- [ ] 提前15分钟准备
- [ ] 确保网络连接稳定
- [ ] 准备好SSH终端

#### 检查清单 (预计10分钟)
```bash
# 1. 连接服务器 (1分钟)
ssh u_topn@39.105.12.124

# 2. 快速检查脚本 (2分钟)
bash /home/u_topn/quick_check.sh

# 3. 详细服务检查 (2分钟)
sudo systemctl status topn
ps aux | grep gunicorn | grep -v grep

# 4. 错误日志检查 (2分钟)
sudo journalctl -u topn.service --since "6 hours ago" | grep -i error
sudo journalctl -u topn.service --since "6 hours ago" | grep -c "ERROR"

# 5. 资源检查 (1分钟)
free -m
df -h /home/u_topn
uptime

# 6. 健康检查 (1分钟)
curl http://localhost:8080/api/health

# 7. 新路由测试 (1分钟)
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8080/api/platforms
curl -s -o /dev/null -w "HTTP %{http_code}\n" -X POST http://localhost:8080/api/csdn/login
```

#### 记录结果
更新 `monitoring_log_20251222.md` 的"检查点 6"部分

#### 决策标准
- ✅ **继续监控**: 错误=0, 服务正常
- ⚠️ **增加频率**: 错误>0但<5, 性能下降
- ❌ **考虑回滚**: 错误>5, 服务异常

---

### ⏰ 检查点 2 - 第12小时
**预定时间**: **2025-12-23 08:10** (周一早晨)
**倒计时**: ~12小时

#### 提醒
- [ ] 工作时间前检查
- [ ] 准备迎接用户流量
- [ ] 确认夜间无问题

#### 检查清单 (预计10分钟)
同检查点1的清单

#### 额外关注
- 12小时运行稳定性
- 资源使用趋势（与基线对比）
- 是否有自动重启记录

#### 决策标准
- ✅ **继续**: 累计错误<3, 趋势稳定
- ⚠️ **警告**: 累计错误3-10, 性能轻微下降
- ❌ **回滚**: 累计错误>10, 明显问题

---

### ⏰ 检查点 3 - 第18小时
**预定时间**: **2025-12-23 14:10** (周一下午)
**倒计时**: ~18小时

#### 提醒
- [ ] 工作时段中期检查
- [ ] 关注实际用户使用情况
- [ ] 检查新路由调用记录

#### 检查清单 (预计10分钟)
同检查点1的清单

#### 额外关注
- 工作时段性能表现
- 用户活动日志
- 新路由实际使用次数
- 响应时间是否正常

#### 决策标准
- ✅ **继续**: 用户无投诉, 性能稳定
- ⚠️ **警告**: 轻微性能问题, 响应变慢
- ❌ **回滚**: 用户报错, 功能受影响

---

### ⏰ 检查点 4 - 第24小时 ⚠️ 重要
**预定时间**: **2025-12-23 20:10** (周一晚上)
**倒计时**: ~24小时
**重要性**: 🔴 **中期评估 - 关键决策点**

#### 提醒
- [ ] 预留30分钟进行全面评估
- [ ] 准备评估报告
- [ ] 准备决策依据

#### 检查清单 (预计30分钟)

##### 基础检查 (10分钟)
同检查点1的清单

##### 深度分析 (20分钟)
```bash
# 1. 24小时错误汇总
sudo journalctl -u topn.service --since "24 hours ago" | grep ERROR | wc -l
sudo journalctl -u topn.service --since "24 hours ago" | grep CRITICAL | wc -l
sudo journalctl -u topn.service --since "24 hours ago" | grep WARNING | wc -l

# 2. 服务重启次数
systemctl show topn --property=NRestarts

# 3. 内存趋势（与基线对比）
# 基线: 1166MB (62%)
free -m

# 4. 新路由使用统计
sudo journalctl -u topn.service --since "24 hours ago" | grep -E "(accounts/test|accounts/import|csdn/|platforms|retry_publish)" | wc -l

# 5. 用户反馈收集
# 检查是否有用户问题报告

# 6. 性能对比
# 响应时间是否与基线(<100ms)一致
```

#### 24小时决策矩阵

| 累计错误数 | 服务可用性 | 用户反馈 | 决策 |
|-----------|----------|---------|------|
| 0 | 100% | 无投诉 | ✅ 可考虑降低监控频率至12h |
| 1-5 | >99% | 无/轻微 | ✅ 继续6h监控 |
| 6-20 | >95% | 轻微问题 | ⚠️ 继续密切监控，准备热修复 |
| >20 | <95% | 明显问题 | ❌ 考虑回滚 |

#### 输出文档
创建 `MONITORING_REPORT_24H.md` 中期评估报告

---

### ⏰ 检查点 5 - 第30小时
**预定时间**: **2025-12-24 02:10** (周二凌晨)
**倒计时**: ~30小时

#### 检查清单 (预计10分钟)
同检查点1的清单

#### 关注重点
- 第二个夜间周期稳定性
- 长期运行无退化

---

### ⏰ 检查点 6 - 第36小时
**预定时间**: **2025-12-24 08:10** (周二早晨)
**倒计时**: ~36小时

#### 检查清单 (预计10分钟)
同检查点1的清单

#### 关注重点
- 第二个工作日开始前检查
- 36小时长期稳定性

---

### ⏰ 检查点 7 - 第42小时
**预定时间**: **2025-12-24 14:10** (周二下午)
**倒计时**: ~42小时

#### 检查清单 (预计10分钟)
同检查点1的清单

#### 关注重点
- 准备最终评估
- 收集所有趋势数据

---

### ⏰ 检查点 8 - 第48小时 ⚠️ 最终
**预定时间**: **2025-12-24 20:10** (周二晚上)
**倒计时**: ~48小时
**重要性**: 🔴 **最终评估 - 关键决策点**

#### 提醒
- [ ] 预留60分钟进行完整评估
- [ ] 准备最终报告
- [ ] 准备P6归档计划执行

#### 检查清单 (预计60分钟)

##### 基础检查 (10分钟)
同检查点1的清单

##### 完整评估 (50分钟)
```bash
# 1. 48小时完整错误统计
sudo journalctl -u topn.service --since "48 hours ago" | grep ERROR | wc -l
sudo journalctl -u topn.service --since "48 hours ago" | grep CRITICAL | wc -l
sudo journalctl -u topn.service --since "48 hours ago" | grep WARNING | wc -l

# 2. 服务稳定性指标
systemctl show topn --property=ActiveState
systemctl show topn --property=SubState
systemctl show topn --property=NRestarts
systemctl show topn --property=ActiveEnterTimestamp

# 3. 资源使用汇总
# CPU负载趋势
# 内存使用趋势（基线: 1166MB）
# 磁盘使用变化（基线: 11GB）

# 4. 新路由完整统计
sudo journalctl -u topn.service --since "48 hours ago" | grep "accounts/test" | wc -l
sudo journalctl -u topn.service --since "48 hours ago" | grep "accounts/import" | wc -l
sudo journalctl -u topn.service --since "48 hours ago" | grep "csdn/login" | wc -l
sudo journalctl -u topn.service --since "48 hours ago" | grep "csdn/check_login" | wc -l
sudo journalctl -u topn.service --since "48 hours ago" | grep "csdn/publish" | wc -l
sudo journalctl -u topn.service --since "48 hours ago" | grep "platforms" | wc -l
sudo journalctl -u topn.service --since "48 hours ago" | grep "retry_publish" | wc -l

# 5. 性能对比分析
# 响应时间是否维持<100ms
# 是否有性能退化迹象

# 6. 用户反馈汇总
# 收集所有48小时的用户反馈
```

#### 48小时最终决策矩阵

| 指标 | 目标值 | 实际值 | 通过标准 |
|-----|--------|--------|---------|
| 服务可用性 | >99.9% | ___ | ✅ >99% |
| 累计错误数 | <5 | ___ | ✅ <10 |
| 服务重启次数 | 0 | ___ | ✅ <2 |
| 用户投诉 | 0 | ___ | ✅ <3 |
| 响应时间 | <200ms | ___ | ✅ <300ms |
| 内存增长 | <10% | ___ | ✅ <20% |

#### 最终决策

**进入P6归档阶段条件** (所有条件必须满足):
- ✅ 错误率 <0.1% (累计错误<5)
- ✅ 服务可用性 >99.9%
- ✅ 零用户严重投诉
- ✅ 无服务重启或<2次
- ✅ 所有新路由可用
- ✅ 性能指标稳定

**延长监控条件**:
- ⚠️ 有轻微问题但不严重
- ⚠️ 需要更多数据观察

**回滚条件**:
- ❌ 严重错误或高错误率(>10)
- ❌ 服务不稳定(重启>3次)
- ❌ 用户无法使用核心功能

#### 输出文档
创建 `MONITORING_REPORT_48H.md` 最终评估报告

#### 下一步行动
- **如果通过**: 执行 `P6_ARCHIVE_PLAN.md` 归档遗留代码
- **如果延长**: 制定新的监控计划
- **如果回滚**: 执行 `rollback_deployment.sh`

---

## 监控指标参考

### 基线数据 (检查点0)
| 指标 | 基线值 | 说明 |
|------|--------|------|
| CPU负载 (1分钟) | 0.23 | 优秀 |
| CPU负载 (5分钟) | 0.14 | 优秀 |
| CPU负载 (15分钟) | 0.05 | 优秀 |
| 内存使用 | 1166MB (62%) | 正常 |
| Gunicorn内存 | 575MB | 正常 |
| 磁盘使用 | 11GB (29%) | 优秀 |
| 错误数 | 0 | 完美 |
| 响应时间 | <100ms | 优秀 |
| Worker进程数 | 5 | 正常 |

### 警告阈值
| 指标 | 警告值 | 严重值 |
|------|--------|--------|
| CPU负载 (1分钟) | >1.0 | >2.0 |
| 内存使用 | >80% | >90% |
| 磁盘使用 | >80% | >90% |
| 错误数/6h | >2 | >5 |
| 响应时间 | >200ms | >500ms |
| Worker重启 | >1次 | >3次 |

---

## 问题分级和响应

### 🟢 级别1: 信息 (INFO)
**特征**:
- 偶尔的INFO日志
- 性能正常
- 用户无影响

**行动**:
- 记录观察
- 继续按计划监控

---

### 🟡 级别2: 警告 (WARNING)
**特征**:
- 1-5个非致命错误
- 性能接近阈值
- 资源使用升高

**行动**:
1. 详细检查日志上下文
2. 增加监控频率至2-3小时
3. 准备热修复方案
4. 通知相关人员

**响应时间**: 2小时内

---

### 🟠 级别3: 错误 (ERROR)
**特征**:
- 6-20个错误
- 功能部分受影响
- 用户开始报告问题
- 性能明显下降

**行动**:
1. 立即调查根本原因
2. 评估影响范围
3. 决定热修复 or 回滚
4. 实时监控
5. 通知所有相关人员

**响应时间**: 30分钟内

---

### 🔴 级别4: 严重 (CRITICAL)
**特征**:
- >20个错误
- 服务不可用或频繁重启
- 多用户无法使用
- 数据可能受影响

**行动**:
1. **立即执行回滚**
2. 通知所有人员
3. 保存完整日志
4. 事后分析

**响应时间**: 立即

**回滚命令**:
```bash
cd /d/code/TOP_N
bash rollback_deployment.sh
```

---

## 快速命令参考

### 连接服务器
```bash
ssh u_topn@39.105.12.124
```

### 快速健康检查
```bash
# 服务器上运行
bash /home/u_topn/quick_check.sh
```

### 查看实时日志
```bash
# 跟踪最新日志
sudo journalctl -u topn.service -f

# 查看最近100行
sudo journalctl -u topn.service -n 100

# 查看最近1小时
sudo journalctl -u topn.service --since "1 hour ago"
```

### 服务控制
```bash
# 查看状态
sudo systemctl status topn

# 重启服务
sudo systemctl restart topn

# 查看服务详情
systemctl show topn
```

### 进程检查
```bash
# 查看Gunicorn进程
ps aux | grep gunicorn | grep -v grep

# 查看进程数
ps aux | grep gunicorn | grep -v grep | wc -l
```

### 资源监控
```bash
# CPU和负载
uptime
top -bn1 | head -10

# 内存
free -m

# 磁盘
df -h /home/u_topn
```

### API测试
```bash
# 健康检查
curl http://localhost:8080/api/health

# 新路由测试（批量）
for route in platforms csdn/login; do
  echo "Testing /api/$route"
  curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8080/api/$route
done
```

### 紧急回滚
```bash
# 本地执行
cd /d/code/TOP_N
bash rollback_deployment.sh

# 或服务器端
ssh u_topn@39.105.12.124
cd /home/u_topn/TOP_N
git reset --hard <上一个commit>
sudo systemctl restart topn
```

---

## 监控进度跟踪

### 完成情况
- [x] 检查点 0 (0h) - 2025-12-22 20:10 ✅
- [ ] 检查点 1 (6h) - 2025-12-23 02:10 ⏳
- [ ] 检查点 2 (12h) - 2025-12-23 08:10 ⏳
- [ ] 检查点 3 (18h) - 2025-12-23 14:10 ⏳
- [ ] 检查点 4 (24h) - 2025-12-23 20:10 ⚠️ 中期评估
- [ ] 检查点 5 (30h) - 2025-12-24 02:10 ⏳
- [ ] 检查点 6 (36h) - 2025-12-24 08:10 ⏳
- [ ] 检查点 7 (42h) - 2025-12-24 14:10 ⏳
- [ ] 检查点 8 (48h) - 2025-12-24 20:10 ⚠️ 最终评估

### 统计数据
- **已完成**: 1/9 (11%)
- **剩余**: 8/9 (89%)
- **已用时间**: 11分钟
- **剩余时间**: 48小时

---

## 联系和升级

### 技术负责人
- **姓名**: [待填写]
- **联系方式**: [待填写]
- **升级条件**: ERROR级别或以上

### 紧急联系
- **运维团队**: [待填写]
- **升级条件**: CRITICAL级别

### 用户支持
- **反馈渠道**: [待填写]
- **响应时间**: [待填写]

---

## 备注和提示

### 夜间检查 (02:10)
- 设置闹钟提醒
- 可使用手机SSH客户端
- 重点: 稳定性验证，可快速检查

### 工作时段检查 (08:10, 14:10)
- 关注用户活动
- 注意实际使用情况
- 收集用户反馈

### 关键决策点
- **24小时**: 决定是否调整监控策略
- **48小时**: 决定是否进入P6归档阶段

### 时间管理
- 常规检查: ~10分钟
- 中期评估 (24h): ~30分钟
- 最终评估 (48h): ~60分钟

### 文档更新
- 每次检查后立即更新 `monitoring_log_20251222.md`
- 发现问题立即记录
- 保持记录完整准确

---

**文档创建**: 2025-12-22 20:30
**文档版本**: 1.0
**状态**: 🟢 监控进行中
**下次检查**: 2025-12-23 02:10 (6小时检查点)

---

## 附录: 检查点报告模板

### 检查点 X 报告模板

```markdown
## 检查点 X: 第Xh检查

**检查时间**: YYYY-MM-DD HH:MM
**检查人**: [姓名]
**耗时**: X分钟

### 1. 服务状态
- 状态: [Active/Inactive]
- PID: [进程ID]
- 运行时间: [小时数]
- Worker数量: [数量]

### 2. 系统资源
- CPU负载: [1分钟], [5分钟], [15分钟]
- 内存使用: [已用]/[总量] ([百分比]%)
- 磁盘使用: [已用]/[总量] ([百分比]%)

### 3. 错误统计
- ERROR: [数量]
- CRITICAL: [数量]
- WARNING: [数量]

### 4. 健康检查
- API健康: [通过/失败]
- 响应时间: [毫秒]

### 5. 新路由测试
- /api/platforms: HTTP [状态码]
- /api/csdn/login: HTTP [状态码]
- [其他路由...]

### 6. 观察和问题
- [记录任何异常或值得注意的情况]

### 7. 决策
- [继续监控/增加频率/准备回滚]

**下次检查**: YYYY-MM-DD HH:MM
```

---

**提醒**: 本清单是监控阶段的重要工具，请保持更新并严格执行每个检查点！
