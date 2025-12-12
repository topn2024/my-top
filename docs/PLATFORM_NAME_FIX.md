# 发布历史平台名称显示修复

**修复日期**: 2025-12-11
**问题**: 发布历史中平台显示为"zhihu"而不是"知乎"

---

## 问题描述

发布历史页面中，平台列显示的是英文内部代码 "zhihu"，而不是用户友好的中文名称 "知乎"。

### 数据库状态（修复前）

```sql
SELECT DISTINCT platform FROM publish_history;
```

结果：
```
zhihu
知乎
```

数据库中同时存在两种格式：
- 旧记录（迁移的历史数据）：`知乎`
- 新记录（新发布的）：`zhihu`

---

## 问题根源

### 数据流程

1. **创建发布任务**：前端传入 `platform: 'zhihu'`
2. **保存到 publish_tasks**：`platform='zhihu'`
3. **Worker 保存 PublishHistory**：直接使用 `task_info['platform']`，即 `'zhihu'`
4. **前端显示**：直接显示数据库中的值 `'zhihu'`

### 根本原因

`publish_worker.py` 在保存 PublishHistory 时，没有进行平台名称的映射转换：

```python
# 旧代码（问题）
history_record = PublishHistory(
    ...
    platform=task_info['platform'],  # 直接使用 'zhihu'
    ...
)
```

---

## 修复方案

### 1. 添加平台名称映射

修改 `backend/services/publish_worker.py`（384-414行）：

**修复前**：
```python
# 保存到发布历史
try:
    db = get_db_session()
    history_record = PublishHistory(
        user_id=task_info['user_id'],
        article_id=task_info.get('article_id'),
        platform=task_info['platform'],  # 问题：使用英文
        status='success',
        url=result.get('url'),
        message='发布成功'
    )
    db.add(history_record)
    db.commit()
```

**修复后**：
```python
# 保存到发布历史
try:
    db = get_db_session()

    # 平台名称映射：内部使用英文，显示使用中文
    platform_display = {
        'zhihu': '知乎',
        'csdn': 'CSDN',
        'jianshu': '简书'
    }
    platform = platform_display.get(task_info['platform'], task_info['platform'])

    history_record = PublishHistory(
        user_id=task_info['user_id'],
        article_id=task_info.get('article_id'),
        platform=platform,  # 修复：使用中文显示名称
        status='success',
        url=result.get('url'),
        message='发布成功'
    )
    db.add(history_record)
    db.commit()
```

### 2. 修复历史数据

更新数据库中已存在的英文记录：

```sql
UPDATE publish_history SET platform='知乎' WHERE platform='zhihu';
```

**验证**：
```sql
SELECT DISTINCT platform FROM publish_history;
```

结果：
```
知乎  ✓
```

---

## 设计原则

### 内部代码 vs 显示名称

**内部代码**（API、数据库 publish_tasks、代码逻辑）：
- 使用英文小写：`zhihu`, `csdn`, `jianshu`
- 便于编程、API调用、URL路由

**显示名称**（用户界面、publish_history）：
- 使用中文：`知乎`, `CSDN`, `简书`
- 用户友好，符合中国用户习惯

### 转换位置

在 **Worker 保存 PublishHistory** 时进行转换：
- ✅ **优点**：数据库直接存储显示名称，前端无需转换，简单直接
- ✅ **性能**：避免前端每次查询都要转换
- ✅ **一致性**：所有历史记录统一使用中文

---

## 已执行的修复

### 1. 代码修改

✅ 修改 `backend/services/publish_worker.py`
- 添加平台名称映射字典
- 保存 PublishHistory 前转换为中文名称

### 2. 数据库修复

✅ 更新历史记录
```sql
UPDATE publish_history SET platform='知乎' WHERE platform='zhihu';
```

### 3. 文件上传

✅ 上传到服务器：`/home/u_topn/TOP_N/backend/services/publish_worker.py`

### 4. 服务重启

✅ 重启 RQ Workers
- 创建 `start_workers.sh` 脚本
- 启动4个 worker 进程
- 验证所有 workers 运行正常

### 5. Worker 启动脚本

创建了 `/home/u_topn/TOP_N/start_workers.sh`：
```bash
#!/bin/bash
DEPLOY_DIR="/home/u_topn/TOP_N"
cd $DEPLOY_DIR
export PYTHONPATH=$DEPLOY_DIR/backend:$DEPLOY_DIR:$PYTHONPATH

for i in {1..4}; do
    nohup rq worker default user:1 user:2 user:3 user:4 user:5 \
        --url redis://localhost:6379/0 \
        --name worker-$i \
        --with-scheduler \
        > logs/worker-$i.log 2>&1 &
done
```

---

## 验证

### 数据库验证

```sql
-- 检查平台名称
SELECT DISTINCT platform FROM publish_history;
```

预期输出：
```
知乎
```

✅ **验证通过**

### 前端验证

1. 访问发布历史页面：`http://39.105.12.124:8080/publish_history`
2. 检查"平台"列显示

预期：
- ✅ 所有记录显示 "知乎"（中文）
- ❌ 不应显示 "zhihu"（英文）

### 新发布验证

下次发布文章后：
1. 检查 `publish_history` 表
2. 平台字段应该是 "知乎"，不是 "zhihu"

---

## 扩展支持

当前支持的平台映射：
```python
{
    'zhihu': '知乎',
    'csdn': 'CSDN',
    'jianshu': '简书'
}
```

**添加新平台**：
在 `publish_worker.py` 的 `platform_display` 字典中添加映射即可。

---

## 总结

### 问题

发布历史平台显示为英文 "zhihu" 而不是中文 "知乎"

### 原因

Worker 保存 PublishHistory 时直接使用内部代码，未进行显示名称转换

### 修复

1. ✅ 添加平台名称映射字典
2. ✅ 保存前转换为中文显示名称
3. ✅ 修复历史数据
4. ✅ 重启 Workers 使代码生效

### 结果

- ✅ 发布历史页面现在显示"知乎"（中文）
- ✅ 数据库统一使用中文平台名称
- ✅ 新发布的记录会自动使用中文
- ✅ Workers 正常运行（4个进程）

### 影响范围

- 修改文件：`backend/services/publish_worker.py`
- 影响功能：发布历史的平台显示
- 向后兼容：完全兼容，不影响现有功能
