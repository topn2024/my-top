# 发布历史功能 - 使用示例

## API 使用示例

### 1. 发布文章到知乎 (自动记录历史)

```bash
# POST /api/publish_zhihu
curl -X POST http://localhost:3001/api/publish_zhihu \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "article_id": 123,
    "account_id": 456,
    "title": "深度解析微服务架构设计",
    "content": "本文将深入探讨微服务架构的核心概念..."
  }'
```

**响应 (成功):**
```json
{
  "success": true,
  "url": "https://zhuanlan.zhihu.com/p/789012345",
  "message": "文章发布成功"
}
```

**响应 (失败):**
```json
{
  "success": false,
  "error": "账号登录失败,请检查用户名和密码"
}
```

**说明:**
- 无论发布成功还是失败,系统都会自动保存到 `publish_history` 表
- 成功时会保存文章URL
- 失败时会保存错误信息

---

### 2. 查询发布历史

#### 2.1 获取最近20条发布记录

```bash
# GET /api/publish_history
curl http://localhost:3001/api/publish_history \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应:**
```json
{
  "success": true,
  "count": 3,
  "history": [
    {
      "id": 15,
      "article_id": 123,
      "article_title": "深度解析微服务架构设计",
      "article_type": "技术创新角度的深度分析文章",
      "user_id": 1,
      "platform": "知乎",
      "status": "success",
      "url": "https://zhuanlan.zhihu.com/p/789012345",
      "message": "文章发布成功",
      "published_at": "2025-12-09T14:30:25"
    },
    {
      "id": 14,
      "article_id": 122,
      "article_title": "用户体验优化的10个实用技巧",
      "article_type": "用户体验角度的评测文章",
      "user_id": 1,
      "platform": "知乎",
      "status": "failed",
      "url": null,
      "message": "账号登录失败,请检查用户名和密码",
      "published_at": "2025-12-09T13:15:10"
    },
    {
      "id": 13,
      "article_id": 121,
      "article_title": "2025年前端技术趋势分析",
      "article_type": "未来发展趋势的前瞻分析",
      "user_id": 1,
      "platform": "知乎",
      "status": "success",
      "url": "https://zhuanlan.zhihu.com/p/789012344",
      "message": "文章发布成功",
      "published_at": "2025-12-09T10:05:30"
    }
  ]
}
```

#### 2.2 获取指定数量的记录

```bash
# 获取最近5条记录
curl "http://localhost:3001/api/publish_history?limit=5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 2.3 按平台筛选

