# 服务层使用示例

本文档提供重构后服务层的详细使用示例。

## 初始化服务

```python
from config import get_config
from services.file_service import FileService
from services.ai_service import AIService
from services.account_service import AccountService
from services.workflow_service import WorkflowService
from services.publish_service import PublishService

# 获取配置
config = get_config('production')
config.init_app()  # 初始化目录

# 初始化服务
file_service = FileService(config)
ai_service = AIService(config)
account_service = AccountService(config)
workflow_service = WorkflowService()
publish_service = PublishService(config)
```

## 文件服务使用示例

### 1. 文件上传

```python
from flask import request

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    file = request.files.get('file')

    # 保存文件
    success, message, filepath = file_service.save_file(file)

    if not success:
        return jsonify({'error': message}), 400

    # 提取文本
    text = file_service.extract_text(filepath)

    return jsonify({
        'success': True,
        'message': message,
        'text': text,
        'filename': file.filename
    })
```

### 2. 文件验证

```python
# 检查文件类型
if file_service.allowed_file('document.pdf'):
    print('PDF文件允许上传')

# 验证文件
is_valid, error_msg = file_service.validate_file(file)
if not is_valid:
    return jsonify({'error': error_msg}), 400
```

### 3. 文件删除

```python
# 删除文件
success = file_service.delete_file('/path/to/file.txt')
if success:
    print('文件删除成功')
```

## AI服务使用示例

### 1. 公司分析

```python
@app.route('/api/analyze', methods=['POST'])
@login_required
def analyze_company():
    data = request.json
    user = get_current_user()

    try:
        # 调用AI分析
        analysis = ai_service.analyze_company(
            company_name=data.get('company_name'),
            company_desc=data.get('company_desc'),
            uploaded_text=data.get('uploaded_text', '')
        )

        # 保存到工作流
        workflow = workflow_service.save_workflow(
            user_id=user.id,
            workflow_id=data.get('workflow_id'),
            data={
                'company_name': data.get('company_name'),
                'analysis': analysis,
                'current_step': 2
            }
        )

        return jsonify({
            'success': True,
            'analysis': analysis,
            'workflow_id': workflow['workflow'].id
        })

    except Exception as e:
        logger.error(f'Analysis failed: {e}')
        return jsonify({'error': str(e)}), 500
```

### 2. 生成文章

```python
@app.route('/api/generate_articles', methods=['POST'])
@login_required
def generate_articles():
    data = request.json
    user = get_current_user()

    try:
        # 生成文章
        articles = ai_service.generate_articles(
            company_name=data.get('company_name'),
            analysis=data.get('analysis'),
            article_count=data.get('article_count', 3)
        )

        # 保存文章
        workflow_service.save_articles(
            user_id=user.id,
            workflow_id=data.get('workflow_id'),
            articles=articles
        )

        return jsonify({
            'success': True,
            'articles': articles
        })

    except Exception as e:
        logger.error(f'Article generation failed: {e}')
        return jsonify({'error': str(e)}), 500
```

### 3. 平台推荐

```python
# 推荐发布平台
platforms = ai_service.recommend_platforms(
    company_name='科技公司',
    analysis='分析结果...',
    articles=[{'title': '标题', 'content': '内容'}]
)

# platforms = [
#     {'name': '知乎', 'reason': '适合技术文章'},
#     {'name': 'CSDN', 'reason': '程序员社区'},
#     ...
# ]
```

## 账号服务使用示例

### 1. 获取账号列表

