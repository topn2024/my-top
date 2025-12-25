# 发布状态显示修复

**修复日期**: 2025-12-11
**问题**: 文章发布后仍在编辑状态,但前端显示成功

---

## 问题分析

### 数据库记录

查询最近的发布任务:
```sql
SELECT id, task_id, article_title, platform, status, result_url, created_at, completed_at
FROM publish_tasks
ORDER BY id DESC LIMIT 1;
```

**结果**:
```
id: 1
task_id: 83695725-3087-4725-8b74-0761753164ea
article_title: 揭秘月栖科技：AI智能体的黑科技，竟然这么牛？
platform: zhihu
status: success  ← 错误！应该是 failed
result_url: https://zhuanlan.zhihu.com/p/1982498178818410358/edit  ← 包含 /edit！
created_at: 2025-12-11 09:12:30
completed_at: 2025-12-11 17:13:37
```

### 问题根源

**关键发现**: `result_url` 包含 `/edit`，说明文章仍在编辑状态，但 `status` 却是 `success`！

**原因**: 该任务在 17:13:37 完成时，使用的是**旧的有问题的代码**（缺少 `/edit` 验证逻辑）。

**时间线**:
1. 09:12:30 - 任务创建
2. 17:13:37 - 任务完成（使用旧代码，错误地标记为成功）
3. ~17:30 - 上传新的修复代码
4. ~17:30 - 重启worker（新代码生效）

---

## 修复措施

### 1. 修复历史数据

更新数据库中错误的状态:
```sql
UPDATE publish_tasks
SET status='failed',
    error_message='文章未真正发布，仍在编辑状态 (URL包含/edit)'
WHERE id=1 AND result_url LIKE '%/edit';
```

**结果**: 状态已修正为 `failed`

### 2. 新代码已部署

新的验证逻辑 (`backend/zhihu_auto_post_enhanced.py` 324-447行) 包含:

#### 步骤5/5: 验证发布结果（带重试机制）

```python
# 关键判断:URL不能包含/edit
if '/edit' not in current_url:
    logger.info(f"✓ 发布验证成功(第{retry_count + 1}次尝试)")
    publish_success = True
    break
else:
    logger.warning(f"⚠ 第{retry_count + 1}次验证失败,URL仍包含/edit,将进行重试...")

# 最终判断
if not publish_success:
    error_msg = "文章未真正发布，仍在编辑状态"
    logger.error(f"✗ {error_msg}")
    return {
        'success': False,
        'message': error_msg,
        'url': current_url
    }
```

**验证标准**:
1. ✓ URL 必须不包含 `/edit`（最关键！）
2. ✓ URL 应该包含文章路径 (`/p/` 或 `/zhuanlan/`)
3. ✓ URL 不是 write 页面
4. ✓ 页面有"编辑文章"按钮（说明在已发布文章页）
5. ✓ 页面显示"发布成功"提示

### 3. Worker 状态

Workers 在 00:10 启动，已加载新代码:
```
worker-1: PID 357375
worker-2: PID 357379
worker-3: PID 357381
worker-4: PID 357383
```

---

## 测试验证

### 下次发布测试点

1. **后端验证**: 检查 worker 日志是否出现:
   - "步骤5/5: 验证发布结果..."
   - "当前URL: ..." (检查是否包含 /edit)
   - "成功指标: ..." (应该包含"URL不包含/edit")

2. **数据库验证**:
   ```sql
   SELECT status, result_url, error_message FROM publish_tasks ORDER BY id DESC LIMIT 1;
   ```
   - 如果 URL 包含 `/edit`，status 应该是 `failed`
   - error_message 应该是 "文章未真正发布，仍在编辑状态"

3. **前端验证**:
   - 发布历史页面应该显示失败状态
   - 任务列表应该显示失败状态

### 预期日志（成功情况）

```
步骤5/5: 验证发布结果...
当前URL: https://zhuanlan.zhihu.com/p/123456
成功指标数量: 4
成功指标: ['URL不包含/edit（已退出编辑模式）', 'URL包含文章路径', 'URL已离开写作页面', '找到文章编辑按钮']
✓ 发布验证成功(第1次尝试)
✓✓✓ 文章已成功发布! URL: https://zhuanlan.zhihu.com/p/123456
```

### 预期日志（失败情况）

```
步骤5/5: 验证发布结果...
当前URL: https://zhuanlan.zhihu.com/p/123456/edit
⚠ URL仍然包含/edit，文章可能未真正发布
成功指标数量: 1
成功指标: ['URL包含文章路径']
⚠ 第1次验证失败,URL仍包含/edit,将进行重试...
第2次验证(重试 1)...
当前URL: https://zhuanlan.zhihu.com/p/123456/edit
⚠ URL仍然包含/edit，文章可能未真正发布
✗ 所有重试均失败,文章未真正发布
✗ 文章未真正发布，仍在编辑状态
```

---

## 总结

### 已修复

1. ✅ 历史错误数据已修正（任务ID=1 状态改为 failed）
2. ✅ 新代码已部署（包含5步验证，检查 `/edit`）
3. ✅ Workers 已重启并加载新代码
4. ✅ 数据库结构支持 error_message 字段

### 用户请求满足

- ✅ "如果发布之后文章是编辑状态要提示发布失败" - 已实现
  - 后端会返回 `success: False`
  - 数据库 status 会是 `failed`
  - error_message 会说明原因

### 下一步

建议用户重新发布测试，验证:
1. 如果发布成功，URL 应该不包含 `/edit`
2. 如果发布失败（URL 包含 `/edit`），前端应该显示失败状态
3. 查看 worker 日志确认5步验证流程正常执行
