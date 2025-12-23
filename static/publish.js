// 发布页面逻辑

// 页面加载时设置
window.addEventListener('load', () => {
    const state = WorkflowState.get();

    // 1. 加载当前用户信息
    loadCurrentUser();

    // 2. 显示文章选择列表（如果有文章）
    if (state.articles && state.articles.length > 0) {
        displayArticleSelection(state.articles);
    } else {
        // 没有文章时显示提示
        const selectionDiv = document.getElementById('article-selection');
        if (selectionDiv) {
            selectionDiv.innerHTML = '<p style="color: #999; text-align: center; padding: 20px;">暂无文章，请先完成文章生成</p>';
        }
    }

    // 3. 加载发布历史（不管有没有文章都要加载）
    publishHistoryManager.init();
});

// 加载当前用户信息
async function loadCurrentUser() {
    try {
        const usernameElement = document.getElementById('username');
        if (!usernameElement) {
            console.warn('username 元素不存在，跳过用户信息加载');
            return;
        }

        const response = await fetch('/api/auth/me', {
            method: 'GET',
            credentials: 'same-origin'
        });

        if (response.ok) {
            const data = await response.json();
            if (data.success && data.user) {
                usernameElement.textContent = data.user.username;
            } else {
                usernameElement.textContent = '游客';
            }
        } else {
            usernameElement.textContent = '游客';
        }
    } catch (error) {
        console.error('加载用户信息失败:', error);
        const usernameElement = document.getElementById('username');
        if (usernameElement) {
            usernameElement.textContent = '游客';
        }
    }
}

// 显示文章选择
function displayArticleSelection(articles) {
    const container = document.getElementById('article-selection');
    container.innerHTML = '';

    articles.forEach((article, index) => {
        const item = document.createElement('div');
        item.className = 'article-select-item';
        item.innerHTML = `
            <input type="checkbox" id="article-${index}" value="${index}" checked>
            <label for="article-${index}">
                <strong>${article.title}</strong>
                <span class="article-type-tag">${article.type}</span>
            </label>
        `;
        container.appendChild(item);
    });
}

// 检查知乎Cookie有效性
async function checkZhihuCookie() {
    console.log('[发布流程] 检查知乎Cookie有效性...');
    try {
        const response = await fetch('/api/zhihu/check_cookie', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        });

        const data = await response.json();
        console.log('[发布流程] Cookie检查结果:', data);
        return data;
    } catch (error) {
        console.error('[发布流程] Cookie检查失败:', error);
        return {
            success: false,
            cookie_valid: false,
            requireQRLogin: true,
            message: '检查Cookie时发生错误'
        };
    }
}

// 开始发布
async function startPublish() {
    console.log('[发布流程] ========== 开始发布流程 ==========');
    console.log('[发布流程] 时间:', new Date().toISOString());

    const state = WorkflowState.get();
    console.log('[发布流程] 当前工作流状态:', state);

    // 获取选中的文章
    const selectedArticles = [];
    state.articles.forEach((article, index) => {
        const checkbox = document.getElementById(`article-${index}`);
        if (checkbox && checkbox.checked) {
            selectedArticles.push(article);
        }
    });

    console.log(`[发布流程] 用户选中了 ${selectedArticles.length} 篇文章`);

    if (selectedArticles.length === 0) {
        console.warn('[发布流程] 未选择任何文章，中止发布');
        alert('请至少选择一篇文章发布');
        return;
    }

    // 获取选中的平台
    const selectedPlatforms = [];
    const platformCheckboxes = document.querySelectorAll('#platform-list input[type="checkbox"]:checked');
    platformCheckboxes.forEach(cb => {
        selectedPlatforms.push(cb.value);
    });

    console.log(`[发布流程] 用户选中的平台: ${selectedPlatforms.join(', ')}`);

    if (selectedPlatforms.length === 0) {
        console.warn('[发布流程] 未选择任何平台，中止发布');
        alert('请至少选择一个发布平台');
        return;
    }

    // 目前只支持知乎
    if (selectedPlatforms.includes('知乎')) {
        console.log('[发布流程] 准备发布到知乎，先检查登录状态...');

        // 先检查Cookie是否有效
        showLoading('正在检查登录状态...');
        const cookieCheck = await checkZhihuCookie();
        hideLoading();

        if (cookieCheck.requireQRLogin) {
            // Cookie无效，需要扫码登录
            console.log('[发布流程] Cookie无效，需要扫码登录');

            // 显示提示并开始扫码登录
            const confirmLogin = confirm(`${cookieCheck.message}\n\n是否现在扫码登录？`);
            if (!confirmLogin) {
                console.log('[发布流程] 用户取消扫码登录');
                return;
            }

            // 开始二维码登录流程，登录成功后继续发布
            await handleQRLoginAndPublish(selectedArticles);
        } else {
            // Cookie有效，直接发布
            console.log('[发布流程] Cookie有效，开始批量发布');
            await publishBatchToZhihu(selectedArticles);
        }

        console.log('[发布流程] ========== 发布流程结束 ==========');
    } else {
        console.warn('[发布流程] 选中的平台不支持:', selectedPlatforms);
        alert('目前仅支持发布到知乎平台，其他平台即将开放');
    }
}

