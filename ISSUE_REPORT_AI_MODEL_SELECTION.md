# AI模型选择被忽略问题报告

## 问题标识
**问题ID**: AI_MODEL_SELECTION_IGNORED
**发现日期**: 2025-12-15
**严重程度**: 中（功能缺失，用户体验差）
**影响范围**: 公司分析功能
**状态**: ✅ 已修复

## 问题描述

### 用户反馈
> "文章分析我都已经选择了智谱plus模型，后台执行的时候仍然调用智谱flash模型。这个问题不是已经改过了吗，怎么又出现了"

### 现象
用户在分析页面选择了 AI 模型（如智谱 GLM-4-Plus），但后台在进行**公司分析**时仍然使用默认模型（智谱 GLM-4-Flash）。

### 实际影响
- 用户无法为公司分析步骤选择高级模型
- 只有文章生成步骤才使用用户选择的模型
- 导致分析质量不符合用户预期

## 根本原因分析

### 工作流程分析

系统的完整工作流程：
```
1. 输入页面 (input.html)
   → 提交公司信息

2. API调用 (/api/analyze)
   → 进行公司分析 ← 【问题点：这里没有模型选择】

3. 分析页面 (analysis.html)
   → 显示分析结果
   → 用户选择AI模型 ← 【模型选择器在这里】

4. API调用 (/api/generate_articles)
   → 生成文章 ← 【这里使用了用户选择的模型】
```

### 问题根源

**设计缺陷**：AI 模型选择器只放在了分析页面（第3步），但用户在第1步提交分析时就已经调用了 AI，此时还没有选择模型的机会。

**代码证据**：

#### 前端问题
1. **输入页面没有模型选择器** (`templates/input.html`)
   - 用户提交时无法选择模型
   - 表单提交时不包含 `ai_model` 参数

2. **分析页面才有模型选择器** (`templates/analysis.html`)
   - 选择器在第134-135行
   - 但这时公司分析已经完成了

#### 后端问题
1. **API 不接收模型参数** (`backend/blueprints/api.py:85`)
   ```python
   def analyze_company():
       data = request.json
       # 没有提取 ai_model 参数
       ai_service = AIService(config)
       analysis = ai_service.analyze_company(...)  # 没有传递model参数
   ```

2. **服务方法不支持模型参数**
   - `AIService.analyze_company()` 没有 `model` 参数
   - `AIService.analyze_company_with_template()` 没有 `model` 参数
   - `AIServiceV2.analyze_with_prompt()` 没有 `model` 参数

### 为什么之前"修复"过但又出现？

可能的原因：
1. 之前可能只修复了文章生成部分，没有修复分析部分
2. 或者修复时只改了后端，没有在前端添加选择器
3. 代码回滚或合并冲突导致修复丢失

## 解决方案

### 修复策略
在**输入页面**添加 AI 模型选择器，让用户在提交分析之前就能选择模型。

### 具体修改

#### 1. 前端修改

**文件**: `templates/input.html` (第167-176行)

添加 AI 模型选择器：
```html
<!-- AI模型选择 -->
<div class="form-group">
    <label for="ai-model-select">🤖 AI模型选择</label>
    <select id="ai-model-select" name="ai_model">
        <option value="">加载中...</option>
    </select>
    <div style="margin-top: 5px; font-size: 12px; color: #666;">
        💡 选择用于分析和生成文章的AI模型
    </div>
</div>
```

**文件**: `static/input.js`

1. 添加加载模型函数 (第68-102行)：
```javascript
async function loadAvailableModels() {
    const modelSelect = document.getElementById('ai-model-select');
    if (!modelSelect) return;

    try {
        const response = await fetch('/api/models');
        const data = await response.json();

        if (data.success && data.models) {
            modelSelect.innerHTML = '';
            data.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.id;
                option.textContent = `${model.name} - ${model.description}`;
                if (model.id === data.default) {
                    option.selected = true;
                }
                modelSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading AI models:', error);
        modelSelect.innerHTML = '<option value="">加载失败，使用默认模型</option>';
    }
}
```

2. 页面加载时调用 (第37行)：
```javascript
window.addEventListener('load', () => {
    // ... existing code ...
    loadAvailableModels();
});
```

3. 表单提交时传递模型 (第312-317行)：
```javascript
// 获取选中的AI模型
const aiModelSelect = document.getElementById('ai-model-select');
if (aiModelSelect && aiModelSelect.value) {
    formData.ai_model = aiModelSelect.value;
    console.log('Selected AI model:', aiModelSelect.value);
}
```

#### 2. 后端修改

