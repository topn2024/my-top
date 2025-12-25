/**
 * TOP_N 公共函数库
 * 提供各页面共用的工具函数
 */

// ========== 加载动画 ==========

/**
 * 显示加载动画
 * @param {string} text - 加载提示文字
 */
function showLoading(text = '处理中...') {
    const loadingText = document.getElementById('loading-text');
    const loading = document.getElementById('loading');
    if (loadingText) loadingText.textContent = text;
    if (loading) loading.style.display = 'flex';
}

/**
 * 隐藏加载动画
 */
function hideLoading() {
    const loading = document.getElementById('loading');
    if (loading) loading.style.display = 'none';
}

// ========== AI模型加载 ==========

/**
 * 加载可用的AI模型列表
 * @param {string} selectId - 下拉框元素ID，默认为 'ai-model-select'
 * @returns {Promise<boolean>} - 是否加载成功
 */
async function loadAvailableModels(selectId = 'ai-model-select') {
    const modelSelect = document.getElementById(selectId);
    if (!modelSelect) return false;

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

            console.log('AI models loaded successfully');
            return true;
        } else {
            console.error('Failed to load AI models:', data);
            modelSelect.innerHTML = '<option value="">加载失败，使用默认模型</option>';
            return false;
        }
    } catch (error) {
        console.error('Error loading AI models:', error);
        modelSelect.innerHTML = '<option value="">加载失败，使用默认模型</option>';
        return false;
    }
}

// ========== 用户信息 ==========

/**
 * 加载当前用户信息
 * @returns {Promise<Object|null>} - 用户信息对象或null
 */
async function loadCurrentUser() {
    try {
        const response = await fetch('/api/current-user');
        const data = await response.json();

        if (data.success && data.user) {
            return data.user;
        }
        return null;
    } catch (error) {
        console.error('Failed to load current user:', error);
        return null;
    }
}

// ========== 保存成功提示 ==========

/**
 * 显示保存成功的提示
 * @param {HTMLElement} container - 提示显示的容器元素
 * @param {string} message - 提示信息，默认为'保存成功'
 */
function showSaveToast(container, message = '保存成功') {
    const toast = document.createElement('div');
    toast.className = 'save-toast';
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('show');
    }, 10);

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 2000);
}

// ========== 表单工具 ==========

/**
 * 填充下拉框选项
 * @param {string} selectId - 下拉框元素ID
 * @param {Array} items - 选项数据数组
 * @param {Object} options - 配置选项
 */
function populateSelect(selectId, items, options = {}) {
    const {
        valueField = 'id',
        textField = 'name',
        defaultField = 'is_default',
        defaultText = '(默认)',
        clearExisting = false
    } = options;

    const select = document.getElementById(selectId);
    if (!select) return;

    if (clearExisting) {
        select.innerHTML = '';
    }

    items.forEach(item => {
        const option = document.createElement('option');
        option.value = item[valueField];
        option.textContent = item[textField];

        if (item[defaultField]) {
            option.textContent += ` ${defaultText}`;
            option.selected = true;
        }

        select.appendChild(option);
    });
}

// ========== 日期格式化 ==========

/**
 * 格式化日期时间
 * @param {string|Date} date - 日期对象或字符串
 * @param {string} format - 格式类型: 'full', 'date', 'time', 'relative'
 * @returns {string} - 格式化后的字符串
 */
function formatDateTime(date, format = 'full') {
    const d = new Date(date);

    if (format === 'relative') {
        const now = new Date();
        const diff = now - d;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);

        if (minutes < 1) return '刚刚';
        if (minutes < 60) return `${minutes}分钟前`;
        if (hours < 24) return `${hours}小时前`;
        if (days < 7) return `${days}天前`;
    }

    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const mins = String(d.getMinutes()).padStart(2, '0');

    if (format === 'date') return `${year}-${month}-${day}`;
    if (format === 'time') return `${hours}:${mins}`;
    return `${year}-${month}-${day} ${hours}:${mins}`;
}

// ========== API请求封装 ==========

/**
 * 封装的fetch请求
 * @param {string} url - 请求URL
 * @param {Object} options - 请求选项
 * @returns {Promise<Object>} - 响应数据
 */
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'include'
    };

    const mergedOptions = { ...defaultOptions, ...options };

    if (options.body && typeof options.body === 'object') {
        mergedOptions.body = JSON.stringify(options.body);
    }

    try {
        const response = await fetch(url, mergedOptions);

        if (response.status === 401) {
            window.location.href = '/login';
            throw new Error('请先登录');
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// 导出到全局（兼容非模块化使用）
window.CommonUtils = {
    showLoading,
    hideLoading,
    loadAvailableModels,
    loadCurrentUser,
    showSaveToast,
    populateSelect,
    formatDateTime,
    apiRequest
};
