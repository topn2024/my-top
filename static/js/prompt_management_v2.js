/**
 * 提示词管理系统 V2 - 前端脚本
 */

// 全局状态
const state = {
    currentTab: 'analysis',
    currentPage: {
        analysis: 1,
        article: 1,
        platform: 1
    },
    pageSize: 20,
    filters: {
        analysis: {},
        article: {},
        platform: {}
    },
    editingId: null,
    editingType: null
};

// API基础URL
const API_BASE = '/api/prompts';

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initTabs();
    loadAnalysisPrompts();
    loadIndustryTags();
    loadArticleTags();
});

// 标签页切换
function initTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tab = this.dataset.tab;
            switchTab(tab);
        });
    });
}

function switchTab(tab) {
    // 更新按钮状态
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tab}"]`).classList.add('active');

    // 更新内容显示
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tab}-tab`).classList.add('active');

    // 更新当前标签页
    state.currentTab = tab;

    // 加载数据
    if (tab === 'analysis') {
        loadAnalysisPrompts();
    } else if (tab === 'article') {
        loadArticlePrompts();
    } else if (tab === 'platform') {
        loadPlatformPrompts();
    }
}

// ========== 分析提示词 ==========

async function loadAnalysisPrompts(page = 1) {
    try {
        const params = new URLSearchParams({
            page: page,
            page_size: state.pageSize,
            ...state.filters.analysis
        });

        const response = await fetch(`${API_BASE}/analysis?${params}`);
        const result = await response.json();

        if (result.success) {
            renderAnalysisTable(result.data.prompts);
            renderPagination('analysis', result.data);
            state.currentPage.analysis = page;
        } else {
            showError('加载失败: ' + result.error);
        }
    } catch (error) {
        console.error('加载分析提示词失败:', error);
        showError('网络错误，请稍后重试');
    }
}

function renderAnalysisTable(prompts) {
    const tbody = document.getElementById('analysis-tbody');

    if (prompts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="empty-state">暂无数据</td></tr>';
        return;
    }

    tbody.innerHTML = prompts.map(prompt => `
        <tr>
            <td><strong>${prompt.name}</strong></td>
            <td><code>${prompt.code}</code></td>
            <td><span class="badge badge-${prompt.status}">${getStatusText(prompt.status)}</span></td>
            <td><div class="tags">${renderTags(prompt.industry_tags)}</div></td>
            <td>${prompt.usage_count || 0}</td>
            <td>${(prompt.success_rate * 100).toFixed(1)}%</td>
            <td>${prompt.is_default ? '<span class="badge badge-default">默认</span>' : '-'}</td>
            <td>
                <button class="btn btn-primary btn-sm" onclick="viewPrompt('analysis', ${prompt.id})">查看</button>
                <button class="btn btn-success btn-sm" onclick="editPrompt('analysis', ${prompt.id})">编辑</button>
                <button class="btn btn-danger btn-sm" onclick="deletePrompt('analysis', ${prompt.id})">删除</button>
            </td>
        </tr>
    `).join('');
}

async function loadIndustryTags() {
    try {
        const response = await fetch(`${API_BASE}/analysis/industry-tags`);
        const result = await response.json();

        if (result.success) {
            const select = document.getElementById('analysis-industry-filter');
            result.data.forEach(tag => {
                const option = document.createElement('option');
                option.value = tag;
                option.textContent = tag;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('加载行业标签失败:', error);
    }
}

function applyAnalysisFilters() {
    state.filters.analysis = {
        status: document.getElementById('analysis-status-filter').value,
        industry_tag: document.getElementById('analysis-industry-filter').value,
        search: document.getElementById('analysis-search').value
    };
    loadAnalysisPrompts(1);
}

function resetAnalysisFilters() {
    document.getElementById('analysis-status-filter').value = '';
    document.getElementById('analysis-industry-filter').value = '';
    document.getElementById('analysis-search').value = '';
    state.filters.analysis = {};
    loadAnalysisPrompts(1);
}

// ========== 文章提示词 ==========

async function loadArticlePrompts(page = 1) {
    try {
        const params = new URLSearchParams({
            page: page,
            page_size: state.pageSize,
            ...state.filters.article
        });

        const response = await fetch(`${API_BASE}/article?${params}`);
        const result = await response.json();

        if (result.success) {
            renderArticleTable(result.data.prompts);
            renderPagination('article', result.data);
            state.currentPage.article = page;
        } else {
            showError('加载失败: ' + result.error);
        }
    } catch (error) {
        console.error('加载文章提示词失败:', error);
        showError('网络错误，请稍后重试');
    }
}

function renderArticleTable(prompts) {
    const tbody = document.getElementById('article-tbody');

    if (prompts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="empty-state">暂无数据</td></tr>';
        return;
    }

    tbody.innerHTML = prompts.map(prompt => `
        <tr>
            <td><strong>${prompt.name}</strong></td>
            <td><code>${prompt.code}</code></td>
            <td><span class="badge badge-${prompt.status}">${getStatusText(prompt.status)}</span></td>
            <td><div class="tags">${renderTags([...prompt.industry_tags, ...prompt.style_tags])}</div></td>
            <td>${prompt.usage_count || 0}</td>
            <td>${prompt.avg_rating ? prompt.avg_rating.toFixed(1) + '⭐' : '-'}</td>
            <td>${prompt.is_default ? '<span class="badge badge-default">默认</span>' : '-'}</td>
            <td>
                <button class="btn btn-primary btn-sm" onclick="viewPrompt('article', ${prompt.id})">查看</button>
                <button class="btn btn-success btn-sm" onclick="editPrompt('article', ${prompt.id})">编辑</button>
                <button class="btn btn-danger btn-sm" onclick="deletePrompt('article', ${prompt.id})">删除</button>
            </td>
        </tr>
    `).join('');
}

async function loadArticleTags() {
    try {
        const response = await fetch(`${API_BASE}/article/tags`);
        const result = await response.json();

        if (result.success) {
            const industrySelect = document.getElementById('article-industry-filter');
            const styleSelect = document.getElementById('article-style-filter');

            result.data.industry_tags.forEach(tag => {
                const option = document.createElement('option');
                option.value = tag;
                option.textContent = tag;
                industrySelect.appendChild(option);
            });

            result.data.style_tags.forEach(tag => {
                const option = document.createElement('option');
                option.value = tag;
                option.textContent = tag;
                styleSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('加载标签失败:', error);
    }
}

function applyArticleFilters() {
    state.filters.article = {
        status: document.getElementById('article-status-filter').value,
        industry_tag: document.getElementById('article-industry-filter').value,
        style_tag: document.getElementById('article-style-filter').value,
        search: document.getElementById('article-search').value
    };
    loadArticlePrompts(1);
}

function resetArticleFilters() {
    document.getElementById('article-status-filter').value = '';
    document.getElementById('article-industry-filter').value = '';
    document.getElementById('article-style-filter').value = '';
    document.getElementById('article-search').value = '';
    state.filters.article = {};
    loadArticlePrompts(1);
}

// ========== 平台风格 ==========

async function loadPlatformPrompts(page = 1) {
    try {
        const params = new URLSearchParams({
            page: page,
            page_size: state.pageSize,
            ...state.filters.platform
        });

        const response = await fetch(`${API_BASE}/platform-style?${params}`);
        const result = await response.json();

        if (result.success) {
            renderPlatformTable(result.data.prompts);
            renderPagination('platform', result.data);
            state.currentPage.platform = page;
        } else {
            showError('加载失败: ' + result.error);
        }
    } catch (error) {
        console.error('加载平台风格失败:', error);
        showError('网络错误，请稍后重试');
    }
}

function renderPlatformTable(prompts) {
    const tbody = document.getElementById('platform-tbody');

    if (prompts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="empty-state">暂无数据</td></tr>';
        return;
    }

    tbody.innerHTML = prompts.map(prompt => `
        <tr>
            <td><strong>${prompt.name}</strong></td>
            <td>${getPlatformName(prompt.platform)}</td>
            <td><code>${prompt.code}</code></td>
            <td><span class="badge badge-${prompt.status}">${getStatusText(prompt.status)}</span></td>
            <td>${getApplyStageText(prompt.apply_stage)}</td>
            <td>${prompt.usage_count || 0}</td>
            <td>${prompt.avg_rating ? prompt.avg_rating.toFixed(1) + '⭐' : '-'}</td>
            <td>${prompt.is_default ? '<span class="badge badge-default">默认</span>' : '-'}</td>
            <td>
                <button class="btn btn-primary btn-sm" onclick="viewPrompt('platform', ${prompt.id})">查看</button>
                <button class="btn btn-success btn-sm" onclick="editPrompt('platform', ${prompt.id})">编辑</button>
                <button class="btn btn-danger btn-sm" onclick="deletePrompt('platform', ${prompt.id})">删除</button>
            </td>
        </tr>
    `).join('');
}

function applyPlatformFilters() {
    state.filters.platform = {
        platform: document.getElementById('platform-filter').value,
        status: document.getElementById('platform-status-filter').value,
        apply_stage: document.getElementById('platform-stage-filter').value,
        search: document.getElementById('platform-search').value
    };
    loadPlatformPrompts(1);
}

function resetPlatformFilters() {
    document.getElementById('platform-filter').value = '';
    document.getElementById('platform-status-filter').value = '';
    document.getElementById('platform-stage-filter').value = '';
    document.getElementById('platform-search').value = '';
    state.filters.platform = {};
    loadPlatformPrompts(1);
}

// ========== 通用功能 ==========

function renderPagination(type, data) {
    const container = document.getElementById(`${type}-pagination`);
    const { page, total_pages } = data;

    if (total_pages <= 1) {
        container.innerHTML = '';
        return;
    }

    let html = '<button class="page-btn" onclick="loadPage(\'' + type + '\', ' + (page - 1) + ')" ' +
               (page <= 1 ? 'disabled' : '') + '>上一页</button>';

    for (let i = 1; i <= total_pages; i++) {
        if (i === 1 || i === total_pages || (i >= page - 2 && i <= page + 2)) {
            html += `<button class="page-btn ${i === page ? 'active' : ''}" onclick="loadPage('${type}', ${i})">${i}</button>`;
        } else if (i === page - 3 || i === page + 3) {
            html += '<span>...</span>';
        }
    }

    html += '<button class="page-btn" onclick="loadPage(\'' + type + '\', ' + (page + 1) + ')" ' +
            (page >= total_pages ? 'disabled' : '') + '>下一页</button>';

    container.innerHTML = html;
}

function loadPage(type, page) {
    if (type === 'analysis') {
        loadAnalysisPrompts(page);
    } else if (type === 'article') {
        loadArticlePrompts(page);
    } else if (type === 'platform') {
        loadPlatformPrompts(page);
    }
}

function renderTags(tags) {
    if (!tags || tags.length === 0) return '-';
    return tags.map(tag => `<span class="tag">${tag}</span>`).join('');
}

function getStatusText(status) {
    const map = {
        'active': '活跃',
        'draft': '草稿',
        'archived': '已归档'
    };
    return map[status] || status;
}

function getPlatformName(platform) {
    const map = {
        'zhihu': '知乎',
        'csdn': 'CSDN',
        'juejin': '掘金',
        'xiaohongshu': '小红书'
    };
    return map[platform] || platform;
}

function getApplyStageText(stage) {
    const map = {
        'generation': '生成时',
        'publish': '发布前',
        'both': '两个阶段'
    };
    return map[stage] || stage;
}

// ========== 创建/编辑/删除 ==========

function showCreateModal() {
    const type = state.currentTab;
    state.editingId = null;
    state.editingType = type;

    document.getElementById('modal-title').textContent = '创建提示词';
    document.getElementById('form-type').value = type;
    document.getElementById('form-id').value = '';
    document.getElementById('prompt-form').reset();

    // 显示/隐藏平台特有字段
    const platformFields = document.getElementById('platform-specific-fields');
    platformFields.style.display = type === 'platform' ? 'block' : 'none';

    document.getElementById('edit-modal').classList.add('active');
}

async function viewPrompt(type, id) {
    try {
        const endpoint = type === 'analysis' ? 'analysis' :
                        type === 'article' ? 'article' : 'platform-style';
        const response = await fetch(`${API_BASE}/${endpoint}/${id}`);
        const result = await response.json();

        if (result.success) {
            const prompt = result.data;
            alert(`名称: ${prompt.name}\n代码: ${prompt.code}\n\n系统提示词:\n${prompt.system_prompt}\n\n用户模板:\n${prompt.user_template}`);
        } else {
            showError('查看失败: ' + result.error);
        }
    } catch (error) {
        console.error('查看提示词失败:', error);
        showError('网络错误');
    }
}

async function editPrompt(type, id) {
    try {
        const endpoint = type === 'analysis' ? 'analysis' :
                        type === 'article' ? 'article' : 'platform-style';
        const response = await fetch(`${API_BASE}/${endpoint}/${id}`);
        const result = await response.json();

        if (result.success) {
            const prompt = result.data;

            state.editingId = id;
            state.editingType = type;

            document.getElementById('modal-title').textContent = '编辑提示词';
            document.getElementById('form-type').value = type;
            document.getElementById('form-id').value = id;
            document.getElementById('form-name').value = prompt.name;
            document.getElementById('form-code').value = prompt.code;
            document.getElementById('form-description').value = prompt.description || '';
            document.getElementById('form-system-prompt').value = prompt.system_prompt;
            document.getElementById('form-user-template').value = prompt.user_template;
            document.getElementById('form-temperature').value = prompt.temperature;
            document.getElementById('form-max-tokens').value = prompt.max_tokens;
            document.getElementById('form-status').value = prompt.status;
            document.getElementById('form-is-default').checked = prompt.is_default;

            // 平台特有字段
            const platformFields = document.getElementById('platform-specific-fields');
            if (type === 'platform') {
                platformFields.style.display = 'block';
                document.getElementById('form-platform').value = prompt.platform;
                document.getElementById('form-apply-stage').value = prompt.apply_stage;
            } else {
                platformFields.style.display = 'none';
            }

            document.getElementById('edit-modal').classList.add('active');
        } else {
            showError('加载失败: ' + result.error);
        }
    } catch (error) {
        console.error('加载提示词失败:', error);
        showError('网络错误');
    }
}

async function savePrompt() {
    const type = document.getElementById('form-type').value;
    const id = document.getElementById('form-id').value;

    const data = {
        name: document.getElementById('form-name').value,
        code: document.getElementById('form-code').value,
        description: document.getElementById('form-description').value,
        system_prompt: document.getElementById('form-system-prompt').value,
        user_template: document.getElementById('form-user-template').value,
        temperature: parseFloat(document.getElementById('form-temperature').value),
        max_tokens: parseInt(document.getElementById('form-max-tokens').value),
        status: document.getElementById('form-status').value,
        is_default: document.getElementById('form-is-default').checked
    };

    if (type === 'platform') {
        data.platform = document.getElementById('form-platform').value;
        data.apply_stage = document.getElementById('form-apply-stage').value;
    }

    try {
        const endpoint = type === 'analysis' ? 'analysis' :
                        type === 'article' ? 'article' : 'platform-style';
        const url = id ? `${API_BASE}/${endpoint}/${id}` : `${API_BASE}/${endpoint}`;
        const method = id ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            showSuccess(id ? '更新成功' : '创建成功');
            closeModal();
            loadPage(type, state.currentPage[type]);
        } else {
            showError('保存失败: ' + result.error);
        }
    } catch (error) {
        console.error('保存提示词失败:', error);
        showError('网络错误');
    }
}

async function deletePrompt(type, id) {
    if (!confirm('确定要删除这个提示词吗？')) {
        return;
    }

    try {
        const endpoint = type === 'analysis' ? 'analysis' :
                        type === 'article' ? 'article' : 'platform-style';
        const response = await fetch(`${API_BASE}/${endpoint}/${id}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            showSuccess('删除成功');
            loadPage(type, state.currentPage[type]);
        } else {
            showError('删除失败: ' + result.error);
        }
    } catch (error) {
        console.error('删除提示词失败:', error);
        showError('网络错误');
    }
}

function closeModal() {
    document.getElementById('edit-modal').classList.remove('active');
}

// ========== 提示信息 ==========

function showSuccess(message) {
    alert('✓ ' + message);
}

function showError(message) {
    alert('✗ ' + message);
}