**文件**: `backend/blueprints/api.py`

1. 提取模型参数 (第100-103行)：
```python
# 获取用户选择的AI模型
ai_model = data.get('ai_model')
if ai_model:
    logger.info(f'User selected AI model: {ai_model}')
```

2. 传递给新系统 (第125行)：
```python
analysis = ai_service_v2.analyze_with_prompt(company_info, analysis_prompt, model=ai_model)
```

3. 传递给旧系统 (第150, 156行)：
```python
# 使用模板
analysis = ai_service.analyze_company_with_template(company_info, template, model=ai_model)

# 不使用模板
analysis = ai_service.analyze_company(
    company_name=data.get('company_name'),
    company_desc=data.get('company_desc', ''),
    uploaded_text=data.get('uploaded_text', ''),
    model=ai_model
)
```

**文件**: `backend/services/ai_service.py`

1. 修改 `analyze_company()` 签名 (第118-119行)：
```python
def analyze_company(self, company_name: str, company_desc: str,
                   uploaded_text: str = '', model: Optional[str] = None) -> str:
```

2. 添加日志和传递参数 (第160-161行)：
```python
logger.info(f'Analyzing company: {company_name}, model: {model or "default"}')
return self._call_api(messages, temperature=0.7, max_tokens=2000, model=model)
```

3. 修改 `analyze_company_with_template()` 签名 (第431行)：
```python
def analyze_company_with_template(self, company_info: Dict, template: Dict, model: Optional[str] = None) -> str:
```

4. 添加日志和传递参数 (第473, 475-479行)：
```python
logger.info(f'Using template for analysis: {template.get("name", "unknown")}, model: {model or "default"}')

return self._call_api(
    messages,
    temperature=ai_config.get('temperature', 0.7),
    max_tokens=ai_config.get('max_tokens', 2000),
    model=model
)
```

**文件**: `backend/services/ai_service_v2.py`

1. 修改 `analyze_with_prompt()` 签名 (第26行)：
```python
def analyze_with_prompt(self, company_info: Dict, analysis_prompt: Dict, model: Optional[str] = None) -> str:
```

2. 添加日志和传递参数 (第53, 55-60行)：
```python
logger.info(f"Using analysis prompt: {analysis_prompt['name']}, model: {model or 'default'}")

return self._call_api(
    messages,
    temperature=analysis_prompt.get('temperature', 0.7),
    max_tokens=analysis_prompt.get('max_tokens', 2000),
    model=model
)
```

### 修复效果

**修复前**：
```
用户在输入页面提交
  ↓
调用 /api/analyze（没有模型参数）
  ↓
使用默认模型进行分析 ← ❌ 用户无法选择
  ↓
跳转到分析页面
  ↓
用户选择模型
  ↓
生成文章（使用用户选择的模型）✅
```

**修复后**：
```
用户在输入页面
  ↓
选择AI模型 ✅
  ↓
提交（包含模型参数）
  ↓
调用 /api/analyze（有模型参数）
  ↓
使用用户选择的模型进行分析 ✅
  ↓
跳转到分析页面
  ↓
生成文章（继续使用同一模型）✅
```

## 测试验证

### 测试步骤

