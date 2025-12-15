// 模板管理JavaScript

const API_BASE = '/api/prompt-templates';

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    loadStats();
    loadTemplates();
    loadFilterOptions();
});

// 加载统计信息
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const data = await response.json();

        if (data.success) {
            document.getElementById('totalTemplates').textContent = data.data.total_templates;
            document.getElementById('activeTemplates').textContent = data.data.active_templates;
            document.getElementById('totalCategories').textContent = data.data.total_categories;
            document.getElementById('totalExamples').textContent = data.data.total_examples;
        }
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

// 加载模板列表
async function loadTemplates() {
    const container = document.getElementById('templatesContainer');
    container.innerHTML = '<div class="loading"><div class="spinner"></div><p>加载中...</p></div>';

    try {
        // 构建查询参数
        const params = new URLSearchParams();
        const status = document.getElementById('filterStatus').value;
        const industry = document.getElementById('filterIndustry').value;
        const platform = document.getElementById('filterPlatform').value;

        if (status) params.append('status', status);
        if (industry) params.append('industry', industry);
        if (platform) params.append('platform', platform);

        const response = await fetch(`${API_BASE}/templates?${params}`);
        const data = await response.json();

        if (data.success && data.data.length > 0) {
            // 应用客户端搜索过滤
            let templates = data.data;
            const searchKeyword = document.getElementById('searchKeyword').value.toLowerCase();
            if (searchKeyword) {
                templates = templates.filter(t =>
                    t.name.toLowerCase().includes(searchKeyword) ||
                    t.code.toLowerCase().includes(searchKeyword)
                );
            }

            if (templates.length > 0) {
                renderTemplates(templates);
            } else {
                showEmptyState('没有找到匹配的模板');
            }
        } else {
            showEmptyState('暂无模板，点击右上角按钮创建新模板');
        }
    } catch (error) {
        console.error('Failed to load templates:', error);
        container.innerHTML = '<div class="empty-state"><p>加载失败，请刷新重试</p></div>';
    }
}

// 渲染模板列表
function renderTemplates(templates) {
    const container = document.getElementById('templatesContainer');
    const grid = document.createElement('div');
    grid.className = 'templates-grid';

    templates.forEach(template => {
        const card = createTemplateCard(template);
        grid.appendChild(card);
    });

    container.innerHTML = '';
    container.appendChild(grid);
}

// 创建模板卡片
function createTemplateCard(template) {
    const card = document.createElement('div');
    card.className = 'template-card';

    const statusClass = `status-${template.status}`;
    const statusText = {
        'active': '活跃',
        'draft': '草稿',
        'archived': '已归档'
    }[template.status] || template.status;

    card.innerHTML = `
        <div class="template-header">
            <div>
                <div class="template-title">${escapeHtml(template.name)}</div>
                <div class="template-code">${escapeHtml(template.code)}</div>
            </div>
            <span class="template-status ${statusClass}">${statusText}</span>
        </div>

        <div class="template-meta">
            <div class="meta-item">
                <span>📊</span>
                <span>使用 ${template.usage_count || 0} 次</span>
            </div>
            <div class="meta-item">
                <span>⭐</span>
                <span>评分 ${(template.avg_rating || 0).toFixed(1)}</span>
            </div>
            <div class="meta-item">
                <span>✓</span>
                <span>成功率 ${((template.success_rate || 0) * 100).toFixed(0)}%</span>
            </div>
        </div>

        ${template.description ? `<div style="color: #7f8c8d; font-size: 14px; margin: 10px 0;">${escapeHtml(template.description)}</div>` : ''}

        <div class="template-tags">
            ${(template.industry_tags || []).map(tag =>
                `<span class="tag tag-industry">${escapeHtml(tag)}</span>`
            ).join('')}
            ${(template.platform_tags || []).map(tag =>
                `<span class="tag tag-platform">${escapeHtml(tag)}</span>`
            ).join('')}
        </div>

        <div class="template-actions">
            <button class="btn btn-primary btn-sm" onclick="viewTemplate(${template.id})">查看详情</button>
            <button class="btn btn-secondary btn-sm" onclick="editTemplate(${template.id})">编辑</button>
            ${template.status === 'active'
                ? `<button class="btn btn-warning btn-sm" onclick="archiveTemplate(${template.id})">归档</button>`
                : `<button class="btn btn-success btn-sm" onclick="activateTemplate(${template.id})">激活</button>`
            }
            <button class="btn btn-danger btn-sm" onclick="deleteTemplate(${template.id})">删除</button>
        </div>
    `;

    return card;
}