// 处理二维码登录并在成功后发布
async function handleQRLoginAndPublish(articles) {
    try {
        showLoading('正在获取登录二维码...');

        // 请求二维码
        const response = await fetch('/api/zhihu/qr_login/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        });

        const data = await response.json();

        if (!data.success) {
            hideLoading();
            alert(`获取二维码失败：${data.error || '未知错误'}`);
            return;
        }

        // 显示二维码弹窗，登录成功后发布文章
        showQRCodeModalForPublish(data.qr_code, data.session_id, articles);

    } catch (error) {
        hideLoading();
        alert('获取二维码失败: ' + error.message);
    }
}

// 显示二维码弹窗（发布专用版本）
function showQRCodeModalForPublish(qrCodeDataUrl, sessionId, articles) {
    hideLoading();

    // 创建模态框
    const modal = document.createElement('div');
    modal.id = 'qr-login-modal-publish';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10000;
    `;

    modal.innerHTML = `
        <div style="background: white; padding: 30px; border-radius: 10px; text-align: center; max-width: 400px;">
            <h3 style="margin-bottom: 20px;">📱 扫码登录知乎</h3>
            <img src="${qrCodeDataUrl}" alt="登录二维码" style="width: 250px; height: 250px; margin: 20px auto; display: block; border: 1px solid #ddd; border-radius: 8px;">
            <p style="color: #666; margin: 15px 0;">请使用<strong>知乎APP</strong>扫描二维码登录</p>
            <p id="qr-login-status-publish" style="color: #3b82f6; font-weight: bold;">⏳ 等待扫码中...</p>
            <p style="color: #999; font-size: 12px; margin-top: 10px;">登录成功后将自动开始发布</p>
            <button id="qr-cancel-btn-publish" style="margin-top: 20px; padding: 10px 30px; background: #ef4444; color: white; border: none; border-radius: 5px; cursor: pointer;">取消</button>
        </div>
    `;

    document.body.appendChild(modal);

    // 取消按钮
    document.getElementById('qr-cancel-btn-publish').addEventListener('click', () => {
        stopQRLoginPolling();
        document.body.removeChild(modal);
    });

    // 开始轮询检查登录状态
    startQRLoginPollingForPublish(sessionId, articles, modal);
}

// 轮询检查登录状态（发布专用版本）
function startQRLoginPollingForPublish(sessionId, articles, modal) {
    let pollCount = 0;
    const maxPolls = 60; // 最多轮询60次 (2分钟)

    qrLoginPollingInterval = setInterval(async () => {
        pollCount++;

        if (pollCount > maxPolls) {
            stopQRLoginPolling();
            const statusEl = document.getElementById('qr-login-status-publish');
            if (statusEl) {
                statusEl.textContent = '❌ 登录超时，请重试';
                statusEl.style.color = '#ef4444';
            }
            return;
        }

        try {
            const response = await fetch('/api/zhihu/qr_login/check', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({ session_id: sessionId })
            });

            const data = await response.json();

            if (data.success && data.logged_in) {
                // 登录成功
                stopQRLoginPolling();
                const statusEl = document.getElementById('qr-login-status-publish');
                if (statusEl) {
                    statusEl.textContent = '✅ 登录成功！正在发布...';
                    statusEl.style.color = '#10b981';
                }

                // 等待1秒后关闭弹窗并开始发布
                setTimeout(async () => {
                    if (modal && modal.parentNode) {
                        document.body.removeChild(modal);
                    }
                    console.log('[发布流程] 二维码登录成功，开始批量发布');
                    await publishBatchToZhihu(articles);
                }, 1000);
            }

        } catch (error) {
            console.error('检查登录状态失败:', error);
        }

    }, 2000); // 每2秒检查一次
}

// 批量发布到知乎（异步任务队列版本）
async function publishBatchToZhihu(articles) {
    console.log(`[发布流程] 开始批量发布流程，共 ${articles.length} 篇文章`);
    console.log(`[发布流程] 文章列表:`, articles.map(a => ({ title: a.title, id: a.id })));

    if (!confirm(`确定要将 ${articles.length} 篇文章发布到知乎吗？\n\n这将创建${articles.length}个后台任务，您可以关闭页面，任务会继续在后台执行。`)) {
        console.log('[发布流程] 用户取消发布');
        return;
    }

    console.log('[发布流程] 用户确认发布，开始创建任务...');
    showLoading(`正在创建发布任务...`);

    try {
        const requestBody = {
            articles: articles.map(article => ({
                title: article.title,
                content: article.content,
                article_id: article.id || 0
            }))
        };

        console.log('[发布流程] 发送批量发布请求到后端API: /api/publish_zhihu_batch');
        console.log('[发布流程] 请求体:', { article_count: requestBody.articles.length });

        const startTime = Date.now();

        // 使用批量发布API
        const response = await fetch('/api/publish_zhihu_batch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',  // 包含session cookie
            body: JSON.stringify(requestBody)
        });

        const requestDuration = Date.now() - startTime;
        console.log(`[发布流程] 后端API响应完成，耗时 ${requestDuration}ms，状态码: ${response.status}`);

        // 检查响应状态
        if (response.status === 401) {
            hideLoading();
            alert('请先登录！');
            window.location.href = '/login';
            return;
        }

        if (!response.ok) {
            const errorText = await response.text();
            console.error('[发布流程] API返回错误:', errorText);
            hideLoading();
            const errorMsg = errorText ? String(errorText).substring(0, 100) : '未知错误';
            alert(`请求失败 (${response.status}): ${errorMsg}`);
            return;
        }

        const data = await response.json();
        console.log('[发布流程] 后端返回数据:', data);
        hideLoading();
        if (data.success || data.success_count > 0) {
            console.log(`[发布流程] 发布完成！成功: ${data.success_count}, 失败: ${data.failed_count}`);
            console.log('[发布流程] 发布结果详情:', data.results);

            // 构建结果消息
            let message = `批量发布完成！

` +
                          `成功: ${data.success_count} 篇
` +
                          `失败: ${data.failed_count} 篇

`;
            
            // 显示详细结果
            if (data.results && data.results.length > 0) {
                message += '详细结果：\n';
                data.results.forEach((item, index) => {
                    // 适配后端返回格式：{article_title: '', result: {success: bool, ...}}
                    const result = item.result || item;
                    let title = item.article_title || item.title || '未知标题';
                    // 确保title是字符串
                    title = String(title || '未知标题');
                    const status = result.success ? '✓' : '✗';
                    const displayTitle = title.length > 30 ? title.substring(0, 30) + '...' : title;
                    message += `${status} ${displayTitle}\n`;
                    if (!result.success && (result.message || result.error)) {
                        message += `   错误: ${result.message || result.error}\n`;
                    }
                });
            }

            alert(message);

            // 刷新发布历史
            if (typeof publishHistoryManager !== 'undefined') {
                console.log('[发布流程] 刷新发布历史');
                publishHistoryManager.refresh();
            }

        } else {
            console.error('[发布流程] 发布失败:', data.error);
            alert(`发布失败：${data.error || '未知错误'}`);
        }

    } catch (error) {
        console.error('[发布流程] 发布流程异常:', error);
        hideLoading();
        alert('创建任务失败: ' + error.message);
    }
}

// 发布单篇文章到知乎（不显示弹窗）
async function publishSingleArticleToZhihu(article) {
    try {
        const response = await fetch('/api/publish_zhihu', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: article.title,
                content: article.content,
                article_id: article.id || 0  // 传递文章ID用于归档
            })
        });

        // 先尝试解析JSON响应
        let data;
        try {
            data = await response.json();
        } catch (e) {
            return {
                success: false,
                message: `服务器响应格式错误 (HTTP ${response.status})`
            };
        }

        // 检查HTTP状态
        if (response.status === 401) {
            return {
                success: false,
                message: data.error || '登录已过期，请重新登录'
            };
        }

        if (!response.ok) {
            return {
                success: false,
                message: data.error || data.message || `服务器返回错误 (${response.status})`
            };
        }

        // 检查是否需要二维码登录
        if (data.requireQRLogin) {
            // 对于批量发布，第一篇需要QR登录后，后续文章会复用Cookie
            const qrLoginResult = await handleQRLoginForBatch(article);
            return qrLoginResult;
        }

        return {
            success: data.success,
            message: data.message || data.error || (data.success ? '发布成功' : '发布失败')
        };

    } catch (error) {
        return {
            success: false,
            message: error.message
        };
    }
}

// 发布到知乎（单篇，带确认弹窗）
async function publishToZhihu(article) {
    if (!confirm(`确定要将文章《${article.title}》发布到知乎吗？`)) {
        return;
    }

    showLoading('正在发布到知乎...');

    try {
        const response = await fetch('/api/publish_zhihu', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: article.title,
                content: article.content,
                article_id: article.id || 0  // 传递文章ID用于归档
            })
        });

        // 先尝试解析JSON响应
        let data;
        try {
            data = await response.json();
        } catch (e) {
            hideLoading();
            alert(`发布失败：服务器响应格式错误 (HTTP ${response.status})`);
            return;
        }

        hideLoading();

        // 检查HTTP状态
        if (response.status === 401) {
            alert(data.error || '您的登录已过期，请重新登录');
            window.location.href = '/login';
            return;
        }

        if (!response.ok) {
            alert(`发布失败：${data.error || data.message || '服务器返回错误 (' + response.status + ')'}`);
            return;
        }

        // 检查是否需要二维码登录
        if (data.requireQRLogin) {
            await handleQRLogin(article);
            return;
        }

        if (data.success) {
            alert(`发布成功！\n${data.message || ''}`);
            // 重新加载发布历史
            publishHistoryManager.refresh();
        } else {
            alert(`发布失败：${data.message || data.error || '未知错误'}`);
        }
    } catch (error) {
        hideLoading();
        alert('发布失败: ' + error.message);
    }
}

// 处理二维码登录（用于批量发布）
async function handleQRLoginForBatch(article) {
    return new Promise((resolve, reject) => {
        handleQRLoginWithCallback(article, (success, message) => {
            if (success) {
                // 登录成功后，重新发布这篇文章
                publishSingleArticleToZhihu(article).then(resolve).catch(reject);
            } else {
                resolve({
                    success: false,
                    message: message || '二维码登录失败'
                });
            }
        });
    });
}

// 处理二维码登录
async function handleQRLogin(article, callback) {
    await handleQRLoginWithCallback(article, callback);
}

// 处理二维码登录（通用版本，带回调）
async function handleQRLoginWithCallback(article, callback) {
    try {
        showLoading('正在获取登录二维码...');

        // 请求二维码
        const response = await fetch('/api/zhihu/qr_login/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (!data.success) {
            hideLoading();
            const errorMsg = `获取二维码失败：${data.error || '未知错误'}`;
            alert(errorMsg);
            if (callback) callback(false, errorMsg);
            return;
        }

        // 显示二维码弹窗
        showQRCodeModal(data.qr_code, data.session_id, article, callback);

    } catch (error) {
        hideLoading();
        const errorMsg = '获取二维码失败: ' + error.message;
        alert(errorMsg);
        if (callback) callback(false, errorMsg);
    }
}

// 显示二维码弹窗
function showQRCodeModal(qrCodeDataUrl, sessionId, article, callback) {
    hideLoading();

    // 创建模态框
    const modal = document.createElement('div');
    modal.id = 'qr-login-modal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10000;
    `;

    modal.innerHTML = `
        <div style="background: white; padding: 30px; border-radius: 10px; text-align: center; max-width: 400px;">
            <h3 style="margin-bottom: 20px;">扫码登录知乎</h3>
            <img src="${qrCodeDataUrl}" alt="登录二维码" style="width: 250px; height: 250px; margin: 20px auto; display: block; border: 1px solid #ddd;">
            <p style="color: #666; margin: 15px 0;">请使用知乎APP扫描二维码登录</p>
            <p id="qr-login-status" style="color: #3b82f6; font-weight: bold;">等待扫码中...</p>
            <button id="qr-cancel-btn" style="margin-top: 20px; padding: 10px 30px; background: #ef4444; color: white; border: none; border-radius: 5px; cursor: pointer;">取消</button>
        </div>
    `;

    document.body.appendChild(modal);

    // 取消按钮
    document.getElementById('qr-cancel-btn').addEventListener('click', () => {
        stopQRLoginPolling();
        document.body.removeChild(modal);
        if (callback) callback(false, '用户取消登录');
    });

    // 开始轮询检查登录状态
    startQRLoginPolling(sessionId, article, modal, callback);
}

// 轮询检查登录状态
let qrLoginPollingInterval = null;

function startQRLoginPolling(sessionId, article, modal, callback) {
    let pollCount = 0;
    const maxPolls = 60; // 最多轮询60次 (2分钟)

    qrLoginPollingInterval = setInterval(async () => {
        pollCount++;

        if (pollCount > maxPolls) {
            stopQRLoginPolling();
            document.getElementById('qr-login-status').textContent = '登录超时，请重试';
            document.getElementById('qr-login-status').style.color = '#ef4444';
            if (callback) callback(false, '登录超时');
            return;
        }

        try {
            const response = await fetch('/api/zhihu/qr_login/check', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ session_id: sessionId })
            });

            const data = await response.json();

            if (data.success && data.logged_in) {
                // 登录成功
                stopQRLoginPolling();
                document.getElementById('qr-login-status').textContent = '✓ 登录成功！正在发布...';
                document.getElementById('qr-login-status').style.color = '#10b981';

                // 等待1秒后关闭弹窗并回调
                setTimeout(async () => {
                    document.body.removeChild(modal);

                    if (callback) {
                        // 如果有回调，使用回调
                        callback(true, '登录成功');
                    } else {
                        // 否则直接重新发布
                        await publishToZhihu(article);
                    }
                }, 1000);
            }

        } catch (error) {
            console.error('检查登录状态失败:', error);
        }

    }, 2000); // 每2秒检查一次
}

