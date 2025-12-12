# 统一日志配置说明

## 概述

系统现在将所有运行日志统一输出到 `/home/u_topn/TOP_N/logs/all.log` 文件,同时保留原有的各个独立日志文件。

## 日志文件列表

### 1. all.log - 统一日志文件(新增) ✨
**路径**: `/home/u_topn/TOP_N/logs/all.log`
**内容**: 所有系统日志的集中输出
- Gunicorn应用日志(带时间戳和模块信息)
- Worker-1日志(前缀: `[Worker-1]`)
- Worker-2日志(前缀: `[Worker-2]`)
- Worker-3日志(前缀: `[Worker-3]`)
- Worker-4日志(前缀: `[Worker-4]`)

### 2. 原有日志文件(保持不变)
- `worker-1.log` - Worker-1独立日志
- `worker-2.log` - Worker-2独立日志
- `worker-3.log` - Worker-3独立日志
- `worker-4.log` - Worker-4独立日志
- `error.log` - Gunicorn错误日志
- `access.log` - Gunicorn访问日志
- `gunicorn.log` - Gunicorn启动日志

## 日志格式

### Gunicorn应用日志格式
```
2025-12-11 00:04:41,377 - root - INFO - [app_factory.py:99] - 日志配置完成: 控制台输出 + /home/u_topn/TOP_N/logs/all.log
```

格式: `时间戳 - logger名称 - 日志级别 - [文件:行号] - 消息`

### Worker日志格式
```
[Worker-1] 00:10:41 Worker worker-1: started with PID 357375, version 2.6.1
[Worker-2] 00:10:41 *** Listening on default, user:1, user:2, user:3, user:4, user:5...
```

格式: `[Worker-X] 时间 消息`

## 如何查看日志

### 1. 实时监控所有日志
```bash
ssh u_topn@39.105.12.124 "tail -f /home/u_topn/TOP_N/logs/all.log"
```

### 2. 查看最近的日志
```bash
ssh u_topn@39.105.12.124 "tail -100 /home/u_topn/TOP_N/logs/all.log"
```

### 3. 搜索特定内容
```bash
# 搜索错误日志
ssh u_topn@39.105.12.124 "grep -i error /home/u_topn/TOP_N/logs/all.log"

# 搜索特定Worker的日志
ssh u_topn@39.105.12.124 "grep '\\[Worker-1\\]' /home/u_topn/TOP_N/logs/all.log"

# 搜索任务执行日志
ssh u_topn@39.105.12.124 "grep '任务执行日志' /home/u_topn/TOP_N/logs/all.log"
```

### 4. 按时间范围查看
```bash
# 查看今天的日志
ssh u_topn@39.105.12.124 "grep '2025-12-11' /home/u_topn/TOP_N/logs/all.log"

# 查看某个小时的日志
ssh u_topn@39.105.12.124 "grep '2025-12-11 23:' /home/u_topn/TOP_N/logs/all.log"
```

### 5. 提取完整的任务日志块
```bash
# 提取某个TaskID的完整日志
ssh u_topn@39.105.12.124 "awk '/任务执行日志 - TaskID: YOUR_TASK_ID/,/总耗时/' /home/u_topn/TOP_N/logs/all.log"
```

## 技术实现

### 1. Gunicorn应用日志
修改了 `backend/app_factory.py` 中的 `setup_logging` 函数:
- 添加了 `RotatingFileHandler` 输出到 `all.log`
- 文件大小限制: 50MB
- 备份文件数: 5个
- 编码: UTF-8

### 2. Worker日志
修改了 `backend/start_workers.sh`:
- 使用管道将worker输出同时写入两个文件
- 每条日志添加 `[Worker-X]` 前缀便于识别
- 使用子shell确保进程正确管理

## 日志轮转

### all.log自动轮转
- 当文件达到50MB时自动创建新文件
- 保留最近5个备份文件
- 备份文件命名: `all.log.1`, `all.log.2`, ... `all.log.5`

