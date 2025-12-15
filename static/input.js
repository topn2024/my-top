// 输入页面逻辑
let uploadedText = '';
let availableTemplates = [];

// 文件上传相关
const uploadArea = document.getElementById('upload-area');
const fileInput = document.getElementById('file-upload');
const uploadPlaceholder = uploadArea.querySelector('.upload-placeholder');
const uploadResult = document.getElementById('upload-result');
const uploadedFilename = document.getElementById('uploaded-filename');

// 页面加载时恢复之前的输入
window.addEventListener('load', () => {
    const state = WorkflowState.get();

    // 恢复表单数据
    if (state.companyName) {
        document.getElementById('company-name').value = state.companyName;
    }
    if (state.companyDesc) {
        document.getElementById('company-desc').value = state.companyDesc;
    }
    if (state.articleCount) {
        document.getElementById('article-count').value = state.articleCount;
    }
    if (state.uploadedFilename) {
        uploadedText = state.uploadedText;
        uploadedFilename.textContent = state.uploadedFilename;
        uploadPlaceholder.style.display = 'none';
        uploadResult.style.display = 'block';
    }

    // 加载可用模板
    loadAvailableTemplates();
});

// 加载可用模板
async function loadAvailableTemplates() {
    try {
        const response = await fetch('/api/prompt-templates/templates?status=active');
        const data = await response.json();

        if (data.success && data.data.length > 0) {
            availableTemplates = data.data;
            const templateSelect = document.getElementById('template-select');

            data.data.forEach(template => {
                const option = document.createElement('option');
                option.value = template.id;
                option.textContent = `${template.name} (${template.code})`;
                option.dataset.template = JSON.stringify(template);
                templateSelect.appendChild(option);
            });

            // 添加选择变化监听
            templateSelect.addEventListener('change', function() {
                showTemplateInfo(this.value);
            });
        }
    } catch (error) {
        console.error('Failed to load templates:', error);
    }
}

// 显示模板信息
function showTemplateInfo(templateId) {
    const templateInfo = document.getElementById('template-info');
    const templateName = document.getElementById('template-name');
    const templateDescription = document.getElementById('template-description');
    const templateTags = document.getElementById('template-tags');

    if (!templateId) {
        templateInfo.style.display = 'none';
        return;
    }

    const template = availableTemplates.find(t => t.id == templateId);
    if (!template) {
        templateInfo.style.display = 'none';
        return;
    }

    templateName.textContent = template.name;
    templateDescription.textContent = template.description || '暂无描述';

    // 构建标签HTML
    let tagsHtml = '';
    if (template.industry_tags && template.industry_tags.length > 0) {
        tagsHtml += `<span style="background: #cfe2ff; color: #084298; padding: 2px 8px; border-radius: 3px; font-size: 11px;">
            ${template.industry_tags.join(', ')}
        </span>`;
    }
    if (template.platform_tags && template.platform_tags.length > 0) {
        tagsHtml += `<span style="background: #d1e7dd; color: #0a3622; padding: 2px 8px; border-radius: 3px; font-size: 11px; margin-left: 5px;">
            ${template.platform_tags.join(', ')}
        </span>`;
    }
    templateTags.innerHTML = tagsHtml;

    templateInfo.style.display = 'block';
}

// 点击上传区域触发文件选择
uploadArea.addEventListener('click', () => {
    fileInput.click();
});

// 拖拽上传
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.style.borderColor = '#667eea';
    uploadArea.style.background = '#f8f9ff';
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.style.borderColor = '#e0e0e0';
    uploadArea.style.background = 'white';
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.style.borderColor = '#e0e0e0';
    uploadArea.style.background = 'white';

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileUpload(files[0]);
    }
});

// 文件选择change事件
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileUpload(e.target.files[0]);
    }
});

