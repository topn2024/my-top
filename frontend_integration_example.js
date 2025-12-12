/**
 * TOP_N 多用户并发发布系统 - 前端集成示例
 *
 * 这个文件展示如何在前端JavaScript中调用任务API
 * 可以将这些代码集成到 static/publish.js 中
 */

// ========================================
// 1. 创建单个发布任务
// ========================================

/**
 * 创建单个发布任务
 * @param {string} title - 文章标题
 * @param {string} content - 文章内容
 * @param {string} platform - 发布平台 (默认: zhihu)
 * @returns {Promise<Object>} 任务创建结果
 */
async function createPublishTask(title, content, platform = 'zhihu') {
    try {
        const response = await fetch('/api/tasks/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include', // 包含cookies
            body: JSON.stringify({
                title: title,
                content: content,
                platform: platform
            })
        });

        const result = await response.json();

        if (result.success) {
            console.log('✅ 任务创建成功:', result.task_id);
            return {
                success: true,
                taskId: result.task_id,
                status: result.status
            };
        } else {
            console.error('❌ 任务创建失败:', result.error);
            return {
                success: false,
                error: result.error,
                message: result.message
            };
        }
    } catch (error) {
        console.error('网络错误:', error);
        return {
            success: false,
            error: '网络请求失败'
        };
    }
}

// ========================================
// 2. 批量创建发布任务
// ========================================

/**
 * 批量创建发布任务
 * @param {Array<Object>} articles - 文章列表
 * @param {string} platform - 发布平台
 * @returns {Promise<Object>} 批量创建结果
 */
async function createBatchPublishTasks(articles, platform = 'zhihu') {
    try {
        const response = await fetch('/api/tasks/create_batch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
                articles: articles,
                platform: platform
            })
        });

        const result = await response.json();

        console.log(`📊 批量创建结果: 成功${result.success_count}/${result.total}`);
        return result;
    } catch (error) {
        console.error('网络错误:', error);
        return {
            success: false,
            error: '网络请求失败'
        };
    }
}

// ========================================
// 3. 查询任务状态
// ========================================

/**
 * 查询任务状态
 * @param {string} taskId - 任务ID
 * @returns {Promise<Object>} 任务状态信息
 */
async function getTaskStatus(taskId) {
    try {
        const response = await fetch(`/api/tasks/${taskId}`, {
            method: 'GET',
            credentials: 'include'
        });

        const result = await response.json();

        if (result.success) {
            return result.task;
        } else {
            console.error('查询失败:', result.error);
            return null;
        }
    } catch (error) {
        console.error('网络错误:', error);
        return null;
    }
}

// ========================================
// 4. 获取任务列表
// ========================================

/**
 * 获取用户任务列表
 * @param {string} status - 状态过滤 (可选)
 * @param {number} limit - 返回数量
 * @param {number} offset - 偏移量
 * @returns {Promise<Object>} 任务列表和统计信息
 */
async function getTaskList(status = null, limit = 20, offset = 0) {
    try {
        let url = `/api/tasks/list?limit=${limit}&offset=${offset}`;
        if (status) {
            url += `&status=${status}`;
        }

        const response = await fetch(url, {
            method: 'GET',
            credentials: 'include'
        });

        const result = await response.json();

        if (result.success) {
            console.log('任务统计:', result.stats);
            return result;
        } else {
            console.error('获取列表失败:', result.error);
            return null;
        }
    } catch (error) {
        console.error('网络错误:', error);
        return null;
    }
}

// ========================================
// 5. 实时任务状态监控
// ========================================

/**
 * 轮询监控任务状态,直到完成或失败
 * @param {string} taskId - 任务ID
 * @param {function} onProgress - 进度回调函数
 * @param {number} interval - 轮询间隔(毫秒)
 * @returns {Promise<Object>} 最终任务状态
 */
async function monitorTaskProgress(taskId, onProgress, interval = 3000) {
    return new Promise((resolve, reject) => {
        const checkStatus = async () => {
            const task = await getTaskStatus(taskId);

            if (!task) {
                clearInterval(timer);
                reject(new Error('无法获取任务状态'));
                return;
            }

            // 调用进度回调
            if (onProgress) {
                onProgress(task);
            }

            // 检查是否完成
            if (task.status === 'success') {
                clearInterval(timer);
                resolve(task);
            } else if (task.status === 'failed') {
                clearInterval(timer);
                reject(new Error(task.error_message || '任务执行失败'));
            }
        };

        // 立即检查一次
        checkStatus();

        // 开始定时轮询
        const timer = setInterval(checkStatus, interval);

        // 设置超时 (10分钟)
        setTimeout(() => {
            clearInterval(timer);
            reject(new Error('任务超时'));
        }, 600000);
    });
}

// ========================================
// 6. 获取限流统计
// ========================================

/**
 * 获取当前用户的限流统计信息
 * @returns {Promise<Object>} 限流统计
 */
async function getRateLimitStats() {
    try {
        const response = await fetch('/api/tasks/stats', {
            method: 'GET',
            credentials: 'include'
        });

        const result = await response.json();

        if (result.success) {
            return {
                concurrent: result.concurrent_tasks,
                maxConcurrent: result.max_concurrent_tasks,
                rateMinute: result.tasks_in_last_minute,
                maxRateMinute: result.max_tasks_per_minute
            };
        } else {
            return null;
        }
    } catch (error) {
        console.error('获取统计失败:', error);
        return null;
    }
}

// ========================================
// 7. UI集成示例
// ========================================

/**
 * 完整的UI集成示例
 * 展示如何在实际页面中使用这些API
 */
