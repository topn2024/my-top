// 账号配置管理

// 显示账号配置模态框
function showAccountConfig() {
    document.getElementById('account-modal').style.display = 'block';
    setupPlatformSelect();
    loadAccounts();
}

// 设置平台选择器
function setupPlatformSelect() {
    const platformSelect = document.getElementById('acc-platform');
    const customInput = document.getElementById('acc-platform-custom');

    platformSelect.addEventListener('change', function() {
        if (this.value === '自定义') {
            customInput.style.display = 'block';
            customInput.required = true;
        } else {
            customInput.style.display = 'none';
            customInput.required = false;
            customInput.value = '';
        }
    });
}

// 关闭账号配置模态框
function closeAccountConfig() {
    document.getElementById('account-modal').style.display = 'none';
}

// 加载所有账号
async function loadAccounts() {
    try {
        const response = await fetch('/api/accounts');
        const data = await response.json();

        if (data.success) {
            displayAccounts(data.accounts);
        } else {
            alert('加载账号失败: ' + (data.error || '未知错误'));
        }
    } catch (error) {
        console.error('Load accounts error:', error);
        alert('加载账号失败: ' + error.message);
    }
}

// 显示账号列表
function displayAccounts(accounts) {
    const container = document.getElementById('accounts-container');
    const countSpan = document.getElementById('account-count');

    countSpan.textContent = `(${accounts.length})`;

    if (accounts.length === 0) {
        container.innerHTML = '<p class="no-accounts">暂无配置账号</p>';
        return;
    }

    let html = '<table class="accounts-table"><thead><tr>' +
        '<th>平台</th><th>用户名</th><th>密码</th><th>备注</th><th>状态</th><th>操作</th>' +
        '</tr></thead><tbody>';

    accounts.forEach(account => {
        const password = account.password ? '******' : '-';
        const notes = account.notes || '-';
        const status = account.status || 'unknown';
        const statusText = status === 'success' ? '✓ 已验证' :
                          status === 'failed' ? '✗ 失败' : '未测试';
        const statusClass = status === 'success' ? 'status-success' :
                           status === 'failed' ? 'status-failed' : 'status-unknown';

        html += `<tr>
            <td>${escapeHtml(account.platform)}</td>
            <td>${escapeHtml(account.username)}</td>
            <td>${password}</td>
            <td>${escapeHtml(notes)}</td>
            <td><span class="${statusClass}">${statusText}</span></td>
            <td>
                <button class="btn-test" onclick="testAccount(${account.id})">测试</button>
                <button class="btn-delete" onclick="deleteAccount(${account.id})">删除</button>
            </td>
        </tr>`;
    });

    html += '</tbody></table>';
    container.innerHTML = html;
}

// 添加账号
async function addAccount(event) {
    event.preventDefault();

    let platform = document.getElementById('acc-platform').value.trim();
    const customPlatform = document.getElementById('acc-platform-custom').value.trim();
    const username = document.getElementById('acc-username').value.trim();
    const password = document.getElementById('acc-password').value;
    const notes = document.getElementById('acc-notes').value.trim();

    // 如果选择了自定义，使用自定义平台名称
    if (platform === '自定义' && customPlatform) {
        platform = customPlatform;
    }

    if (!platform || !username || platform === '自定义') {
        alert('请选择平台/填写自定义平台名称和用户名');
        return;
    }

    if (!password) {
        alert('请输入密码');
        return;
    }

    try {
        const response = await fetch('/api/accounts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                platform: platform,
                username: username,
                password: password,
                notes: notes
            })
        });

        const data = await response.json();

        if (data.success) {
            alert('账号添加成功');
            document.getElementById('add-account-form').reset();
            loadAccounts();
        } else {
            alert('添加失败: ' + (data.error || '未知错误'));
        }
    } catch (error) {
        console.error('Add account error:', error);
        alert('添加失败: ' + error.message);
    }
}

// 删除账号
async function deleteAccount(accountId) {
    if (!confirm('确定要删除这个账号吗?')) {
        return;
    }

    try {
        const response = await fetch(`/api/accounts/${accountId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            alert('账号删除成功');
            loadAccounts();
        } else {
            alert('删除失败: ' + (data.error || '未知错误'));
        }
    } catch (error) {
        console.error('Delete account error:', error);
        alert('删除失败: ' + error.message);
    }
}

// 批量导入账号
async function importAccounts(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
        showLoading('正在导入账号...');

        const response = await fetch('/api/accounts/import', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        hideLoading();

        if (data.success) {
            alert(`成功导入 ${data.count} 个账号`);
            loadAccounts();
        } else {
            alert('导入失败: ' + (data.error || '未知错误'));
        }
    } catch (error) {
        hideLoading();
        console.error('Import accounts error:', error);
        alert('导入失败: ' + error.message);
    } finally {
        event.target.value = '';
    }
}

// HTML转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 测试账号登录
async function testAccount(accountId) {
    try {
        showLoading('正在测试登录...');

        const response = await fetch(`/api/accounts/${accountId}/test`, {
            method: 'POST'
        });

        hideLoading();

        const data = await response.json();

        if (data.success) {
            showTestResult('success', '登录测试成功', data.message || '账号验证通过');
            // 重新加载账号列表以更新状态
            loadAccounts();
        } else {
            showTestResult('failed', '登录测试失败', data.message || data.error || '未知错误');
        }
    } catch (error) {
        hideLoading();
        console.error('Test account error:', error);
        showTestResult('failed', '登录测试失败', error.message);
    }
}

// 显示测试结果
function showTestResult(status, title, message) {
    const modal = document.getElementById('test-result-modal');
    const titleEl = document.getElementById('test-result-title');
    const bodyEl = document.getElementById('test-result-body');

    const icon = status === 'success' ? '✓' : '✗';
    const statusClass = status === 'success' ? 'test-success' : 'test-failed';

    titleEl.textContent = `${icon} ${title}`;
    bodyEl.innerHTML = `<p class="${statusClass}">${escapeHtml(message)}</p>`;

    modal.style.display = 'block';
}

// 关闭测试结果
function closeTestResult() {
    document.getElementById('test-result-modal').style.display = 'none';
}

// 点击模态框外部关闭
window.onclick = function(event) {
    const modal = document.getElementById('account-modal');
    const testModal = document.getElementById('test-result-modal');

    if (event.target === modal) {
        closeAccountConfig();
    }
    if (event.target === testModal) {
        closeTestResult();
    }
}
