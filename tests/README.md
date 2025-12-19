# 🧪 TOP_N 完整测试套件

## 测试架构概览

```
tests/
├── unit/               # 单元测试
│   ├── test_models.py
│   ├── test_auth.py
│   └── test_services.py
├── integration/        # 集成测试
│   ├── test_api_integration.py
│   └── test_database_integration.py
├── e2e/               # 端到端测试
│   ├── test_user_workflows.py
│   └── test_publishing_workflows.py
├── api/               # API接口测试
│   ├── test_auth_api.py
│   ├── test_article_api.py
│   ├── test_workflow_api.py
│   └── test_publish_api.py
├── ui/                # 前端UI测试
│   ├── test_login_page.py
│   ├── test_analysis_page.py
│   └── test_dashboard.py
├── fixtures/          # 测试数据
│   ├── test_users.json
│   ├── test_articles.json
│   └── test_workflows.json
├── utils/             # 测试工具
│   ├── test_helpers.py
│   ├── api_client.py
│   ├── ui_helpers.py
│   └── database_helpers.py
├── reports/           # 测试报告
│   ├── templates/
│   └── archives/
├── config/            # 测试配置
│   ├── test_config.py
│   └── environments.json
├── requirements.txt   # 测试依赖
├── conftest.py       # pytest配置
├── run_all_tests.py  # 主测试运行器
└── generate_report.py # 报告生成器
```

## 测试类型说明

### 1. 单元测试 (unit/)
- 测试单个函数、类、模块
- 快速执行，隔离性强
- 覆盖核心业务逻辑

### 2. 集成测试 (integration/)
- 测试多个组件协同工作
- 数据库集成测试
- API与服务层集成

### 3. API接口测试 (api/)
- 完整的HTTP API测试
- 请求/响应验证
- 状态码和错误处理测试

### 4. 前端UI测试 (ui/)
- 用户界面交互测试
- 页面渲染验证
- 用户操作流程测试

### 5. 端到端测试 (e2e/)
- 完整业务流程测试
- 从用户操作到数据库存储的完整链路
- 模拟真实用户场景

## 运行方式

```bash
# 运行所有测试
python tests/run_all_tests.py

# 运行特定类型测试
python tests/run_all_tests.py --type unit
python tests/run_all_tests.py --type api
python tests/run_all_tests.py --type ui

# 运行特定测试文件
pytest tests/unit/test_models.py -v

# 生成HTML报告
python tests/generate_report.py --format html

# 运行带覆盖率的测试
python tests/run_all_tests.py --coverage
```

## 测试目标

- **代码覆盖率**: 目标 > 80%
- **API测试覆盖**: 100% API端点覆盖
- **UI测试覆盖**: 主要用户流程全覆盖
- **执行时间**: 全套测试 < 10分钟

## 技术栈

- **后端测试**: pytest + requests + SQLAlchemy测试工具
- **前端测试**: Selenium WebDriver + Chrome/ChromeDriver
- **报告生成**: pytest-html + Allure
- **并发测试**: pytest-xdist
- **模拟数据**: Faker + factory_boy
- **API测试**: requests + responses