// 处理文件上传
async function handleFileUpload(file) {
    const allowedExtensions = ['.txt', '.pdf', '.doc', '.docx', '.md'];
    const fileName = file.name.toLowerCase();
    const hasValidExtension = allowedExtensions.some(ext => fileName.endsWith(ext));

    if (!hasValidExtension) {
        alert('不支持的文件格式！仅支持 TXT, PDF, DOC, DOCX, MD 格式');
        return;
    }

    if (file.size > 10 * 1024 * 1024) {
        alert('文件太大！最大支持 10MB');
        return;
    }

    showLoading('正在读取文件...');

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/upload', {
            method: 'POST',
            credentials: 'include',  // 包含session cookie
            body: formData
        });

        // 检查响应状态
        if (response.status === 401) {
            hideLoading();
            alert('请先登录！');
            window.location.href = '/login';
            return;
        }

        if (!response.ok) {
            const errorText = await response.text();
            hideLoading();
            alert(`上传失败 (${response.status}): ${errorText.substring(0, 100)}`);
            return;
        }

        const data = await response.json();
        console.log('Upload response:', data); // 调试信息

        if (data.success) {
            uploadedText = data.text;
            uploadedFilename.textContent = data.filename;
            uploadPlaceholder.style.display = 'none';
            uploadResult.style.display = 'block';

            // 保存到状态
            WorkflowState.update({
                uploadedText: data.text,
                uploadedFilename: data.filename
            });

            // 将提取的文本添加到描述框
            const descTextarea = document.getElementById('company-desc');
            if (data.text) {
                if (descTextarea.value) {
                    descTextarea.value += '\n\n--- 文件内容 ---\n' + data.text;
                } else {
                    descTextarea.value = data.text;
                }
                alert('文件上传成功！内容已自动填充到描述框中');
            } else {
                console.warn('Extracted text is empty');
                alert('文件上传成功，但未能提取到文本内容');
            }
        } else {
            alert('文件上传失败: ' + data.error);
        }
    } catch (error) {
        alert('文件上传失败: ' + error.message);
    } finally {
        hideLoading();
    }
}

// 清除上传的文件
function clearUpload() {
    uploadedText = '';
    fileInput.value = '';
    uploadPlaceholder.style.display = 'block';
    uploadResult.style.display = 'none';

    // 更新状态
    WorkflowState.update({
        uploadedText: '',
        uploadedFilename: ''
    });

    // 从描述框中移除文件内容
    const descTextarea = document.getElementById('company-desc');
    if (descTextarea.value.includes('--- 文件内容 ---')) {
        const parts = descTextarea.value.split('--- 文件内容 ---');
        descTextarea.value = parts[0].trim();
    }
}

// 表单提交
document.getElementById('company-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = {
        company_name: document.getElementById('company-name').value,
        company_desc: document.getElementById('company-desc').value
    };

    const articleCount = parseInt(document.getElementById('article-count').value);
    const templateId = document.getElementById('template-select').value;

    // 如果选择了模板，添加到表单数据
    if (templateId) {
        formData.template_id = parseInt(templateId);
    }

    // 获取三模块提示词ID
    const analysisPromptId = document.getElementById('analysis-prompt-select')?.value;
    const articlePromptId = document.getElementById('article-prompt-select')?.value;
    const platformStyleId = document.getElementById('platform-style-select')?.value;

    // 添加新的三模块提示词ID到请求
    if (analysisPromptId) {
        formData.analysis_prompt_id = parseInt(analysisPromptId);
    }
    if (articlePromptId) {
        formData.article_prompt_id = parseInt(articlePromptId);
    }
    if (platformStyleId) {
        formData.platform_style_prompt_id = parseInt(platformStyleId);
    }

    // 保存到状态
    WorkflowState.update({
        companyName: formData.company_name,
        companyDesc: formData.company_desc,
        articleCount: articleCount,
        templateId: templateId || null,
        analysisPromptId: analysisPromptId || null,
        articlePromptId: articlePromptId || null,
        platformStylePromptId: platformStyleId || null,
        currentStep: 1
    });

    showLoading('正在分析公司信息...');

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (data.success) {
            // 保存分析结果和workflow_id到状态
            WorkflowState.update({
                analysis: data.analysis,
                workflowId: data.workflow_id,
                currentStep: 2
            });

            // 跳转到分析页面
            WorkflowNav.goToAnalysis();
        } else {
            alert('分析失败: ' + data.error);
        }
    } catch (error) {
        alert('请求失败: ' + error.message);
    } finally {
        hideLoading();
    }
});

