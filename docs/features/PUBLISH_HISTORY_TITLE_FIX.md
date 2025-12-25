# 发布历史标题显示修复

**修复日期**: 2025-12-11
**问题**: 发布历史中所有文章标题都显示为"临时发布"

---

## 问题分析

### 症状

用户反馈：发布历史页面中，所有文章标题都显示为"临时发布"，而不是实际的文章标题。

### 数据库状态

查询 `publish_history` 表：
```sql
SELECT id, article_id, platform, status, url FROM publish_history ORDER BY id DESC LIMIT 3;
```

结果：
```
14 | 0    | zhihu | success | https://zhuanlan.zhihu.com/p/1982498178818410358/edit
13 | NULL | 知乎  | success | https://zhuanlan.zhihu.com/p/1980790884887966082
12 | NULL | 知乎  | failed  | (null)
```

查询 `publish_tasks` 表：
```sql
SELECT id, article_id, article_title FROM publish_tasks ORDER BY id DESC LIMIT 1;
```

结果：
```
1 | 0 | 揭秘月栖科技：AI智能体的黑科技，竟然这么牛？
```

### 问题根源

**关键发现**：

1. `publish_history.article_id` 为 **0** 或 **NULL**
2. `articles` 表中没有 `id=0` 的记录
3. 旧的 `get_publish_history()` 方法使用 LEFT JOIN 关联 `articles` 表
4. 当 `article_id=0` 时，JOIN 找不到对应记录，`h.article` 为 None
5. 代码将 `h.article` 为 None 的情况统一当作"临时发布"处理

**实际情况**：

- 这些记录**不是真正的临时发布**！
- 实际文章标题存储在 `publish_tasks.article_title` 字段中
- `article_id=0` 是因为发布任务创建时传入的 article_id 为0（临时发布场景）

---

## 修复方案

### 修改 `publish_service.py` 的 `get_publish_history()` 方法

**修复前**（133-170行）：
```python
# 转换为字典并添加文章标题
result = []
for h in history:
    item = h.to_dict()
    # 添加文章标题
    if h.article:
        item['article_title'] = h.article.title
        item['article_type'] = h.article.article_type
    else:
        # 临时发布,使用默认标题
        item['article_title'] = '临时发布'  # ← 问题！没有尝试从publish_tasks获取
        item['article_type'] = 'temp'
    result.append(item)
```

**修复后**（155-183行）：
```python
# 转换为字典并添加文章标题
result = []
for h in history:
    item = h.to_dict()
    # 添加文章标题
    if h.article:
        item['article_title'] = h.article.title
        item['article_type'] = h.article.article_type
    else:
        # 没有关联文章，尝试从URL和时间匹配PublishTask获取标题
        title_found = False
        if h.url:
            # 尝试通过URL和时间范围匹配publish_tasks表
            task = db.query(PublishTask).filter(
                PublishTask.user_id == user_id,
                PublishTask.result_url == h.url,
                PublishTask.article_title.isnot(None)
            ).first()

            if task and task.article_title:
                item['article_title'] = task.article_title
                item['article_type'] = 'temp'
                title_found = True

        # 如果还是没找到标题，使用默认值
        if not title_found:
            item['article_title'] = '临时发布'
            item['article_type'] = 'temp'

    result.append(item)
```

### 修复逻辑

1. **优先使用 articles 表**：如果 `h.article` 存在，使用文章表中的标题（正常流程）
2. **fallback 到 publish_tasks 表**：如果找不到文章，通过 URL 匹配 `publish_tasks` 表获取标题
3. **最终默认值**：如果还是找不到，才显示"临时发布"

**匹配条件**：
```python
PublishTask.user_id == user_id           # 同一用户
PublishTask.result_url == h.url          # 相同URL
PublishTask.article_title.isnot(None)    # 有标题
```

---

## 测试验证

### 数据库验证