### 手动清理日志
如果需要手动清理日志:
```bash
# 清空all.log(谨慎操作!)
ssh u_topn@39.105.12.124 "> /home/u_topn/TOP_N/logs/all.log"

# 备份后清空
ssh u_topn@39.105.12.124 "
cd /home/u_topn/TOP_N/logs
cp all.log all.log.backup_\$(date +%Y%m%d_%H%M%S)
> all.log
"
```

## 优势

### ✅ 集中查看
- 一个文件包含所有日志
- 不需要在多个文件间切换
- 便于全局搜索和分析

### ✅ 保留原有结构
- 原有的独立日志文件继续存在
- 不影响现有的日志查看习惯
- 兼容性好

### ✅ 便于调试
- 可以看到不同组件的时序关系
- Worker和应用日志混合显示
- 更容易发现问题

### ✅ 易于分享
- 需要分享日志时,只需提供all.log
- 包含完整的系统运行信息
- 减少遗漏

## 监控建议

### 开发/测试环境
```bash
# 持续监控所有日志
tmux new-session -d -s logs 'ssh u_topn@39.105.12.124 "tail -f /home/u_topn/TOP_N/logs/all.log"'
tmux attach -t logs
```

### 生产环境
```bash
# 只监控错误和警告
ssh u_topn@39.105.12.124 "tail -f /home/u_topn/TOP_N/logs/all.log | grep -E 'ERROR|WARN|✗'"
```

## 日志分析脚本示例

### 统计今日任务数
```bash
ssh u_topn@39.105.12.124 "
grep '任务执行日志' /home/u_topn/TOP_N/logs/all.log | \
grep \$(date +%Y-%m-%d) | \
wc -l
"
```

### 统计成功/失败任务
```bash
ssh u_topn@39.105.12.124 "
echo -n '成功: '
grep '✓✓✓ 任务执行成功' /home/u_topn/TOP_N/logs/all.log | wc -l
echo -n '失败: '
grep '✗✗✗ 任务执行失败' /home/u_topn/TOP_N/logs/all.log | wc -l
"
```

### 查看平均执行时间
```bash
ssh u_topn@39.105.12.124 "
grep '总耗时:' /home/u_topn/TOP_N/logs/all.log | \
awk '{sum+=\$2; count++} END {print \"平均耗时:\", sum/count, \"秒\"}'
"
```

## 常见问题

### Q: all.log文件太大怎么办?
A: 系统配置了自动轮转,达到50MB会自动创建新文件。如需手动清理,参考上面的"手动清理日志"部分。

### Q: 能否只查看某个Worker的日志?
A: 可以,使用grep过滤:
```bash
ssh u_topn@39.105.12.124 "tail -f /home/u_topn/TOP_N/logs/all.log | grep '\\[Worker-1\\]'"
```

### Q: 能否关闭all.log?
A: 可以,但不推荐。如必须关闭:
1. 修改 `backend/app_factory.py`,注释掉 `all_file_handler` 相关代码
2. 修改 `backend/start_workers.sh`,去掉输出到all.log的管道
3. 重启服务

### Q: all.log影响性能吗?
A: 影响很小。日志写入是异步的,不会阻塞主业务。

## 总结

统一日志系统现已配置完成,你可以通过以下命令快速查看:

```bash
# 实时查看所有日志
ssh u_topn@39.105.12.124 "tail -f /home/u_topn/TOP_N/logs/all.log"

# 查看最近100行
ssh u_topn@39.105.12.124 "tail -100 /home/u_topn/TOP_N/logs/all.log"

# 搜索错误
ssh u_topn@39.105.12.124 "grep ERROR /home/u_topn/TOP_N/logs/all.log | tail -20"
```

---

**配置完成时间**: 2025-12-11 00:10
**配置版本**: v1.0
**状态**: ✅ 已部署到生产环境
