# 用户发布历史记录功能

## 功能概述

本系统已实现完整的用户发布历史记录功能,每当用户发布文章到平台时,系统会自动将发布信息保存到数据库中,方便用户查看历史记录。

## 数据库模型

### PublishHistory 表 (backend/models.py)

存储所有用户的发布历史记录:

```python
class PublishHistory(Base):
    """发布历史表"""
    __tablename__ = 'publish_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(Integer, ForeignKey('articles.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    platform = Column(String(50), nullable=False, index=True)  # 平台名称(知乎、CSDN等)
    status = Column(String(50), nullable=False)  # 发布状态(success/failed)
    url = Column(Text)  # 发布成功后的文章URL
    message = Column(Text)  # 发布消息或错误信息
    published_at = Column(TIMESTAMP, server_default=func.now(), index=True)  # 发布时间
```

**字段说明:**
- `id`: 主键,自增ID
- `article_id`: 关联的文章ID (外键)
- `user_id`: 发布用户ID (外键)
- `platform`: 发布平台名称
- `status`: 发布状态 (success/failed)
- `url`: 发布成功后的文章链接
- `message`: 发布消息或错误信息
- `published_at`: 发布时间 (自动记录)

**关系:**
- 与 `User` 表建立多对一关系
- 与 `Article` 表建立多对一关系

## 核心服务

### PublishService (backend/services/publish_service.py)

提供发布相关的核心功能:

#### 1. publish_to_zhihu() - 发布到知乎

```python
def publish_to_zhihu(self, user_id: int, account_id: int,
                    article_id: int, title: str, content: str) -> Dict
```

**功能:**
- 发布文章到知乎平台
- 自动保存发布历史记录 (成功或失败)

**参数:**
- `user_id`: 用户ID
- `account_id`: 账号ID
- `article_id`: 文章ID (必需,用于关联发布历史)
- `title`: 文章标题
- `content`: 文章内容

**返回值:**
- 发布结果字典,包含 success, url, message 等字段

#### 2. get_publish_history() - 获取发布历史

```python
def get_publish_history(self, user_id: int, limit: int = 20, platform: str = None)
```

**功能:**
- 获取指定用户的发布历史记录
- 支持按平台筛选
- 自动关联文章信息,返回文章标题和类型

**参数:**
- `user_id`: 用户ID
- `limit`: 返回记录数量限制 (默认20条)
- `platform`: 平台名称筛选 (可选,例如 "知乎")

**返回值:**
- 发布历史记录列表,每条记录包含:
  - `id`: 历史记录ID
  - `article_id`: 文章ID
  - `article_title`: 文章标题 (自动关联)
  - `article_type`: 文章类型 (自动关联)
  - `user_id`: 用户ID
  - `platform`: 平台名称
  - `status`: 发布状态
  - `url`: 文章链接
  - `message`: 发布消息
  - `published_at`: 发布时间 (ISO格式字符串)

#### 3. _save_publish_history() - 保存发布历史

```python
def _save_publish_history(self, user_id: int, article_id: int,
                         platform: str, status: str,
                         url: Optional[str] = None,
                         message: Optional[str] = None)
```

**功能:**
- 内部方法,保存发布历史到数据库
- 发布成功或失败时自动调用

## API 端点

### 1. POST /api/publish_zhihu - 发布到知乎

**需要认证:** ✓ (需要登录)

**请求体:**
```json
{
  "article_id": 123,
  "account_id": 456,
  "title": "文章标题",
  "content": "文章内容..."
}
```

**响应示例 (成功):**
```json
{
  "success": true,
  "url": "https://zhuanlan.zhihu.com/p/123456789",
  "message": "发布成功"
}
```

**响应示例 (失败):**
```json
{
  "success": false,
  "error": "发布失败原因..."
}
```

### 2. GET /api/publish_history - 获取发布历史

**需要认证:** ✓ (需要登录)

**查询参数:**
- `limit` (可选): 返回记录数量,默认20
- `platform` (可选): 平台筛选,例如 "知乎"

**请求示例:**
```
GET /api/publish_history?limit=10
GET /api/publish_history?limit=10&platform=知乎
```

**响应示例:**
```json
{
  "success": true,
  "count": 3,
  "history": [
    {
      "id": 1,
      "article_id": 123,
      "article_title": "深度解析XXX技术架构",
      "article_type": "技术创新角度的深度分析文章",
      "user_id": 1,
      "platform": "知乎",
      "status": "success",
      "url": "https://zhuanlan.zhihu.com/p/123456789",
      "message": "发布成功",
      "published_at": "2025-12-09T10:30:00"
    },
    {
      "id": 2,
      "article_id": 124,
      "article_title": "用户体验优化实践",
      "article_type": "用户体验角度的评测文章",
      "user_id": 1,
      "platform": "知乎",
      "status": "failed",
      "url": null,
      "message": "登录失败",
      "published_at": "2025-12-09T09:15:00"
    }
  ]
}
```

## 使用流程

### 1. 发布文章并记录历史

```python
from services.publish_service import PublishService
from config import get_config

config = get_config()
publish_service = PublishService(config)

# 发布文章
result = publish_service.publish_to_zhihu(
    user_id=1,
    account_id=2,
    article_id=123,
    title="文章标题",
    content="文章内容..."
)

# 发布历史会自动保存
# - 发布成功: status='success', url=文章链接
# - 发布失败: status='failed', message=错误信息
```