class PublishTaskManager {
    constructor() {
        this.activeTasks = new Map(); // taskId -> task info
    }

    /**
     * 发布单篇文章(带进度显示)
     */
    async publishArticle(title, content, platform = 'zhihu') {
        // 1. 创建任务
        const createResult = await createPublishTask(title, content, platform);

        if (!createResult.success) {
            alert(`创建任务失败: ${createResult.error}`);
            return;
        }

        const taskId = createResult.taskId;

        // 2. 显示进度UI
        this.showProgressUI(taskId, title);

        // 3. 监控任务进度
        try {
            const task = await monitorTaskProgress(taskId, (task) => {
                this.updateProgressUI(taskId, task);
            });

            // 4. 任务成功
            this.showSuccess(taskId, task.result_url);
        } catch (error) {
            // 5. 任务失败
            this.showError(taskId, error.message);
        }
    }

    /**
     * 批量发布文章
     */
    async publishBatch(articles, platform = 'zhihu') {
        // 显示提示
        const confirmMsg = `准备发布${articles.length}篇文章,确认吗?`;
        if (!confirm(confirmMsg)) {
            return;
        }

        // 批量创建任务
        const result = await createBatchPublishTasks(articles, platform);

        alert(`批量创建完成:\n成功: ${result.success_count}\n失败: ${result.failed_count}`);

        // 刷新任务列表
        this.refreshTaskList();
    }

    /**
     * 显示进度UI
     */
    showProgressUI(taskId, title) {
        // 创建进度条元素
        const progressHtml = `
            <div class="task-progress" id="task-${taskId}">
                <h4>${title}</h4>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: 0%"></div>
                </div>
                <p class="status-text">任务已创建...</p>
            </div>
        `;

        // 添加到页面
        document.getElementById('tasks-container').insertAdjacentHTML('beforeend', progressHtml);
    }

    /**
     * 更新进度UI
     */
    updateProgressUI(taskId, task) {
        const element = document.getElementById(`task-${taskId}`);
        if (!element) return;

        const progressFill = element.querySelector('.progress-fill');
        const statusText = element.querySelector('.status-text');

        // 更新进度条
        progressFill.style.width = `${task.progress}%`;

        // 更新状态文本
        const statusMap = {
            'pending': '等待中...',
            'queued': '排队中...',
            'running': `执行中 (${task.progress}%)`,
            'success': '✅ 发布成功!',
            'failed': '❌ 发布失败'
        };
        statusText.textContent = statusMap[task.status] || task.status;
    }

    /**
     * 显示成功
     */
    showSuccess(taskId, url) {
        const element = document.getElementById(`task-${taskId}`);
        if (!element) return;

        element.classList.add('success');
        element.innerHTML += `<a href="${url}" target="_blank">查看文章</a>`;
    }

    /**
     * 显示错误
     */
    showError(taskId, error) {
        const element = document.getElementById(`task-${taskId}`);
        if (!element) return;

        element.classList.add('error');
        const statusText = element.querySelector('.status-text');
        statusText.textContent = `❌ ${error}`;
    }

    /**
     * 刷新任务列表
     */
    async refreshTaskList() {
        const result = await getTaskList(null, 10, 0);

        if (!result) {
            console.error('获取任务列表失败');
            return;
        }

        // 更新统计信息
        this.updateStats(result.stats);

        // 渲染任务列表
        this.renderTaskList(result.tasks);
    }

    /**
     * 更新统计信息显示
     */
    updateStats(stats) {
        document.getElementById('stat-pending').textContent = stats.pending;
        document.getElementById('stat-queued').textContent = stats.queued;
        document.getElementById('stat-running').textContent = stats.running;
        document.getElementById('stat-success').textContent = stats.success;
        document.getElementById('stat-failed').textContent = stats.failed;
    }

    /**
     * 渲染任务列表
     */
    renderTaskList(tasks) {
        const listContainer = document.getElementById('task-list');
        listContainer.innerHTML = '';

        tasks.forEach(task => {
            const taskHtml = `
                <tr class="task-row task-${task.status}">
                    <td>${task.article_title}</td>
                    <td>${task.platform}</td>
                    <td>${task.status}</td>
                    <td>${task.progress}%</td>
                    <td>${task.created_at}</td>
                    <td>
                        ${task.result_url ? `<a href="${task.result_url}" target="_blank">查看</a>` : '-'}
                    </td>
                </tr>
            `;
            listContainer.insertAdjacentHTML('beforeend', taskHtml);
        });
    }
}

// ========================================
// 8. 页面初始化
// ========================================

// 创建全局任务管理器实例
const taskManager = new PublishTaskManager();

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('📦 任务管理器已初始化');

    // 加载任务列表
    taskManager.refreshTaskList();

    // 每30秒自动刷新一次
    setInterval(() => {
        taskManager.refreshTaskList();
    }, 30000);

    // 绑定发布按钮
    document.getElementById('btn-publish').addEventListener('click', function() {
        const title = document.getElementById('article-title').value;
        const content = document.getElementById('article-content').value;

        if (!title || !content) {
            alert('请填写标题和内容');
            return;
        }

        taskManager.publishArticle(title, content);
    });
});

// ========================================
// 9. 导出函数供外部使用
// ========================================

window.PublishAPI = {
    createTask: createPublishTask,
    createBatch: createBatchPublishTasks,
    getStatus: getTaskStatus,
    getList: getTaskList,
    monitor: monitorTaskProgress,
    getStats: getRateLimitStats,
    manager: taskManager
};

console.log('✅ 发布API已加载');