// 显示空状态
function showEmptyState(message) {
    const container = document.getElementById('templatesContainer');
    container.innerHTML = `
        <div class="empty-state">
            <div class="empty-state-icon">📝</div>
            <p>${message}</p>
        </div>
    `;
}

// 加载过滤选项
async function loadFilterOptions() {
    // 加载常见的行业和平台标签
    const industries = ['tech', 'finance', 'education', 'healthcare', 'retail', 'manufacturing'];
    const platforms = ['zhihu', 'csdn', 'juejin', 'wechat', 'weibo', 'douyin'];

    const industrySelect = document.getElementById('filterIndustry');
    industries.forEach(industry => {
        const option = document.createElement('option');
        option.value = industry;
        option.textContent = industry;
        industrySelect.appendChild(option);
    });

    const platformSelect = document.getElementById('filterPlatform');
    platforms.forEach(platform => {
        const option = document.createElement('option');
        option.value = platform;
        option.textContent = platform;
        platformSelect.appendChild(option);
    });
}

// 显示创建模态框
function showCreateModal() {
    document.getElementById('modalTitle').textContent = '创建新模板';
    document.getElementById('templateForm').reset();
    document.getElementById('templateId').value = '';
    document.getElementById('templateStatus').value = 'draft';
    document.getElementById('templateModal').style.display = 'block';
}

// 查看模板详情
async function viewTemplate(id) {
    try {
        const response = await fetch(`${API_BASE}/templates/${id}`);
        const data = await response.json();

        if (data.success) {
            const template = data.data;
            alert(`模板: ${template.name}\n\n` +
                  `代码: ${template.code}\n` +
                  `状态: ${template.status}\n` +
                  `描述: ${template.description || '无'}\n\n` +
                  `使用次数: ${template.usage_count}\n` +
                  `成功率: ${(template.success_rate * 100).toFixed(1)}%\n` +
                  `平均评分: ${template.avg_rating.toFixed(1)}`);
        }
    } catch (error) {
        console.error('Failed to view template:', error);
        alert('加载模板详情失败');
    }
}

// 编辑模板
async function editTemplate(id) {
    try {
        const response = await fetch(`${API_BASE}/templates/${id}`);
        const data = await response.json();

        if (data.success) {
            const template = data.data;

            document.getElementById('modalTitle').textContent = '编辑模板';
            document.getElementById('templateId').value = template.id;
            document.getElementById('templateName').value = template.name;
            document.getElementById('templateCode').value = template.code;
            document.getElementById('templateDescription').value = template.description || '';

            // 填充提示词
            if (template.prompts && template.prompts.analysis) {
                document.getElementById('analysisSystem').value = template.prompts.analysis.system || '';
                document.getElementById('analysisUserTemplate').value = template.prompts.analysis.user_template || '';
            }
            if (template.prompts && template.prompts.article_generation) {
                document.getElementById('generationSystem').value = template.prompts.article_generation.system || '';
                document.getElementById('generationUserTemplate').value = template.prompts.article_generation.user_template || '';
            }

            // 填充标签
            document.getElementById('industryTags').value = (template.industry_tags || []).join(', ');
            document.getElementById('platformTags').value = (template.platform_tags || []).join(', ');
            document.getElementById('keywords').value = (template.keywords || []).join(', ');

            // AI配置
            if (template.ai_config) {
                document.getElementById('temperature').value = template.ai_config.temperature || 0.8;
                document.getElementById('maxTokens').value = template.ai_config.max_tokens || 3000;
            }

            document.getElementById('templateStatus').value = template.status;
            document.getElementById('templateModal').style.display = 'block';
        }
    } catch (error) {
        console.error('Failed to load template:', error);
        alert('加载模板失败');
    }
}

