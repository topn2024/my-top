# 知乎自动发帖功能 - 使用说明

## 功能概述

已为TopN项目集成完整的知乎自动发帖功能,包括:
1. 发布文章到知乎
2. 回答知乎问题
3. 将已生成的文章一键发布到知乎

---

## 部署步骤

### 1. 部署自动发帖模块

```bash
cd D:\work\code\TOP_N
python deploy_auto_post.py
```

这将自动完成:
- 上传 `zhihu_auto_post.py` 到服务器
- 在 `app_with_upload.py` 中添加3个新API接口
- 重启服务

---

## API接口说明

### 1. POST /api/zhihu/post - 发布文章

**请求示例**:
```bash
curl -X POST http://39.105.12.124:8080/api/zhihu/post \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_zhihu_account",
    "title": "Python自动化最佳实践",
    "content": "本文介绍Python自动化的最佳实践...\n\n第一部分...\n\n第二部分...",
    "topics": ["Python", "编程", "自动化"],
    "draft": false
  }'
```

**参数说明**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 知乎账号(对应Cookie文件名) |
| title | string | 是 | 文章标题 |
| content | string | 是 | 文章内容(支持换行) |
| topics | array | 否 | 话题标签列表 |
| draft | boolean | 否 | true=保存草稿, false=直接发布 |

**响应示例**:
```json
{
  "success": true,
  "message": "文章发布成功",
  "type": "published",
  "url": "https://zhuanlan.zhihu.com/p/123456789"
}
```

---

### 2. POST /api/zhihu/answer - 回答问题

**请求示例**:
```bash
curl -X POST http://39.105.12.124:8080/api/zhihu/answer \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_zhihu_account",
    "question_url": "https://www.zhihu.com/question/12345678",
    "content": "这是一个详细的回答..."
  }'
```

**参数说明**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 知乎账号 |
| question_url | string | 是 | 问题链接 |
| content | string | 是 | 回答内容 |

---

### 3. POST /api/articles/publish_to_zhihu/{article_id} - 发布已生成文章

**请求示例**:
```bash
curl -X POST http://39.105.12.124:8080/api/articles/publish_to_zhihu/1 \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_zhihu_account",
    "topics": ["AI", "机器学习"],
    "draft": false
  }'
```

**参数说明**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 知乎账号 |
| topics | array | 否 | 话题标签 |
| draft | boolean | 否 | 是否保存为草稿 |

---

## 使用流程

### 步骤1: 扫码登录保存Cookie

1. 访问账号配置页面: `http://39.105.12.124:8080`
2. 添加知乎账号
3. 点击"测试"按钮
4. 弹出二维码,用知乎App扫码
5. 在手机上确认登录
6. 登录成功后,Cookie自动保存到服务器

Cookie保存位置:
```
/home/u_topn/TOP_N/backend/cookies/zhihu_{username}.json
```

---

### 步骤2: 发布文章

#### 方式A: 直接通过API发布

```python
import requests

# 发布文章
response = requests.post(
    'http://39.105.12.124:8080/api/zhihu/post',
    json={
        'username': 'your_account',
        'title': '文章标题',
        'content': '''这是文章内容...

可以包含多个段落...

支持换行''',
        'topics': ['Python', 'AI'],
        'draft': False
    }
)

result = response.json()
print(result)
# {'success': True, 'url': '...'}
```

#### 方式B: 发布TopN生成的文章

```python
# 假设文章ID为1
response = requests.post(
    'http://39.105.12.124:8080/api/articles/publish_to_zhihu/1',
    json={
        'username': 'your_account',
        'topics': ['技术'],
        'draft': False
    }
)
```

---

## 核心模块说明

### zhihu_auto_post.py

**主要类**: `ZhihuAutoPost`

**核心方法**:

1. `init_browser()` - 初始化DrissionPage浏览器
2. `load_cookies(username)` - 从文件加载Cookie并登录
3. `verify_login()` - 验证登录状态
4. `create_article(title, content, topics, draft)` - 创建文章
5. `create_answer(question_url, content)` - 回答问题
6. `close()` - 关闭浏览器

**便捷函数**:
```python
from zhihu_auto_post import post_article_to_zhihu

result = post_article_to_zhihu(
    username='your_account',
    title='标题',
    content='内容',
    topics=['话题'],
    draft=False
)
```

---

## 工作原理

### 1. Cookie登录流程
```
加载Cookie文件
    ↓
访问知乎主页
    ↓
设置Cookie到浏览器
    ↓
刷新页面
    ↓
验证登录状态
```

### 2. 文章发布流程
```
访问创作页面
https://zhuanlan.zhihu.com/write
    ↓
等待编辑器加载
    ↓
输入标题
    ↓
输入正文(多段落)
    ↓
添加话题标签
    ↓
点击发布/保存草稿
    ↓
获取文章链接
```