// 加载动画
function showLoading(text = '处理中...') {
    document.getElementById('loading-text').textContent = text;
    document.getElementById('loading').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

// ========== 三模块提示词选择功能 ==========

// 页面加载时初始化提示词选择
window.addEventListener('load', () => {
    loadPromptOptions();
});

// 加载提示词选项
async function loadPromptOptions() {
    try {
        // 加载分析提示词
        const analysisRes = await fetch('/api/prompts/analysis?status=active&page_size=50');
        const analysisData = await analysisRes.json();
        if (analysisData.success) {
            populateSelect('analysis-prompt-select', analysisData.data.prompts);
        }

        // 加载文章提示词
        const articleRes = await fetch('/api/prompts/article?status=active&page_size=50');
        const articleData = await articleRes.json();
        if (articleData.success) {
            populateSelect('article-prompt-select', articleData.data.prompts);
        }
    } catch (error) {
        console.error('加载提示词选项失败:', error);
    }
}

// 填充下拉框
function populateSelect(selectId, prompts) {
    const select = document.getElementById(selectId);
    if (!select) return;

    prompts.forEach(prompt => {
        const option = document.createElement('option');
        option.value = prompt.id;
        option.textContent = prompt.name;
        if (prompt.is_default) {
            option.textContent += ' (默认)';
        }
        select.appendChild(option);
    });
}

// 智能推荐功能
async function getRecommendation() {
    const companyName = document.getElementById('company-name').value;
    const companyDesc = document.getElementById('company-desc').value;

    if (!companyName && !companyDesc) {
        alert('请先填写公司名称或描述信息');
        return;
    }

    showLoading('正在分析并推荐最佳组合...');

    try {
        // 获取选择的平台
        const platformSelect = document.getElementById('platform-style-select');
        const targetPlatform = platformSelect.value;

        const response = await fetch('/api/prompts/combinations/recommend', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                company_info: {
                    company_name: companyName,
                    company_desc: companyDesc + (uploadedText ? '\n\n' + uploadedText : '')
                },
                target_platform: targetPlatform || null
            })
        });

        const result = await response.json();

        if (result.success) {
            const recommendation = result.data;

            // 应用推荐
            if (recommendation.analysis_prompt) {
                document.getElementById('analysis-prompt-select').value = recommendation.analysis_prompt.id;
            }

            if (recommendation.article_prompt) {
                document.getElementById('article-prompt-select').value = recommendation.article_prompt.id;
            }

            if (recommendation.platform_style) {
                // 根据平台设置选项
                const platformMap = {
                    'zhihu': 'zhihu',
                    'csdn': 'csdn',
                    'juejin': 'juejin',
                    'xiaohongshu': 'xiaohongshu'
                };
                const platformValue = platformMap[recommendation.platform_style.platform];
                if (platformValue) {
                    document.getElementById('platform-style-select').value = platformValue;
                }
            }

            // 显示推荐理由
            const reasonDiv = document.getElementById('recommendation-reason');
            const reasonText = document.getElementById('reason-text');
            reasonText.textContent = recommendation.reason;
            reasonDiv.style.display = 'block';

            // 显示检测到的行业
            if (recommendation.detected_industries && recommendation.detected_industries.length > 0) {
                alert('推荐成功！\n\n检测到的行业：' + recommendation.detected_industries.join(', ') + '\n推荐置信度：' + (recommendation.confidence * 100).toFixed(0) + '%');
            }
        } else {
            alert('推荐失败：' + result.error);
        }
    } catch (error) {
        console.error('智能推荐失败:', error);
        alert('推荐失败，请稍后重试');
    } finally {
        hideLoading();
    }
}