1. **访问输入页面** (http://39.105.12.124/)
   - ✅ 检查是否有"AI模型选择"下拉框
   - ✅ 检查模型列表是否正确加载

2. **选择高级模型**
   - 选择"智谱 GLM-4-Plus"
   - 填写公司信息
   - 点击"开始分析"

3. **检查后台日志**
   ```bash
   ssh u_topn@39.105.12.124 "tail -50 /tmp/topn.log | grep 'User selected AI model'"
   ```
   - 应该看到：`User selected AI model: glm-4-plus`

4. **检查分析调用日志**
   ```bash
   ssh u_topn@39.105.12.124 "tail -50 /tmp/topn.log | grep 'model:'"
   ```
   - 应该看到：`Analyzing company: XXX, model: glm-4-plus`

5. **验证 API 调用**
   - 分析时应该调用智谱 GLM-4-Plus 接口
   - 不再调用默认的 GLM-4-Flash 接口

### 预期结果

- ✅ 输入页面有 AI 模型选择器
- ✅ 模型列表正确加载（包括 Flash、Plus 等）
- ✅ 默认选中配置的默认模型
- ✅ 用户选择的模型正确传递到后端
- ✅ 后端使用用户选择的模型进行分析
- ✅ 日志中记录了用户选择的模型

## 防止措施

### 设计原则

1. **及时选择原则**
   - 需要使用 AI 的地方，在之前就应该有选择器
   - 不要让用户在调用发生后才能选择

2. **一致性原则**
   - 同一个工作流中的所有 AI 调用应该使用相同的模型
   - 用户只需选择一次，应用到整个流程

3. **透明性原则**
   - 明确告知用户模型的选择会影响哪些步骤
   - 在 UI 提示中说明"用于分析和生成文章的AI模型"

### 代码规范

**前端规范**：
```javascript
// ✅ 好的做法：在需要AI的页面提供选择器
<div class="form-group">
    <label for="ai-model-select">🤖 AI模型选择</label>
    <select id="ai-model-select" name="ai_model">...</select>
    <div class="hint">💡 选择用于XXX的AI模型</div>
</div>

// ✅ 提交时传递模型
formData.ai_model = aiModelSelect.value;
```

**后端规范**：
```python
# ✅ 好的做法：所有AI调用方法都支持model参数
def analyze_company(self, company_name: str, company_desc: str,
                   uploaded_text: str = '', model: Optional[str] = None) -> str:
    logger.info(f'Analyzing company: {company_name}, model: {model or "default"}')
    return self._call_api(messages, model=model)

# ✅ API 接口提取并传递模型参数
ai_model = data.get('ai_model')
if ai_model:
    logger.info(f'User selected AI model: {ai_model}')
analysis = ai_service.analyze_company(..., model=ai_model)
```

### 监控建议

**日志监控**：
```bash
# 检查模型选择情况
grep "User selected AI model" /tmp/topn.log | tail -20

# 检查默认模型使用率
grep "model: default" /tmp/topn.log | wc -l

# 检查高级模型使用率
grep "model: glm-4-plus" /tmp/topn.log | wc -l
```

**告警规则**：
- 如果所有调用都是 `model: default`，说明选择器可能失效
- 高级模型使用率 = 0%，检查是否功能失效

## 相关问题

### 类似问题
如果将来有其他配置选项（温度、token数等）需要在分析时使用：

**错误做法**：
```html
<!-- ❌ 在分析页面添加配置，但分析已经完成 -->
<div id="analysis-config">
    <input type="number" id="temperature" />
    <input type="number" id="max-tokens" />
</div>
```

**正确做法**：
```html
<!-- ✅ 在输入页面添加配置，在分析前就收集 -->
<div id="input-form">
    <input type="number" id="temperature" />
    <input type="number" id="max-tokens" />
    <select id="ai-model"></select>
</div>
```

## 经验教训

### 教训
1. **UI 流程设计要考虑数据流**: 配置项要在使用前提供，不能在使用后
2. **前后端要同步修改**: 只改前端或只改后端都不行
3. **测试要覆盖完整流程**: 不能只测试文章生成，也要测试分析
4. **修复要记录文档**: 避免同样问题反复出现

### 收获
1. **参数传递链要完整**: 前端 → API → Service → 底层调用
2. **日志要记录关键参数**: 方便排查用户选择是否生效
3. **用户提示要准确**: 明确说明配置的影响范围
4. **代码要向后兼容**: 添加 `Optional[str] = None` 参数，不影响旧调用

## 快速诊断指南

### 如何快速识别此问题？

1. **用户报告**: "我选了高级模型但还是用的默认模型"
2. **日志特征**:
   ```
   ✗ 没有看到: User selected AI model: glm-4-plus
   ✗ 只看到: model: default 或 model: None
   ```
3. **前端检查**: 输入页面没有模型选择器
4. **后端检查**: API 不接收或不传递 `ai_model` 参数

### 快速验证
```bash
# 1. 检查前端是否有选择器
curl -s http://39.105.12.124/ | grep "ai-model-select"

# 2. 检查后端是否记录模型选择
ssh u_topn@39.105.12.124 "grep 'User selected AI model' /tmp/topn.log"

# 3. 检查是否使用了用户选择的模型
ssh u_topn@39.105.12.124 "grep 'Analyzing company.*model:' /tmp/topn.log | tail -5"
```

## 总结

这是一个典型的**UI流程设计与数据流不匹配的问题**。

**核心问题**: 配置项（AI模型选择）出现的位置晚于使用位置，导致用户无法影响第一步的AI调用。

**解决方案**: 将配置项前移到输入页面，确保在所有AI调用之前就收集用户选择。

**关键原则**:
- ✅ 配置要在使用前提供
- ✅ 参数要完整传递
- ✅ 日志要记录选择
- ✅ 提示要说明影响范围

**修复时间**: 2025-12-15
**修复版本**: commit 8bfa22b
**验证状态**: ✅ 已部署到生产环境
