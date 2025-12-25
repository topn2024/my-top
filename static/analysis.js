// 分析页面逻辑 - 支持富文本编辑

// Quill 编辑器实例
let analysisEditor = null;
let isEditing = false;

// 页面加载时显示分析结果
window.addEventListener('load', () => {
    const state = WorkflowState.get();

    // 检查是否有分析结果
    if (!state.analysis) {
        alert('未找到分析结果，请先完成信息输入');
        WorkflowNav.goToInput();
        return;
    }

    // 显示分析结果
    displayAnalysis(state.analysis);

    // 加载AI模型列表
    loadAvailableModels();

    // 初始化编辑功能
    initAnalysisEditor();
});

// 初始化编辑功能
function initAnalysisEditor() {
    const editBtn = document.getElementById('edit-analysis-btn');
    const cancelBtn = document.getElementById('cancel-analysis-edit');
    const saveBtn = document.getElementById('save-analysis-edit');

    if (editBtn) {
        editBtn.addEventListener('click', toggleAnalysisEdit);
    }
    if (cancelBtn) {
        cancelBtn.addEventListener('click', cancelAnalysisEdit);
    }
    if (saveBtn) {
        saveBtn.addEventListener('click', saveAnalysisEdit);
    }
}

// 切换编辑模式
function toggleAnalysisEdit() {
    if (isEditing) {
        cancelAnalysisEdit();
    } else {
        enterAnalysisEditMode();
    }
}

// 进入编辑模式
function enterAnalysisEditMode() {
    const card = document.getElementById('analysis-card');
    const display = document.getElementById('analysis-display');
    const editorContainer = document.getElementById('analysis-editor-container');
    const editActions = document.getElementById('analysis-edit-actions');
    const editBtn = document.getElementById('edit-analysis-btn');

    // 切换显示
    display.style.display = 'none';
    editorContainer.style.display = 'block';
    editActions.style.display = 'flex';
    card.classList.add('editing');
    editBtn.classList.add('active');

    // 初始化编辑器（如果还没有）
    if (!analysisEditor) {
        analysisEditor = new Quill('#analysis-editor', {
            theme: 'snow',
            modules: {
                toolbar: '#analysis-toolbar'
            },
            placeholder: '编辑分析内容...'
        });
    }

    // 设置内容
    const state = WorkflowState.get();
    const content = state.analysis || '';
    // 将纯文本转换为带换行的HTML
    const htmlContent = content.replace(/\n/g, '<br>');
    analysisEditor.clipboard.dangerouslyPasteHTML(htmlContent);

    isEditing = true;
}

// 取消编辑
function cancelAnalysisEdit() {
    const card = document.getElementById('analysis-card');
    const display = document.getElementById('analysis-display');
    const editorContainer = document.getElementById('analysis-editor-container');
    const editActions = document.getElementById('analysis-edit-actions');
    const editBtn = document.getElementById('edit-analysis-btn');

    // 恢复原始内容
    if (analysisEditor) {
        const state = WorkflowState.get();
        const htmlContent = (state.analysis || '').replace(/\n/g, '<br>');
        analysisEditor.clipboard.dangerouslyPasteHTML(htmlContent);
    }

    // 切换显示
    display.style.display = 'block';
    editorContainer.style.display = 'none';
    editActions.style.display = 'none';
    card.classList.remove('editing');
    editBtn.classList.remove('active');

    isEditing = false;
}

// 保存编辑
function saveAnalysisEdit() {
    const display = document.getElementById('analysis-display');
    const card = document.getElementById('analysis-card');
    const editorContainer = document.getElementById('analysis-editor-container');
    const editActions = document.getElementById('analysis-edit-actions');
    const editBtn = document.getElementById('edit-analysis-btn');

    // 获取新内容
    const newHtmlContent = analysisEditor.root.innerHTML;
    const newTextContent = analysisEditor.getText().trim();

    // 验证
    if (!newTextContent) {
        alert('分析内容不能为空');
        return;
    }

    // 更新显示
    display.innerHTML = newHtmlContent;

    // 更新状态
    const state = WorkflowState.get();
    state.analysis = newTextContent;
    state.analysisHtml = newHtmlContent;
    WorkflowState.save(state);

    // 切换显示
    display.style.display = 'block';
    editorContainer.style.display = 'none';
    editActions.style.display = 'none';
    card.classList.remove('editing');
    editBtn.classList.remove('active');

    isEditing = false;

    // 显示保存成功提示
    showSaveToast(card);
}

// 显示保存成功提示
function showSaveToast(container) {
    const toast = document.createElement('div');
    toast.className = 'save-toast';
    toast.textContent = '保存成功';
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('show');
    }, 10);

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 2000);
}

// 加载可用的AI模型列表 - 使用公共模块中的 loadAvailableModels()
// 如果公共模块未加载，提供回退实现
if (typeof loadAvailableModels === 'undefined') {
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
                    if (model.id === data.default) option.selected = true;
                    modelSelect.appendChild(option);
                });
            } else {
                modelSelect.innerHTML = '<option value="">加载失败，使用默认模型</option>';
            }
        } catch (error) {
            console.error('Error loading models:', error);
            modelSelect.innerHTML = '<option value="">加载失败，使用默认模型</option>';
        }
    }
}

// 显示分析结果
function displayAnalysis(analysis) {
    const resultBox = document.getElementById('analysis-display');
    // 如果有HTML版本则使用，否则将纯文本转换为HTML
    const state = WorkflowState.get();
    if (state.analysisHtml) {
        resultBox.innerHTML = state.analysisHtml;
    } else {
        resultBox.innerHTML = analysis.replace(/\n/g, '<br>');
    }
}

// 生成文章按钮
document.getElementById('generate-btn').addEventListener('click', async () => {
    const state = WorkflowState.get();

    showLoading('正在生成推广文章，请稍候...');

    try {
        const requestData = {
            company_name: state.companyName,
            analysis: state.analysis,
            article_count: state.articleCount || 3
        };

        // 添加workflow_id（如果存在）
        if (state.workflowId) {
            requestData.workflow_id = state.workflowId;
        }

        // 添加旧模板ID（向后兼容）
        if (state.templateId) {
            requestData.template_id = state.templateId;
        }

        // 添加新的三模块提示词ID
        if (state.articlePromptId) {
            requestData.article_prompt_id = state.articlePromptId;
        }
        if (state.platformStylePromptId) {
            requestData.platform_style_prompt_id = state.platformStylePromptId;
        }

        // 添加选中的AI模型
        const modelSelect = document.getElementById('ai-model-select');
        if (modelSelect && modelSelect.value) {
            requestData.ai_model = modelSelect.value;
        }

        const response = await fetch('/api/generate_articles', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });

        const data = await response.json();

        if (data.success) {
            // 保存文章到状态
            WorkflowState.update({
                articles: data.articles,
                currentStep: 3
            });

            // 跳转到文章页面
            WorkflowNav.goToArticles();
        } else {
            alert('生成文章失败: ' + data.error);
        }
    } catch (error) {
        alert('请求失败: ' + error.message);
    } finally {
        hideLoading();
    }
});

// 加载动画 - 使用公共模块中的 showLoading() 和 hideLoading()
// 如果公共模块未加载，提供回退实现
if (typeof showLoading === 'undefined') {
    function showLoading(text = '处理中...') {
        document.getElementById('loading-text').textContent = text;
        document.getElementById('loading').style.display = 'flex';
    }
}

if (typeof hideLoading === 'undefined') {
    function hideLoading() {
        document.getElementById('loading').style.display = 'none';
    }
}