function stopQRLoginPolling() {
    if (qrLoginPollingInterval) {
        clearInterval(qrLoginPollingInterval);
        qrLoginPollingInterval = null;
    }
}

// 任务监控面板
function showTaskMonitor(taskResults) {
    // 创建监控面板
    const monitorPanel = document.createElement('div');
    monitorPanel.id = 'task-monitor-panel';
    monitorPanel.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 400px;
        max-height: 500px;
        background: white;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        padding: 20px;
        z-index: 9999;
        overflow-y: auto;
    `;

    const taskIds = taskResults
        .filter(r => r.result && r.result.task_id)
        .map(r => r.result.task_id);

    monitorPanel.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
            <h3 style="margin: 0;">发布任务监控</h3>
            <button onclick="closeTaskMonitor()" style="background: none; border: none; font-size: 20px; cursor: pointer;">&times;</button>
        </div>
        <div id="task-list" style="margin-top: 10px;"></div>
        <div style="margin-top: 15px; text-align: center;">
            <button onclick="refreshTaskMonitor()" style="padding: 8px 16px; background: #3b82f6; color: white; border: none; border-radius: 5px; cursor: pointer;">刷新状态</button>
        </div>
    `;

    document.body.appendChild(monitorPanel);

    // 保存任务ID到全局
    window.monitoringTasks = taskIds;

    // 首次加载任务状态
    refreshTaskMonitor();

    // 自动刷新（每5秒）
    window.taskMonitorInterval = setInterval(refreshTaskMonitor, 5000);
}

