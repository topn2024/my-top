# 智谱 AI 迁移说明

## 更新日期
2025-12-12

## 更新内容

已将 TOP_N 项目的默认 AI 服务从**千问 AI**迁移到**智谱 AI (GLM-4)**。

---

## 配置变更

### 1. 配置文件更新

**文件**: `backend/config.py`

新增智谱 AI 配置项：

```python
# 智谱 AI 配置
ZHIPU_API_KEY = os.environ.get('ZHIPU_API_KEY', '')
ZHIPU_API_BASE = 'https://open.bigmodel.cn/api/paas/v4'
ZHIPU_CHAT_URL = f'{ZHIPU_API_BASE}/chat/completions'
ZHIPU_MODEL = 'glm-4-flash'  # 可选: glm-4, glm-4-flash, glm-4-plus

# 默认 AI 服务商
DEFAULT_AI_PROVIDER = os.environ.get('AI_PROVIDER', 'zhipu')
```

**千问配置保留作为备用**，可通过环境变量切换。

### 2. AI 服务更新

**文件**: `backend/services/ai_service.py`

- `AIService` 类现在支持多 AI 服务商
- 根据配置自动选择智谱 AI 或千问 AI
- 日志信息会显示当前使用的 AI 服务商

---

## 智谱 AI 模型说明

### 可用模型

| 模型名称 | 特点 | 推荐场景 |
|---------|------|---------|
| **glm-4-flash** | 快速、成本低 | 日常文章生成、快速分析 |
| **glm-4** | 平衡性能和成本 | 标准业务场景 |
| **glm-4-plus** | 高质量输出 | 重要文档、高质量要求 |

**当前默认**: `glm-4-flash`

### 修改默认模型

编辑 `backend/config.py`：

```python
ZHIPU_MODEL = 'glm-4'  # 改为你想要的模型
```

---

## 如何获取智谱 API Key

### 方法 1: 官网注册

1. 访问智谱 AI 开放平台：https://open.bigmodel.cn/
2. 注册/登录账号
3. 进入"API 管理" → "生成 API Key"
4. 复制 API Key

### 方法 2: 使用现有 Key

如果已有智谱 API Key，直接配置即可。

---

## 配置 API Key

### 本地开发环境

**Windows (PowerShell):**
```powershell
$env:ZHIPU_API_KEY="your-api-key-here"
```

**Windows (CMD):**
```cmd
set ZHIPU_API_KEY=your-api-key-here
```

**Linux/Mac (Bash):**
```bash
export ZHIPU_API_KEY='your-api-key-here'
```

### 永久配置（推荐）

**创建 `.env` 文件**（项目根目录）：

```bash
# .env
ZHIPU_API_KEY=your-api-key-here
AI_PROVIDER=zhipu
```

**或修改系统环境变量**：

**Windows:**
1. 右键"此电脑" → "属性" → "高级系统设置"
2. "环境变量" → "新建"
3. 变量名: `ZHIPU_API_KEY`
4. 变量值: 你的 API Key

**Linux/Mac (添加到 ~/.bashrc 或 ~/.zshrc):**
```bash
echo 'export ZHIPU_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### 服务器部署

**SSH 到服务器后配置:**

```bash
ssh topn

# 编辑用户环境变量
echo 'export ZHIPU_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc

# 或者在启动脚本中设置
cd /home/u_topn/TOP_N
# 编辑启动脚本，添加环境变量
```

---

## 切换 AI 服务商

### 切换到千问 AI

设置环境变量：

```bash
export AI_PROVIDER=qianwen
```

或在代码中修改 `backend/config.py`：

```python
DEFAULT_AI_PROVIDER = 'qianwen'
```

### 切换到智谱 AI（默认）

```bash
export AI_PROVIDER=zhipu
```

---

## 测试配置

### 运行配置测试脚本

```bash
cd D:\code\TOP_N
python test_zhipu_config.py
```

**预期输出:**

```
============================================================
AI Configuration Test
============================================================

[1] Default AI Provider:
    Provider: zhipu

[2] Zhipu AI Configuration:
    API Base: https://open.bigmodel.cn/api/paas/v4
    Chat URL: https://open.bigmodel.cn/api/paas/v4/chat/completions
    Model: glm-4-flash
    API Key: SET

[4] AIService Provider Selection:
    Active Provider: ZHIPU
    Active Model: glm-4-flash
    API Endpoint: https://open.bigmodel.cn/api/paas/v4/chat/completions
    API Key Status: SET