```python
@app.route('/api/accounts', methods=['GET'])
@login_required
def get_accounts():
    user = get_current_user()

    try:
        accounts = account_service.get_user_accounts(user.id)
        return jsonify({
            'success': True,
            'accounts': accounts
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### 2. 添加账号

```python
@app.route('/api/accounts', methods=['POST'])
@login_required
def add_account():
    data = request.json
    user = get_current_user()

    try:
        result = account_service.add_account(
            user_id=user.id,
            platform=data.get('platform'),
            username=data.get('username'),
            password=data.get('password'),
            config=data.get('config')
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### 3. 删除账号

```python
@app.route('/api/accounts/<int:account_id>', methods=['DELETE'])
@login_required
def delete_account(account_id):
    user = get_current_user()

    try:
        success = account_service.delete_account(user.id, account_id)

        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': '账号不存在'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### 4. 获取带密码的账号（用于发布）

```python
# 获取账号信息（包含解密后的密码）
account = account_service.get_account_with_password(user_id, account_id)

if account:
    username = account['username']
    password = account['password']  # 已解密
    # 使用账号信息进行发布...
```

## 工作流服务使用示例

### 1. 获取当前工作流

```python
@app.route('/api/workflow/current', methods=['GET'])
@login_required
def get_current_workflow():
    user = get_current_user()

    workflow = workflow_service.get_current_workflow(user.id)

    if workflow:
        return jsonify({'success': True, 'workflow': workflow})
    else:
        return jsonify({'success': True, 'workflow': None})
```

### 2. 保存工作流

```python
@app.route('/api/workflow/save', methods=['POST'])
@login_required
def save_workflow():
    data = request.json
    user = get_current_user()

    try:
        result = workflow_service.save_workflow(
            user_id=user.id,
            workflow_id=data.get('workflow_id'),
            data={
                'company_name': data.get('company_name'),
                'company_desc': data.get('company_desc'),
                'analysis': data.get('analysis'),
                'current_step': data.get('current_step')
            }
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### 3. 获取工作流列表

```python
# 获取用户最近的10个工作流
workflows = workflow_service.get_workflow_list(user_id=user.id, limit=10)

for workflow in workflows:
    print(f"公司: {workflow['company_name']}")
    print(f"步骤: {workflow['current_step']}")
    print(f"更新时间: {workflow['updated_at']}")
```

## 发布服务使用示例

### 1. 发布到知乎

```python
@app.route('/api/publish_zhihu', methods=['POST'])
@login_required
def publish_to_zhihu():
    data = request.json
    user = get_current_user()

    try:
        result = publish_service.publish_to_zhihu(
            user_id=user.id,
            account_id=data.get('account_id'),
            title=data.get('title'),
            content=data.get('content')
        )

        return jsonify(result)

    except Exception as e:
        logger.error(f'Publish failed: {e}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

### 2. 获取发布历史

```python
@app.route('/api/publish/history', methods=['GET'])
@login_required
def get_publish_history():
    user = get_current_user()

    try:
        history = publish_service.get_publish_history(
            user_id=user.id,
            limit=20
        )

        return jsonify({
            'success': True,
            'history': history
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

## 组合使用示例

### 完整的工作流程

```python
@app.route('/api/complete_workflow', methods=['POST'])
@login_required
def complete_workflow():
    """完整的工作流：上传 -> 分析 -> 生成 -> 发布"""
    user = get_current_user()
    data = request.json

    try:
        # 1. 文件处理（如果有）
        if 'file' in request.files:
            file = request.files['file']
            success, message, filepath = file_service.save_file(file)
            if success:
                uploaded_text = file_service.extract_text(filepath)
            else:
                uploaded_text = ''
        else:
            uploaded_text = ''

        # 2. AI分析
        analysis = ai_service.analyze_company(
            company_name=data.get('company_name'),
            company_desc=data.get('company_desc'),
            uploaded_text=uploaded_text
        )

        # 3. 创建工作流
        workflow_result = workflow_service.save_workflow(
            user_id=user.id,
            workflow_id=None,
            data={
                'company_name': data.get('company_name'),
                'company_desc': data.get('company_desc'),
                'uploaded_text': uploaded_text,
                'analysis': analysis,
                'current_step': 2
            }
        )
        workflow_id = workflow_result['workflow']['id']

        # 4. 生成文章
        articles = ai_service.generate_articles(
            company_name=data.get('company_name'),
            analysis=analysis,
            article_count=3
        )

        # 5. 保存文章
        workflow_service.save_articles(
            user_id=user.id,
            workflow_id=workflow_id,
            articles=articles
        )

        # 6. 推荐平台
        platforms = ai_service.recommend_platforms(
            company_name=data.get('company_name'),
            analysis=analysis,
            articles=articles
        )

        return jsonify({
            'success': True,
            'workflow_id': workflow_id,
            'analysis': analysis,
            'articles': articles,
            'platforms': platforms
        })

    except Exception as e:
        logger.error(f'Complete workflow failed: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500
```

## 错误处理模式

### 统一错误处理

```python
from functools import wraps

def handle_service_errors(f):
    """服务层错误处理装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.warning(f'Validation error: {e}')
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f'Service error: {e}', exc_info=True)
            return jsonify({'error': '服务器错误'}), 500
    return decorated_function

@app.route('/api/example')
@login_required
@handle_service_errors
def example():
    # 业务逻辑
    result = some_service.do_something()
    return jsonify({'success': True, 'data': result})
```

## 日志记录模式

```python
import logging

logger = logging.getLogger(__name__)

@app.route('/api/example')
@login_required
def example():
    user = get_current_user()
    logger.info(f'User {user.id} started operation')

    try:
        result = some_service.operation()
        logger.info(f'Operation completed for user {user.id}')
        return jsonify({'success': True, 'data': result})

    except Exception as e:
        logger.error(f'Operation failed for user {user.id}: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500
```

## 性能优化

### 使用缓存

```python
from functools import lru_cache

class AIService:
    @lru_cache(maxsize=100)
    def analyze_company(self, company_name, company_desc):
        """带缓存的分析（相同输入直接返回缓存结果）"""
        ...
```

### 批量操作

```python
# 批量添加账号
accounts_data = [
    {'platform': '知乎', 'username': 'user1', 'password': 'pass1'},
    {'platform': 'CSDN', 'username': 'user2', 'password': 'pass2'},
]

for account_data in accounts_data:
    account_service.add_account(user.id, **account_data)
```

---

**文档版本**: 1.0
**创建日期**: 2025-12-08