```bash
# 只获取知乎的发布历史
curl "http://localhost:3001/api/publish_history?platform=知乎&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 前端 JavaScript 示例

### 完整的前端集成示例

```html
<!DOCTYPE html>
<html>
<head>
  <title>发布历史查看器</title>
  <style>
    .history-item {
      border: 1px solid #ddd;
      padding: 15px;
      margin: 10px 0;
      border-radius: 5px;
    }
    .success { border-left: 4px solid #4caf50; }
    .failed { border-left: 4px solid #f44336; }
    .status-badge {
      display: inline-block;
      padding: 3px 8px;
      border-radius: 3px;
      font-size: 12px;
      font-weight: bold;
    }
    .status-success { background: #4caf50; color: white; }
    .status-failed { background: #f44336; color: white; }
  </style>
</head>
<body>
  <h1>我的发布历史</h1>

  <!-- 筛选器 -->
  <div>
    <label>平台筛选:</label>
    <select id="platformFilter">
      <option value="">全部平台</option>
      <option value="知乎">知乎</option>
      <option value="CSDN">CSDN</option>
      <option value="掘金">掘金</option>
    </select>

    <label>显示数量:</label>
    <select id="limitFilter">
      <option value="10">10条</option>
      <option value="20" selected>20条</option>
      <option value="50">50条</option>
    </select>

    <button onclick="loadHistory()">刷新</button>
  </div>

  <!-- 历史记录列表 -->
  <div id="historyList"></div>

  <script>
    // 获取Token (实际项目中从localStorage或cookie获取)
    function getToken() {
      return localStorage.getItem('auth_token');
    }

    // 加载发布历史
    async function loadHistory() {
      const platform = document.getElementById('platformFilter').value;
      const limit = document.getElementById('limitFilter').value;

      // 构建查询参数
      const params = new URLSearchParams({ limit });
      if (platform) {
        params.append('platform', platform);
      }

      try {
        const response = await fetch(`/api/publish_history?${params}`, {
          headers: {
            'Authorization': 'Bearer ' + getToken()
          }
        });

        const data = await response.json();

        if (data.success) {
          displayHistory(data.history);
        } else {
          alert('获取发布历史失败: ' + (data.error || '未知错误'));
        }
      } catch (error) {
        console.error('Error:', error);
        alert('网络错误: ' + error.message);
      }
    }

    // 显示历史记录
    function displayHistory(history) {
      const listDiv = document.getElementById('historyList');

      if (history.length === 0) {
        listDiv.innerHTML = '<p>暂无发布记录</p>';
        return;
      }

      listDiv.innerHTML = history.map(record => {
        const statusClass = record.status === 'success' ? 'success' : 'failed';
        const statusBadge = record.status === 'success' ? 'status-success' : 'status-failed';
        const statusText = record.status === 'success' ? '成功' : '失败';

        return `
          <div class="history-item ${statusClass}">
            <h3>${record.article_title || '无标题'}</h3>
            <div>
              <span class="status-badge ${statusBadge}">${statusText}</span>
              <span style="margin-left: 10px;">平台: ${record.platform}</span>
              <span style="margin-left: 10px;">时间: ${formatDate(record.published_at)}</span>
            </div>
            ${record.article_type ? `<p><small>类型: ${record.article_type}</small></p>` : ''}
            ${record.url ? `<p><a href="${record.url}" target="_blank">查看文章 →</a></p>` : ''}
            ${record.message ? `<p><em>${record.message}</em></p>` : ''}
          </div>
        `;
      }).join('');
    }

    // 格式化日期
    function formatDate(dateString) {
      const date = new Date(dateString);
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    }

    // 页面加载时自动获取历史
    window.onload = loadHistory;
  </script>
</body>
</html>
```

---

## Python 代码示例

### 在后端代码中使用发布服务

```python
from services.publish_service import PublishService
from config import get_config

# 初始化服务
config = get_config()
publish_service = PublishService(config)

# 示例1: 发布文章到知乎
def publish_article_example():
    """发布文章示例"""
    try:
        result = publish_service.publish_to_zhihu(
            user_id=1,          # 当前登录用户ID
            account_id=2,       # 使用的知乎账号ID
            article_id=123,     # 要发布的文章ID
            title="深度解析微服务架构设计",
            content="本文将深入探讨微服务架构的核心概念和最佳实践..."
        )

        if result.get('success'):
            print(f"✓ 发布成功!")
            print(f"  文章链接: {result.get('url')}")
            # 历史记录已自动保存到数据库
        else:
            print(f"✗ 发布失败: {result.get('error')}")
            # 失败记录也已自动保存到数据库

        return result

    except Exception as e:
        print(f"✗ 发布异常: {e}")
        # 异常情况下也会保存失败记录
        return {'success': False, 'error': str(e)}


# 示例2: 查询发布历史
def get_history_example():
    """查询发布历史示例"""

    # 获取最近20条发布记录
    history = publish_service.get_publish_history(user_id=1)

    print(f"共有 {len(history)} 条发布记录:\n")

    for record in history:
        print(f"ID: {record['id']}")
        print(f"文章: {record['article_title']}")
        print(f"平台: {record['platform']}")
        print(f"状态: {record['status']}")
        print(f"时间: {record['published_at']}")

        if record['status'] == 'success' and record['url']:
            print(f"链接: {record['url']}")
        elif record['status'] == 'failed' and record['message']:
            print(f"错误: {record['message']}")

        print("-" * 50)


# 示例3: 按平台查询
def get_zhihu_history_example():
    """查询知乎发布历史"""

    zhihu_history = publish_service.get_publish_history(
        user_id=1,
        limit=10,
        platform="知乎"
    )

    print(f"知乎平台共有 {len(zhihu_history)} 条发布记录")

    # 统计成功和失败数量
    success_count = sum(1 for r in zhihu_history if r['status'] == 'success')
    failed_count = len(zhihu_history) - success_count

    print(f"成功: {success_count} 条, 失败: {failed_count} 条")


# 示例4: 批量发布多篇文章
def batch_publish_example(user_id, account_id, articles):
    """批量发布文章"""
    results = []

    for article in articles:
        print(f"正在发布: {article['title']}")

        result = publish_service.publish_to_zhihu(
            user_id=user_id,
            account_id=account_id,
            article_id=article['id'],
            title=article['title'],
            content=article['content']
        )

        results.append({
            'article_id': article['id'],
            'title': article['title'],
            'success': result.get('success'),
            'url': result.get('url'),
            'error': result.get('error')
        })

        # 每条都会自动保存到发布历史

    # 统计
    success_count = sum(1 for r in results if r['success'])
    print(f"\n批量发布完成: {success_count}/{len(results)} 篇成功")

    return results


# 运行示例
if __name__ == '__main__':
    # 发布一篇文章
    publish_article_example()

    # 查询历史
    get_history_example()

    # 查询知乎历史
    get_zhihu_history_example()
```

---

## 数据库查询示例

### 直接使用 SQLAlchemy 查询

```python
from models import PublishHistory, Article, User, get_db_session
from sqlalchemy import func

db = get_db_session()

# 查询1: 获取用户的所有发布记录
user_history = db.query(PublishHistory).filter_by(user_id=1).all()

# 查询2: 获取成功的发布记录
success_records = db.query(PublishHistory).filter_by(
    user_id=1,
    status='success'
).all()

# 查询3: 统计各平台发布数量
platform_stats = db.query(
    PublishHistory.platform,
    func.count(PublishHistory.id).label('count')
).filter_by(
    user_id=1
).group_by(
    PublishHistory.platform
).all()

print("各平台发布数量:")
for platform, count in platform_stats:
    print(f"  {platform}: {count} 篇")

# 查询4: 获取最近7天的发布记录
from datetime import datetime, timedelta
seven_days_ago = datetime.now() - timedelta(days=7)

recent_history = db.query(PublishHistory).filter(
    PublishHistory.user_id == 1,
    PublishHistory.published_at >= seven_days_ago
).order_by(
    PublishHistory.published_at.desc()
).all()

# 查询5: 关联查询文章信息
history_with_articles = db.query(
    PublishHistory, Article
).join(
    Article, PublishHistory.article_id == Article.id
).filter(
    PublishHistory.user_id == 1
).all()

for history, article in history_with_articles:
    print(f"{article.title} -> {history.platform} ({history.status})")

db.close()
```

---

## 常见问题 (FAQ)

### Q1: 如果发布失败,历史记录会保存吗?

**A:** 会的。无论发布成功还是失败,系统都会自动保存发布历史记录。失败时会保存错误信息到 `message` 字段。

### Q2: 可以删除历史记录吗?

**A:** 当前版本没有提供删除API,但您可以:
- 通过删除文章来级联删除相关的发布历史
- 通过删除用户来级联删除该用户的所有发布历史
- 直接在数据库中执行删除操作

### Q3: 历史记录会包含文章内容吗?

**A:** 不会。历史记录只保存发布的元信息(平台、状态、URL等),不保存文章内容。文章内容存储在 `articles` 表中。

### Q4: 如何按日期范围查询?

**A:** 当前API不支持日期范围查询,但您可以:
- 获取所有记录后在前端过滤
- 或者扩展 `get_publish_history` 方法添加日期参数

### Q5: 可以重新发布失败的文章吗?

**A:** 当前版本没有提供重试API,但您可以:
- 从历史记录中找到失败的 `article_id`
- 重新调用 `/api/publish_zhihu` 发布该文章
- 系统会创建新的发布历史记录

---

## 总结

发布历史功能的核心优势:

✓ **自动记录** - 无需手动保存,发布时自动记录
✓ **完整信息** - 包含文章标题、平台、状态、时间等
✓ **失败追踪** - 失败记录包含错误信息,方便调试
✓ **灵活查询** - 支持按平台筛选、限制数量
✓ **关联查询** - 自动关联文章信息
✓ **简单集成** - API简单易用,前后端都易于集成

开始使用吧! 🚀
