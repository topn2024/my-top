# 服务层清理报告

## 发现的版本冲突

### AI服务
```
backend/services/
├── ai_service.py           # 主要版本 ✅ 保留
└── ai_service_v2.py        # 旧版本 ❌ 可删除
```

### 发布Worker
```
backend/services/
├── publish_worker.py           # 当前使用 ✅ 保留
├── publish_worker_enhanced.py  # 增强版 ❌ 可删除
└── publish_worker_v3.py        # v3版本 ❌ 可删除
```

## 决策

### 保留的服务（主要版本）
- ✅ `ai_service.py` - 最新的AI服务实现
- ✅ `publish_worker.py` - 当前使用的发布worker
- ✅ `task_queue_manager.py` - 任务队列管理
- ✅ `file_service.py` - 文件处理
- ✅ `account_service.py` - 账号服务
- ✅ `workflow_service.py` - 工作流服务
- ✅ 所有提示词服务（*_prompt_service.py）

### 标记为废弃（可删除）
- ❌ `ai_service_v2.py` - 已被ai_service.py取代
- ❌ `publish_worker_enhanced.py` - 功能已合并
- ❌ `publish_worker_v3.py` - 旧版本

### 清理操作（待执行）
```bash
# 移动到archive目录而不是直接删除
mkdir -p backend/services/archive
mv backend/services/ai_service_v2.py backend/services/archive/
mv backend/services/publish_worker_enhanced.py backend/services/archive/
mv backend/services/publish_worker_v3.py backend/services/archive/
```

## 服务规范

### 命名规范
- 使用清晰的服务名，不带版本后缀
- 功能描述性命名: `{domain}_service.py`
- 避免 v2, v3, enhanced等后缀

### 版本管理
- 使用Git管理版本历史
- 重大更新时打tag
- 不保留多个版本文件

### 文档要求
- 每个服务添加docstring
- 说明主要功能和API
- 记录依赖关系

## 执行状态
- ✅ 已识别冗余服务
- ✅ 已制定清理计划
- ⏸️ 暂不删除文件（避免破坏依赖）
- 📝 标记为待清理

**结论**: 问题已识别，清理计划已制定，标记完成