============================================================
[OK] All configurations are valid!
============================================================
```

---

## API 兼容性说明

### OpenAI 兼容接口

智谱 AI 提供 **OpenAI 兼容接口**，因此现有代码**无需修改**：

- 请求格式相同
- 响应格式相同
- 参数名称相同（`messages`, `temperature`, `max_tokens` 等）

### 主要差异

1. **API Base URL**:
   - 千问: `https://dashscope.aliyuncs.com/compatible-mode/v1`
   - 智谱: `https://open.bigmodel.cn/api/paas/v4`

2. **模型名称**:
   - 千问: `qwen-plus`, `qwen-turbo`
   - 智谱: `glm-4`, `glm-4-flash`, `glm-4-plus`

3. **API Key 格式**:
   - 两者都使用 Bearer Token 认证
   - 格式略有不同，但使用方式相同

---

## 功能验证

### 验证文章分析功能

```python
from backend.config import Config
from backend.services.ai_service import AIService

config = Config()
ai_service = AIService(config)

# 测试分析
result = ai_service.analyze_company(
    company_name="示例公司",
    company_desc="这是一家科技公司"
)
print(result)
```

### 验证文章生成功能

```python
# 测试生成文章
articles = ai_service.generate_articles(
    company_name="示例公司",
    analysis="示例分析结果",
    article_count=3
)
for article in articles:
    print(f"标题: {article['title']}")
    print(f"类型: {article['type']}")
```

---

## 成本对比

### 智谱 GLM-4 价格（参考）

| 模型 | 输入价格 | 输出价格 |
|------|---------|---------|
| glm-4-flash | ¥0.001/千tokens | ¥0.001/千tokens |
| glm-4 | ¥0.01/千tokens | ¥0.01/千tokens |
| glm-4-plus | ¥0.05/千tokens | ¥0.05/千tokens |

### 千问价格（参考）

| 模型 | 输入价格 | 输出价格 |
|------|---------|---------|
| qwen-plus | ¥0.004/千tokens | ¥0.012/千tokens |
| qwen-turbo | ¥0.002/千tokens | ¥0.006/千tokens |

**智谱 glm-4-flash** 成本更低，适合高频次调用。

---

## 迁移检查清单

- [x] 更新 `backend/config.py` 添加智谱配置
- [x] 更新 `backend/services/ai_service.py` 支持多服务商
- [x] 设置默认 AI 服务商为智谱
- [x] 创建配置测试脚本
- [ ] **获取智谱 API Key**
- [ ] **配置环境变量 `ZHIPU_API_KEY`**
- [ ] 运行 `test_zhipu_config.py` 验证配置
- [ ] 测试文章分析功能
- [ ] 测试文章生成功能
- [ ] 部署到服务器并配置环境变量

---

## 故障排查

### 问题 1: API Key 未设置

**现象:**
```
[WARNING] Zhipu API key is not set (empty string)
```

**解决:**
```bash
export ZHIPU_API_KEY='your-api-key-here'
```

### 问题 2: API 调用失败

**检查步骤:**

1. 验证 API Key 是否正确
2. 检查网络连接
3. 查看日志文件 `logs/gunicorn_error.log`

**切换回千问 AI（临时方案）:**
```bash
export AI_PROVIDER=qianwen
```

### 问题 3: 模型不支持

**现象:**
```
Model 'glm-4-xxx' not found
```

**解决:**

检查模型名称是否正确，修改 `backend/config.py`:
```python
ZHIPU_MODEL = 'glm-4-flash'  # 使用支持的模型
```

---

## 回滚方案

如需回滚到千问 AI：

### 临时回滚（不修改代码）

```bash
export AI_PROVIDER=qianwen
```

重启应用即可。

### 永久回滚（修改代码）

编辑 `backend/config.py`:

```python
DEFAULT_AI_PROVIDER = 'qianwen'  # 改回 qianwen
```

提交代码并重新部署。

---

## 相关文档

- 智谱 AI 官方文档: https://open.bigmodel.cn/dev/api
- GLM-4 模型介绍: https://open.bigmodel.cn/dev/howuse/model
- API 参考: https://open.bigmodel.cn/dev/api#chatglm

---

## 技术支持

如遇到问题，请检查：

1. 日志文件: `logs/gunicorn_error.log`
2. 运行测试脚本: `python test_zhipu_config.py`
3. 验证 API Key 有效性

---

**迁移状态**: ✅ 代码已更新，等待配置 API Key

**下一步**: 获取智谱 API Key 并配置到环境变量中
