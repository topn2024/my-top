# 发布历史数据流程说明

## 📊 数据来源总结

发布历史表格中显示的**文章标题**和**查看内容**按钮打开的内容，**全部来自 `publish_history` 表**。

---

## 🔄 完整数据流程

### 1️⃣ 数据存储（发布时）

当文章发布到知乎时，系统会在 `publish_history` 表中创建一条记录：

```python
# 位置：backend/app_with_upload.py 第1426-1437行
publish_record = PublishHistory(
    user_id=user.id,
    article_id=article_id,              # 关联的文章ID（可能为NULL）
    article_title=title,                # ✅ 文章标题（直接存储）
    article_content=content,            # ✅ 文章内容（直接存储）
    platform='知乎',
    status='success' if success else 'failed',
    url=article_url if success else '',
    message=message
)
db.add(publish_record)
db.commit()
```

**关键点：**
- `article_title` 和 `article_content` 在发布时就保存到 `publish_history` 表
- 即使 `articles` 表中的文章被删除，发布历史仍然保留完整的标题和内容

---

### 2️⃣ 数据读取（显示历史）

#### 后端API：`/api/publish_history`

```python
# 位置：backend/app_with_upload.py 第1300-1323行

@app.route('/api/publish_history', methods=['GET'])
@login_required
def get_publish_history():
    # 从 publish_history 表查询
    history = db.query(PublishHistory).filter_by(
        user_id=user.id
    ).order_by(PublishHistory.published_at.desc()).limit(50).all()

    # 转换为字典格式返回
    return jsonify({
        'success': True,
        'history': [record.to_dict() for record in history]
    })
```

#### 模型的 to_dict() 方法

```python
# 位置：backend/models.py 第210-223行

def to_dict(self):
    return {
        'id': self.id,
        'article_id': self.article_id,
        'article_title': self.article_title,      # ✅ 从 publish_history 表
        'article_content': self.article_content,  # ✅ 从 publish_history 表
        'user_id': self.user_id,
        'platform': self.platform,
        'status': self.status,
        'url': self.url,
        'message': self.message,
        'published_at': self.published_at.isoformat() if self.published_at else None
    }
```

---

### 3️⃣ 前端显示

#### 显示标题（表格中）

```javascript
// 位置：static/publish_history.js 第114-115行

const title = item.article_title || '未知';  // ✅ 来自 publish_history 表
const displayTitle = title.length > 40 ? title.substring(0, 40) + '...' : title;
```

#### 查看内容按钮

```javascript
// 位置：static/publish_history.js 第123行

${item.article_content ? `<button onclick="publishHistoryManager.viewContent(${item.id})" class="view-content-btn">📄 查看内容</button>` : '<span style="color: #999;">无内容</span>'}
```

- 如果 `item.article_content` 存在（不为空），显示"📄 查看内容"按钮
- 否则显示"无内容"

#### 查看内容弹窗

```javascript
// 位置：static/publish_history.js 第151-179行

viewContent(id) {
    const item = this.allHistory.find(h => h.id === id);
    if (!item || !item.article_content) {
        alert('没有文章内容');
        return;
    }

    // 创建模态框显示内容
    modal.innerHTML = `
        <div class="modal-content">
            <h3>${this.escapeHtml(item.article_title || '文章内容')}</h3>
            <div class="content-preview">${this.escapeHtml(item.article_content)}</div>
        </div>
    `;
}
```

**关键点：**
- 标题：`item.article_title` ✅ 来自 `publish_history` 表
- 内容：`item.article_content` ✅ 来自 `publish_history` 表

---

## 📋 数据表关系图

```
┌─────────────────────────────────────────────────────────────┐
│                   publish_history 表                         │
├─────────────────────────────────────────────────────────────┤
│ id              INTEGER (主键)                               │
│ article_id      INTEGER (外键 → articles.id, 可为NULL)      │
│ user_id         INTEGER (外键 → users.id)                   │
│ platform        VARCHAR(50)                                  │
│ status          VARCHAR(50)                                  │
│ url             TEXT                                         │
│ message         TEXT                                         │
│ published_at    TIMESTAMP                                    │
│ article_title   VARCHAR(500)  ← 📄 表格显示的标题           │
│ article_content TEXT          ← 📄 查看内容按钮打开的内容    │
└─────────────────────────────────────────────────────────────┘
           ↑
           │ (可选关联)
           │
┌──────────┴──────────┐
│   articles 表        │
├─────────────────────┤
│ id                  │
│ workflow_id         │
│ title               │
│ content             │
│ article_type        │
└─────────────────────┘
```

---

## ⚠️ 重要说明

### 为什么要在 publish_history 表存储标题和内容？

1. **数据独立性**：即使 `articles` 表中的文章被删除，发布历史仍然完整
2. **支持临时发布**：有些发布可能没有关联 `article_id`，但仍需要保存内容
3. **支持重试功能**：失败的发布可以从历史记录中获取标题和内容进行重试
4. **历史快照**：记录发布时的实际内容，即使原文章后续被修改

### 数据一致性

- 发布时，`article_title` 和 `article_content` 从请求参数中获取
- 如果有 `article_id`，这些数据通常来自 `articles` 表
- 如果没有 `article_id`（临时发布），数据直接从用户提交的表单获取

---

## ✅ 总结

**问题：发布历史表格里面看到的文章标题和查看内容按钮打开的页面中的内容是从哪个表里出来的数据？**

**答案：全部来自 `publish_history` 表**

- 文章标题：`publish_history.article_title` ✅
- 文章内容：`publish_history.article_content` ✅

这两个字段在发布时就被存储到 `publish_history` 表中，作为发布记录的快照保存。
