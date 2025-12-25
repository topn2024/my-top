# 提示词模板系统 - 快速部署指南

## 当前状态

✅ **已完成**:
- 数据库模型设计（5个新表）
- 数据库初始化脚本
- 预置数据（14个分类 + 2个样例）
- 管理员账号创建（admin / TopN@2024）

⏳ **待完成**:
- 服务层实现
- API接口
- 管理界面
- 前端集成

---

## 快速部署步骤

### 步骤1：初始化数据库（已完成）

```bash
cd D:/code/TOP_N/backend
python init_prompt_template_system_fixed.py
```

### 步骤2：提交当前代码到Git

```bash
cd D:/code/TOP_N
git add -A
git commit -m "Add prompt template system - database layer complete"
git push origin main
```

### 步骤3：部署到服务器

```bash
# 从本地上传到服务器
scp -r D:/code/TOP_N/* u_topn@39.105.12.124:/home/u_topn/TOP_N/

# SSH到服务器
ssh u_topn@39.105.12.124

# 在服务器上初始化数据库
cd /home/u_topn/TOP_N/backend
python3.14 init_prompt_template_system_fixed.py

# 重启服务
pkill -9 -f 'gunicorn.*app'
cd /home/u_topn/TOP_N/backend
nohup python3.14 -m gunicorn --config ../gunicorn_config.py app_factory:app > ../logs/gunicorn.log 2>&1 &
```

---

## 最小可用版本（MVP）实施

由于完整实施需要大量代码，建议分阶段实施：

### Phase 1: 数据库层 ✅ **（已完成）**
- ✅ 数据库模型
- ✅ 初始化脚本
- ✅ 预置数据

### Phase 2: 核心API（简化版）
创建基本的CRUD接口，让管理员可以通过API管理模板：

**文件**: `backend/blueprints/prompt_template_api_simple.py`

```python
from flask import Blueprint, jsonify, request
from models import SessionLocal
from models_prompt_template import PromptTemplate, PromptTemplateCategory, PromptExampleLibrary

bp = Blueprint('prompt_templates', __name__, url_prefix='/api/prompt-templates')

@bp.route('/templates', methods=['GET'])
def list_templates():
    """列出所有模板"""
    session = SessionLocal()
    try:
        templates = session.query(PromptTemplate).filter_by(status='active').all()
        return jsonify([t.to_dict(include_prompts=False) for t in templates])
    finally:
        session.close()

@bp.route('/templates/<int:template_id>', methods=['GET'])
def get_template(template_id):
    """获取模板详情"""
    session = SessionLocal()
    try:
        template = session.query(PromptTemplate).get(template_id)
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        return jsonify(template.to_dict())
    finally:
        session.close()

@bp.route('/categories', methods=['GET'])
def list_categories():
    """列出所有分类"""
    session = SessionLocal()
    try:
        categories = session.query(PromptTemplateCategory).all()
        return jsonify([c.to_dict() for c in categories])
    finally:
        session.close()

@bp.route('/examples', methods=['GET'])
def list_examples():
    """列出所有样例"""
    session = SessionLocal()
    try:
        examples = session.query(PromptExampleLibrary).all()
        return jsonify([e.to_dict() for e in examples])
    finally:
        session.close()
```

### Phase 3: 注册蓝图到主应用

修改 `backend/app_factory.py`，添加：

```python
from blueprints.prompt_template_api_simple import bp as prompt_template_bp
app.register_blueprint(prompt_template_bp)
```

### Phase 4: 验证功能

```bash
# 测试API
curl http://localhost:3001/api/prompt-templates/templates
curl http://localhost:3001/api/prompt-templates/categories
curl http://localhost:3001/api/prompt-templates/examples
```

---

## 完整实施方案

完整实施需要以下文件（约20个文件，2000+行代码）：

### 服务层（3个文件）
1. `backend/services/prompt_template_service.py` (~500 lines)
2. `backend/services/prompt_template_matcher.py` (~300 lines)
3. `backend/services/example_library_service.py` (~200 lines)

### API层（3个文件）
4. `backend/blueprints/admin_template_api.py` (~600 lines)
5. `backend/blueprints/template_api.py` (~400 lines)
6. `backend/blueprints/example_library_api.py` (~300 lines)

### 前端界面（8个文件）
7. `templates/admin/template_list.html` (~300 lines)
8. `templates/admin/template_edit.html` (~500 lines)
9. `templates/admin/category_manage.html` (~200 lines)
10. `templates/admin/example_library.html` (~300 lines)
11. `static/js/template_management.js` (~600 lines)
12. `static/js/template_editor.js` (~400 lines)
13. `static/js/example_browser.js` (~300 lines)
14. `static/css/template_admin.css` (~200 lines)

### 集成修改（4个文件）
15. 修改 `templates/input.html` - 添加模板选择
16. 修改 `backend/blueprints/api.py` - 集成模板功能
17. 修改 `backend/services/ai_service.py` - 支持模板化提示词
18. 修改 `static/app.js` - 前端模板选择逻辑

---

## 当前可以做的事情

虽然完整功能未实现，但数据库层已就绪，可以：

1. **直接操作数据库**创建模板
2. **使用SQL**管理模板和样例
3. **准备模板内容**，待API完成后批量导入

### 示例：通过SQL创建模板

```sql
-- 创建一个简单的模板
INSERT INTO prompt_templates (
    name, code, prompts, industry_tags, platform_tags,
    keywords, ai_config, version, status, description, created_at
) VALUES (
    'Tech Company - Zhihu Template',
    'tech_zhihu_v1',
    '{"analysis": {"system": "You are a tech analyst...", "user_template": "Analyze {{company_name}}..."},
      "article_generation": {"system": "You are a Zhihu writer...", "user_template": "Write about {{company_name}}..."}}',
    '["tech", "ai"]',
    '["zhihu"]',
    '["AI", "cloud", "tech"]',
    '{"temperature": 0.8, "max_tokens": 3000}',
    '1.0',
    'active',
    'Template for tech companies on Zhihu platform',
    datetime('now')
);
```

---

## 推荐实施路径

### 方案A：立即可用（当前状态）
- ✅ 数据库已就绪
- 部署到服务器
- 手动通过SQL管理模板
- 等待完整功能开发

### 方案B：最小API（+2小时）
- 实现基本CRUD API
- 使用Postman/curl管理模板
- 无UI界面
- 可以开始使用模板功能

### 方案C：完整系统（+1-2天）
- 完整服务层
- 完整API
- 管理界面
- 用户界面集成
- 全功能可用

---

## 联系与支持

如需继续完成实施，请告知选择哪个方案。

当前已提交代码包含：
- ✅ 数据库模型
- ✅ 初始化脚本
- ✅ 设计文档
- ✅ 预置数据

可以在此基础上继续开发。

---

**最后更新**: 2025-12-13
**状态**: 数据库层完成，待实施服务层和界面