### 2. 获取发布历史

```python
# 获取最近20条发布历史
history = publish_service.get_publish_history(user_id=1)

# 获取最近10条知乎发布历史
zhihu_history = publish_service.get_publish_history(
    user_id=1,
    limit=10,
    platform="知乎"
)

# 遍历历史记录
for record in history:
    print(f"文章: {record['article_title']}")
    print(f"平台: {record['platform']}")
    print(f"状态: {record['status']}")
    print(f"时间: {record['published_at']}")
    if record['url']:
        print(f"链接: {record['url']}")
```

## 数据库索引

为了优化查询性能,以下字段已建立索引:

- `article_id` - 用于按文章查询
- `user_id` - 用于按用户查询
- `platform` - 用于按平台筛选
- `published_at` - 用于时间排序

## 级联删除

当用户或文章被删除时,相关的发布历史记录会自动删除 (CASCADE):

- 删除用户 → 删除该用户的所有发布历史
- 删除文章 → 删除该文章的所有发布历史

## 前端集成建议

### 显示发布历史列表

```javascript
// 获取发布历史
async function loadPublishHistory() {
  const response = await fetch('/api/publish_history?limit=20', {
    headers: {
      'Authorization': 'Bearer ' + getToken()
    }
  });

  const data = await response.json();

  if (data.success) {
    displayHistory(data.history);
  }
}

// 显示历史记录
function displayHistory(history) {
  history.forEach(record => {
    // 显示文章标题、平台、状态、时间等
    console.log(`${record.article_title} - ${record.platform} - ${record.status}`);

    // 成功的记录显示链接
    if (record.status === 'success' && record.url) {
      console.log(`查看文章: ${record.url}`);
    }

    // 失败的记录显示错误信息
    if (record.status === 'failed' && record.message) {
      console.log(`错误: ${record.message}`);
    }
  });
}
```

### 按平台筛选

```javascript
// 获取知乎发布历史
async function loadZhihuHistory() {
  const response = await fetch('/api/publish_history?platform=知乎&limit=10', {
    headers: {
      'Authorization': 'Bearer ' + getToken()
    }
  });

  const data = await response.json();
  // 处理数据...
}
```

## 扩展建议

### 1. 添加更多平台支持

可以扩展 `PublishService` 类,添加其他平台的发布方法:

```python
def publish_to_csdn(self, user_id, account_id, article_id, title, content):
    # CSDN发布逻辑
    pass

def publish_to_juejin(self, user_id, account_id, article_id, title, content):
    # 掘金发布逻辑
    pass
```

### 2. 添加统计功能

```python
def get_publish_stats(self, user_id):
    """获取发布统计"""
    db = get_db_session()
    try:
        # 总发布数
        total = db.query(PublishHistory).filter_by(user_id=user_id).count()

        # 成功数
        success = db.query(PublishHistory).filter_by(
            user_id=user_id, status='success'
        ).count()

        # 按平台统计
        platform_stats = db.query(
            PublishHistory.platform,
            func.count(PublishHistory.id)
        ).filter_by(user_id=user_id).group_by(PublishHistory.platform).all()

        return {
            'total': total,
            'success': success,
            'failed': total - success,
            'by_platform': dict(platform_stats)
        }
    finally:
        db.close()
```

### 3. 添加重试机制

对于失败的发布,可以添加重新发布功能:

```python
def retry_publish(self, history_id):
    """重试发布"""
    db = get_db_session()
    try:
        # 获取历史记录
        history = db.query(PublishHistory).filter_by(id=history_id).first()

        if not history or history.status == 'success':
            return {'error': '无需重试'}

        # 获取文章信息
        article = history.article

        # 根据平台重新发布
        if history.platform == '知乎':
            return self.publish_to_zhihu(
                user_id=history.user_id,
                account_id=history.account_id,
                article_id=article.id,
                title=article.title,
                content=article.content
            )
    finally:
        db.close()
```

## 文件清单

相关代码文件:

1. **backend/models.py** - 数据库模型定义
   - `PublishHistory` 类 (第181-212行)

2. **backend/services/publish_service.py** - 发布服务
   - `publish_to_zhihu()` - 发布到知乎
   - `get_publish_history()` - 获取历史
   - `_save_publish_history()` - 保存历史

3. **backend/blueprints/api.py** - API端点
   - `POST /api/publish_zhihu` (第225-262行)
   - `GET /api/publish_history` (第335-361行)

4. **scripts/test/test_publish_history_api.py** - 测试脚本

## 总结

发布历史记录功能已完全集成到系统中:

✓ 数据库模型已定义 (PublishHistory表)
✓ 自动记录发布历史 (成功/失败)
✓ 支持查询历史记录 (带平台筛选)
✓ API端点已实现并测试
✓ 关联查询文章信息
✓ 优化的数据库索引
✓ 级联删除支持

每次用户发布文章时,系统会自动:
1. 调用平台发布API
2. 记录发布结果到数据库
3. 保存发布状态、URL、时间等信息
4. 用户可以随时查询历史记录