### 3. 元素定位策略

**标题输入框**:
- 主选择器: `css:.WriteIndex-titleInput`
- 备选: `css:textarea[placeholder*="标题"]`

**正文编辑器**:
- 优先: `css:.public-DraftEditor-content`
- 备选: `css:[contenteditable="true"]`
- 备选: `css:.notranslate`
- 备选: `css:[data-text="true"]`

**发布按钮**:
- `text:发布文章`
- `text:发布`
- `css:button.PublishButton`

---

## 内容格式

### 支持的内容格式

1. **纯文本**
```
这是一篇文章

包含多个段落

每个段落之间用空行分隔
```

2. **带换行的文本**
```python
content = """第一段内容

第二段内容

第三段内容"""
```

3. **后续可扩展**: Markdown, HTML

---

## 故障排除

### Q1: 发布失败,提示"未登录"
**A**: Cookie可能过期,重新扫码登录

### Q2: 找不到编辑器元素
**A**: 知乎界面可能更新,检查日志中的选择器信息

### Q3: 文章发布后看不到
**A**:
- 检查是否保存为草稿(draft=true)
- 草稿位置: 知乎 → 创作中心 → 草稿箱

### Q4: Cookie文件不存在
**A**:
```bash
# 检查Cookie文件
ssh u_topn@39.105.12.124
ls -l /home/u_topn/TOP_N/backend/cookies/
```

### Q5: 浏览器无法启动
**A**: 检查DrissionPage是否正确安装
```bash
ssh u_topn@39.105.12.124
python3 -c "from DrissionPage import ChromiumPage; print('OK')"
```

---

## 日志查看

### 查看发帖日志
```bash
# 实时查看
ssh u_topn@39.105.12.124
sudo journalctl -u topn -f | grep -i zhihu

# 查看最近日志
sudo journalctl -u topn -n 100 --no-pager | grep -i zhihu
```

### 日志级别说明
- `✓` - 操作成功
- `✓✓` - 重要成功(发布成功等)
- `⚠` - 警告
- `✗` - 错误

---

## 性能优化建议

### 1. 批量发布
如果需要发布多篇文章,建议:
- 复用同一个浏览器实例
- 不要频繁关闭/打开浏览器

### 2. 无头模式
生产环境可设置 `headless=True`:
```python
co.headless(True)  # 不显示浏览器窗口
```

### 3. 发布间隔
建议两次发布间隔 ≥ 30秒,避免被限流

---

## 扩展功能建议

### 1. 定时发布
结合cron实现定时发布:
```bash
# 每天10点发布
0 10 * * * curl -X POST http://localhost:8080/api/articles/publish_to_zhihu/1 ...
```

### 2. 批量发布
创建批量发布脚本:
```python
article_ids = [1, 2, 3, 4, 5]
for article_id in article_ids:
    # 发布文章
    time.sleep(60)  # 间隔1分钟
```

### 3. 发布队列
使用Celery等任务队列:
- 异步发布
- 失败重试
- 任务管理

---

## 安全注意事项

1. **Cookie保护**: Cookie文件包含登录凭证,注意权限控制
2. **频率限制**: 避免短时间大量发布,可能被知乎限制
3. **内容审核**: 发布前确保内容符合知乎社区规范
4. **账号安全**: 建议使用专门的营销账号,而非主账号

---

## 测试示例

### 测试脚本
```python
#!/usr/bin/env python3
import requests
import time

BASE_URL = 'http://39.105.12.124:8080'

def test_post_article():
    """测试发布文章"""
    print("测试发布文章...")

    response = requests.post(
        f'{BASE_URL}/api/zhihu/post',
        json={
            'username': 'test_account',  # 替换为实际账号
            'title': f'测试文章 - {time.strftime("%Y%m%d%H%M%S")}',
            'content': '''这是一篇测试文章。

本文用于测试自动发帖功能。

测试时间: ''' + time.strftime("%Y-%m-%d %H:%M:%S"),
            'topics': ['测试'],
            'draft': True  # 保存为草稿,不公开发布
        }
    )

    result = response.json()
    print(f"结果: {result}")

    if result.get('success'):
        print("✓ 测试成功!")
    else:
        print(f"✗ 测试失败: {result.get('message')}")

if __name__ == '__main__':
    test_post_article()
```

---

## 总结

知乎自动发帖功能现已完全集成到TopN项目中:

- ✅ 二维码登录保存Cookie
- ✅ Cookie自动加载登录
- ✅ 自动发布文章
- ✅ 自动回答问题
- ✅ 一键发布TopN生成的文章
- ✅ REST API接口
- ✅ 完整的错误处理和日志

**下一步**:
1. 测试二维码扫码登录
2. 验证Cookie保存成功
3. 使用API发布测试文章
4. 根据实际效果优化选择器