function closeTaskMonitor() {
    const panel = document.getElementById('task-monitor-panel');
    if (panel) {
        panel.remove();
    }
    if (window.taskMonitorInterval) {
        clearInterval(window.taskMonitorInterval);
    }
}

async function refreshTaskMonitor() {
    if (!window.monitoringTasks || window.monitoringTasks.length === 0) {
        return;
    }

    const taskList = document.getElementById('task-list');
    if (!taskList) return;

    taskList.innerHTML = '<div style="text-align: center; color: #666;">加载中...</div>';

    try {
        // 获取所有任务状态
        const tasks = await Promise.all(
            window.monitoringTasks.map(taskId =>
                fetch(`/api/publish_task/${taskId}`)
                    .then(r => r.json())
                    .catch(() => ({ success: false, error: '获取失败' }))
            )
        );

        let html = '';
        let allCompleted = true;

        tasks.forEach((response, index) => {
            if (!response.success) {
                html += `<div style="padding: 10px; margin: 5px 0; border: 1px solid #ccc; border-radius: 5px;">
                    <div style="color: #666;">任务 ${index + 1}: 获取状态失败</div>
                </div>`;
                return;
            }

            const task = response.task;
            const statusColors = {
                'pending': '#f59e0b',
                'queued': '#3b82f6',
                'running': '#10b981',
                'success': '#22c55e',
                'failed': '#ef4444'
            };

            const statusTexts = {
                'pending': '等待中',
                'queued': '队列中',
                'running': '发布中',
                'success': '成功',
                'failed': '失败'
            };

            const statusColor = statusColors[task.status] || '#666';
            const statusText = statusTexts[task.status] || task.status;

            if (task.status !== 'success' && task.status !== 'failed') {
                allCompleted = false;
            }

            const taskTitle = String(task.article_title || '未知标题');
            const displayTaskTitle = taskTitle.length > 30 ? taskTitle.substring(0, 30) + '...' : taskTitle;

            html += `
                <div style="padding: 10px; margin: 5px 0; border: 1px solid ${statusColor}; border-radius: 5px; background: ${statusColor}15;">
                    <div style="font-weight: bold; margin-bottom: 5px;">${displayTaskTitle}</div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: ${statusColor}; font-weight: bold;">${statusText}</span>
                        ${task.progress ? `<span style="color: #666; font-size: 12px;">${task.progress}%</span>` : ''}
                    </div>
                    ${task.status === 'success' && task.result_url ? `<div style="margin-top: 5px;"><a href="${task.result_url}" target="_blank" style="color: #3b82f6; font-size: 12px;">查看文章</a></div>` : ''}
                    ${task.status === 'failed' && task.error_message ? `<div style="margin-top: 5px; color: #ef4444; font-size: 12px;">${task.error_message}</div>` : ''}
                </div>
            `;
        });

        taskList.innerHTML = html;

        // 如果全部完成，停止自动刷新
        if (allCompleted) {
            if (window.taskMonitorInterval) {
                clearInterval(window.taskMonitorInterval);
            }
        }

    } catch (error) {
        taskList.innerHTML = `<div style="color: #ef4444;">刷新失败: ${error.message}</div>`;
    }
}

// 加载动画
function showLoading(text = '处理中...') {
    document.getElementById('loading-text').textContent = text;
    document.getElementById('loading').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}