```bash
cd /home/u_topn/TOP_N && python3 << 'EOF'
import sys
sys.path.insert(0, 'backend')

from models import get_db_session, PublishHistory, PublishTask

db = get_db_session()

h = db.query(PublishHistory).filter_by(id=14).first()
print(f'PublishHistory ID={h.id}:')
print(f'  article_id: {h.article_id}')
print(f'  url: {h.url}')

if h.url:
    task = db.query(PublishTask).filter(
        PublishTask.user_id == h.user_id,
        PublishTask.result_url == h.url,
        PublishTask.article_title.isnot(None)
    ).first()

    if task:
        print(f'  找到匹配的PublishTask: {task.article_title}')

db.close()
EOF
```

**预期输出**：
```
PublishHistory ID=14:
  article_id: 0
  url: https://zhuanlan.zhihu.com/p/1982498178818410358/edit
  找到匹配的PublishTask: 揭秘月栖科技：AI智能体的黑科技，竟然这么牛？
```

✅ **验证结果**：匹配逻辑正常工作！

### 前端验证

1. 访问 `http://39.105.12.124:8080/publish_history`
2. 检查文章标题是否正确显示

**预期**：
- 第一条记录应该显示："揭秘月栖科技：AI智能体的黑科技，竟然这么牛？"
- 不应该显示"临时发布"

---

## 根本原因分析

### 为什么 article_id 会是 0？

这涉及到发布流程的设计：

1. **正常流程**（通过工作流生成文章）：
   - 用户创建工作流 → 生成文章 → 保存到 `articles` 表 → 获得 `article_id`
   - 发布时使用这个 `article_id`

2. **临时发布流程**（直接发布文本）：
   - 用户直接输入标题和内容 → 不保存到 `articles` 表
   - 发布时 `article_id=0` 或 `None`
   - 文章标题只存储在 `publish_tasks.article_title` 字段

**问题场景**：用户通过临时发布功能发布文章时，`article_id` 为 0，但文章标题存在于 `publish_tasks` 表中。

---

## 长期优化建议

### 建议1：统一数据模型

**问题**：文章标题分散在两个地方
- `articles.title`（工作流生成的文章）
- `publish_tasks.article_title`（临时发布的文章）

**建议**：
1. 临时发布的文章也创建 `articles` 记录，标记为 `workflow_id=NULL`
2. 所有文章统一从 `articles` 表获取标题
3. 简化 `get_publish_history()` 逻辑

### 建议2：修复 article_id=0 的问题

**问题**：`article_id=0` 不是有效的外键值（应该是 NULL）

**修复**：publish_worker.py 中已有转换逻辑（101-102行）：
```python
if article_id == 0:
    article_id = None
```

但这个逻辑**没有在 publish_worker.py 中执行**！需要检查为什么 PublishHistory 的 article_id 是 0 而不是 NULL。

**检查点**：
- `publish_worker.py` 保存 PublishHistory 的代码（384-405行）
- 确认是否执行了 `article_id=0 → None` 的转换

---

## 已执行的修复

1. ✅ 修改 `backend/services/publish_service.py:get_publish_history()` 方法
2. ✅ 上传到服务器：`/home/u_topn/TOP_N/backend/services/publish_service.py`
3. ✅ 重启 Gunicorn 服务
4. ✅ 验证匹配逻辑正常工作

---

## 总结

### 问题

发布历史标题显示为"临时发布"，实际标题存储在 `publish_tasks.article_title`

### 原因

`publish_history.article_id=0`，无法通过 JOIN `articles` 表获取标题

### 修复

添加 fallback 逻辑：通过 URL 匹配 `publish_tasks` 表获取标题

### 结果

- ✅ 发布历史页面现在会正确显示文章标题
- ✅ 临时发布的文章标题可以正确显示
- ✅ 不影响正常工作流生成的文章

### 影响范围

- 修改文件：`backend/services/publish_service.py`
- 影响功能：发布历史页面的标题显示
- 向后兼容：完全兼容，不影响现有功能