// 关闭模态框
function closeModal() {
    document.getElementById('templateModal').style.display = 'none';
}

// 提交表单
document.getElementById('templateForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const id = document.getElementById('templateId').value;
    const isEdit = !!id;

    const templateData = {
        name: document.getElementById('templateName').value,
        code: document.getElementById('templateCode').value,
        description: document.getElementById('templateDescription').value,
        prompts: {
            analysis: {
                system: document.getElementById('analysisSystem').value,
                user_template: document.getElementById('analysisUserTemplate').value
            },
            article_generation: {
                system: document.getElementById('generationSystem').value,
                user_template: document.getElementById('generationUserTemplate').value
            }
        },
        industry_tags: document.getElementById('industryTags').value
            .split(',').map(s => s.trim()).filter(s => s),
        platform_tags: document.getElementById('platformTags').value
            .split(',').map(s => s.trim()).filter(s => s),
        keywords: document.getElementById('keywords').value
            .split(',').map(s => s.trim()).filter(s => s),
        ai_config: {
            temperature: parseFloat(document.getElementById('temperature').value),
            max_tokens: parseInt(document.getElementById('maxTokens').value)
        },
        status: document.getElementById('templateStatus').value
    };

    try {
        const url = isEdit
            ? `${API_BASE}/admin/templates/${id}`
            : `${API_BASE}/admin/templates`;

        const method = isEdit ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(templateData)
        });

        const data = await response.json();

        if (data.success) {
            alert(isEdit ? '模板更新成功！' : '模板创建成功！');
            closeModal();
            loadStats();
            loadTemplates();
        } else {
            alert('操作失败: ' + (data.error || '未知错误'));
        }
    } catch (error) {
        console.error('Failed to save template:', error);
        alert('保存失败，请重试');
    }
});

// 激活模板
async function activateTemplate(id) {
    if (!confirm('确定要激活此模板吗？')) return;

    try {
        const response = await fetch(`${API_BASE}/admin/templates/${id}/activate`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            alert('模板已激活');
            loadStats();
            loadTemplates();
        } else {
            alert('激活失败: ' + (data.error || '未知错误'));
        }
    } catch (error) {
        console.error('Failed to activate template:', error);
        alert('操作失败');
    }
}

// 归档模板
async function archiveTemplate(id) {
    if (!confirm('确定要归档此模板吗？归档后将不再出现在活跃列表中。')) return;

    try {
        const response = await fetch(`${API_BASE}/admin/templates/${id}/archive`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            alert('模板已归档');
            loadStats();
            loadTemplates();
        } else {
            alert('归档失败: ' + (data.error || '未知错误'));
        }
    } catch (error) {
        console.error('Failed to archive template:', error);
        alert('操作失败');
    }
}

// 删除模板
async function deleteTemplate(id) {
    if (!confirm('确定要删除此模板吗？此操作不可恢复！')) return;

    try {
        const response = await fetch(`${API_BASE}/admin/templates/${id}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            alert('模板已删除');
            loadStats();
            loadTemplates();
        } else {
            alert('删除失败: ' + (data.error || '未知错误'));
        }
    } catch (error) {
        console.error('Failed to delete template:', error);
        alert('操作失败');
    }
}

// HTML转义
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// 点击模态框外部关闭
window.onclick = function(event) {
    const modal = document.getElementById('templateModal');
    if (event.target === modal) {
        closeModal();
    }
};
