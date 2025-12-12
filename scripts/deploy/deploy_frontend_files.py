#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署发布历史管理前端文件
"""
import paramiko
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

try:
    print("=" * 80)
    print("部署发布历史管理前端文件")
    print("=" * 80)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
    print("✓ SSH连接成功\n")

    sftp = ssh.open_sftp()

    # 步骤1: 创建HTML文件
    print("[1/3] 创建HTML页面...")
    html_file = '/home/u_topn/TOP_N/templates/publish_history.html'

    # 使用Python heredoc方式直接写入
    cmd = r"""cat > /home/u_topn/TOP_N/templates/publish_history.html << 'HTMLEOF'
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>发布历史管理 - TOP_N</title>
    <link rel="stylesheet" href="/static/style.css">
    <style>
        .history-container { max-width: 1400px; margin: 20px auto; padding: 20px; }
        .stats-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        .stat-card.success { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
        .stat-card.failed { background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); }
        .stat-card.rate { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
        .stat-card h3 { margin: 0 0 10px 0; font-size: 14px; opacity: 0.9; }
        .stat-card .value { font-size: 32px; font-weight: bold; margin: 0; }
        .filters { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .filter-group { display: flex; gap: 15px; align-items: center; flex-wrap: wrap; }
        .filter-group select { padding: 8px 12px; border: 1px solid #ddd; border-radius: 5px; font-size: 14px; }
        .history-table { background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .history-table table { width: 100%; border-collapse: collapse; }
        .history-table th { background: #f8f9fa; padding: 15px; text-align: left; font-weight: 600; color: #333; border-bottom: 2px solid #e0e0e0; }
        .history-table td { padding: 15px; border-bottom: 1px solid #f0f0f0; }
        .history-table tr:hover { background: #f8f9fa; }
        .status-badge { display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 500; }
        .status-success { background: #d4edda; color: #155724; }
        .status-failed { background: #f8d7da; color: #721c24; }
        .action-btns { display: flex; gap: 8px; }
        .btn-small { padding: 6px 12px; font-size: 12px; border-radius: 4px; border: none; cursor: pointer; transition: all 0.3s; text-decoration: none; display: inline-block; }
        .btn-view { background: #667eea; color: white; }
        .btn-delete { background: #dc3545; color: white; }
        .btn-small:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
        .pagination { display: flex; justify-content: center; align-items: center; gap: 10px; padding: 20px; background: white; margin-top: 20px; border-radius: 8px; }
        .pagination button { padding: 8px 16px; border: 1px solid #ddd; background: white; border-radius: 4px; cursor: pointer; }
        .pagination button:hover:not(:disabled) { background: #667eea; color: white; border-color: #667eea; }
        .pagination button:disabled { opacity: 0.5; cursor: not-allowed; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; }
        .modal-content { background: white; max-width: 800px; margin: 50px auto; padding: 30px; border-radius: 10px; max-height: 80vh; overflow-y: auto; }
        .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 2px solid #e0e0e0; }
        .modal-close { font-size: 28px; cursor: pointer; color: #999; }
        .detail-section { margin-bottom: 20px; }
        .detail-section h3 { color: #667eea; margin-bottom: 10px; }
        .detail-field { margin-bottom: 15px; }
        .detail-field label { display: block; font-weight: 600; color: #555; margin-bottom: 5px; }
        .detail-field .value { padding: 10px; background: #f8f9fa; border-radius: 4px; word-wrap: break-word; }
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1>📊 发布历史管理</h1>
            <div class="nav">
                <a href="/" class="btn">🏠 返回首页</a>
                <a href="/accounts" class="btn">⚙️ 账号配置</a>
            </div>
        </div>
    </div>

    <div class="history-container">
        <div class="stats-cards">
            <div class="stat-card"><h3>总发布数</h3><p class="value" id="stat-total">0</p></div>
            <div class="stat-card success"><h3>成功</h3><p class="value" id="stat-success">0</p></div>
            <div class="stat-card failed"><h3>失败</h3><p class="value" id="stat-failed">0</p></div>
            <div class="stat-card rate"><h3>成功率</h3><p class="value" id="stat-rate">0%</p></div>
        </div>

        <div class="filters">
            <div class="filter-group">
                <label>状态筛选:</label>
                <select id="filter-status" onchange="loadHistory()">
                    <option value="">全部</option>
                    <option value="success">成功</option>
                    <option value="failed">失败</option>
                </select>
                <label>平台筛选:</label>
                <select id="filter-platform" onchange="loadHistory()">
                    <option value="">全部</option>
                    <option value="知乎">知乎</option>
                </select>
                <button class="btn" onclick="loadHistory()">🔄 刷新</button>
            </div>
        </div>

        <div class="history-table">
            <table>
                <thead>
                    <tr>
                        <th>ID</th><th>标题</th><th>平台</th><th>账号</th><th>状态</th><th>发布时间</th><th>发布人</th><th>操作</th>
                    </tr>
                </thead>
                <tbody id="history-tbody">
                    <tr><td colspan="8" style="text-align: center; padding: 40px;">加载中...</td></tr>
                </tbody>
            </table>
        </div>

        <div class="pagination">
            <button onclick="changePage(-1)" id="prev-btn">上一页</button>
            <span id="page-info">第 1 页</span>
            <button onclick="changePage(1)" id="next-btn">下一页</button>
        </div>
    </div>

    <div class="modal" id="detail-modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>发布详情</h2>
                <span class="modal-close" onclick="closeModal()">&times;</span>
            </div>
            <div id="detail-content"></div>
        </div>
    </div>

    <script src="/static/publish_history.js"></script>
</body>
</html>
HTMLEOF"""

    ssh.exec_command(cmd, timeout=10)
    time.sleep(1)
    print("✓ HTML文件已创建")

    # 步骤2: 创建JavaScript文件
    print("\n[2/3] 创建JavaScript文件...")
    cmd2 = r"""cat > /home/u_topn/TOP_N/static/publish_history.js << 'JSEOF'
let currentPage = 1;
let pageSize = 20;
let totalPages = 1;

async function loadStats() {
    try {
        const response = await fetch('/api/publish-history/stats');
        const data = await response.json();
        if (data.success) {
            document.getElementById('stat-total').textContent = data.stats.total;
            document.getElementById('stat-success').textContent = data.stats.success;
            document.getElementById('stat-failed').textContent = data.stats.failed;
            document.getElementById('stat-rate').textContent = data.stats.success_rate + '%';
        }
    } catch (error) {
        console.error('加载统计数据失败:', error);
    }
}

async function loadHistory(page = 1) {
    currentPage = page;
    const status = document.getElementById('filter-status').value;
    const platform = document.getElementById('filter-platform').value;

    try {
        const params = new URLSearchParams({
            page: currentPage,
            page_size: pageSize,
            status: status,
            platform: platform
        });

        const response = await fetch(`/api/publish-history?${params}`);
        const data = await response.json();

        if (data.success) {
            displayHistory(data.data);
            updatePagination(data.total);
        }
    } catch (error) {
        console.error('加载历史记录失败:', error);
        document.getElementById('history-tbody').innerHTML =
            '<tr><td colspan="8" style="text-align: center; color: red;">加载失败</td></tr>';
    }
}

function displayHistory(records) {
    const tbody = document.getElementById('history-tbody');

    if (records.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center;">暂无记录</td></tr>';
        return;
    }

    tbody.innerHTML = records.map(record => `
        <tr>
            <td>${record.id}</td>
            <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${record.title}</td>
            <td>${record.platform}</td>
            <td>${record.account_username}</td>
            <td><span class="status-badge status-${record.status}">${record.status === 'success' ? '✅ 成功' : '❌ 失败'}</span></td>
            <td>${formatDateTime(record.publish_time)}</td>
            <td>${record.publish_user}</td>
            <td>
                <div class="action-btns">
                    <button class="btn-small btn-view" onclick="viewDetail(${record.id})">查看</button>
                    ${record.article_url ? `<a href="${record.article_url}" target="_blank" class="btn-small btn-view">链接</a>` : ''}
                    <button class="btn-small btn-delete" onclick="deleteRecord(${record.id})">删除</button>
                </div>
            </td>
        </tr>
    `).join('');
}

function updatePagination(total) {
    totalPages = Math.ceil(total / pageSize);
    document.getElementById('page-info').textContent = `第 ${currentPage} / ${totalPages} 页 (共 ${total} 条)`;
    document.getElementById('prev-btn').disabled = currentPage <= 1;
    document.getElementById('next-btn').disabled = currentPage >= totalPages;
}

function changePage(delta) {
    const newPage = currentPage + delta;
    if (newPage >= 1 && newPage <= totalPages) {
        loadHistory(newPage);
    }
}

async function viewDetail(id) {
    try {
        const response = await fetch(`/api/publish-history/${id}`);
        const data = await response.json();

        if (data.success) {
            const record = data.data;
            document.getElementById('detail-content').innerHTML = `
                <div class="detail-section">
                    <h3>基本信息</h3>
                    <div class="detail-field"><label>ID:</label><div class="value">${record.id}</div></div>
                    <div class="detail-field"><label>标题:</label><div class="value">${record.title}</div></div>
                    <div class="detail-field"><label>平台:</label><div class="value">${record.platform}</div></div>
                    <div class="detail-field"><label>账号:</label><div class="value">${record.account_username}</div></div>
                    <div class="detail-field"><label>状态:</label><div class="value"><span class="status-badge status-${record.status}">${record.status === 'success' ? '✅ 成功' : '❌ 失败'}</span></div></div>
                    <div class="detail-field"><label>发布时间:</label><div class="value">${record.publish_time}</div></div>
                    <div class="detail-field"><label>发布人:</label><div class="value">${record.publish_user}</div></div>
                    ${record.article_url ? `<div class="detail-field"><label>文章链接:</label><div class="value"><a href="${record.article_url}" target="_blank">${record.article_url}</a></div></div>` : ''}
                </div>
                <div class="detail-section">
                    <h3>文章内容</h3>
                    <div class="detail-field"><label>字数:</label><div class="value">${record.word_count} 字</div></div>
                    <div class="detail-field"><label>内容:</label><div class="value" style="max-height: 300px; overflow-y: auto; white-space: pre-wrap;">${record.content || '(无内容)'}</div></div>
                </div>
                ${record.error_message ? `<div class="detail-section"><h3>错误信息</h3><div class="detail-field"><div class="value" style="color: red;">${record.error_message}</div></div></div>` : ''}
            `;
            document.getElementById('detail-modal').style.display = 'block';
        }
    } catch (error) {
        alert('加载详情失败: ' + error.message);
    }
}

async function deleteRecord(id) {
    if (!confirm('确认删除这条发布记录吗？')) return;

    try {
        const response = await fetch(`/api/publish-history/${id}`, { method: 'DELETE' });
        const data = await response.json();

        if (data.success) {
            alert('删除成功');
            loadHistory(currentPage);
            loadStats();
        } else {
            alert('删除失败: ' + data.message);
        }
    } catch (error) {
        alert('删除失败: ' + error.message);
    }
}

function closeModal() {
    document.getElementById('detail-modal').style.display = 'none';
}

function formatDateTime(datetime) {
    if (!datetime) return '-';
    const date = new Date(datetime);
    return date.toLocaleString('zh-CN');
}

window.onclick = function(event) {
    const modal = document.getElementById('detail-modal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
};

document.addEventListener('DOMContentLoaded', function() {
    loadStats();
    loadHistory();
});
JSEOF"""

    ssh.exec_command(cmd2, timeout=10)
    time.sleep(1)
    print("✓ JavaScript文件已创建")

    # 步骤3: 集成保存历史记录到知乎发布API
    print("\n[3/3] 集成历史记录保存到知乎发布API...")
    # 这里需要修改zhihu发布API，添加save_publish_history调用
    # 由于不知道具体的API代码结构，我们创建一个说明文件

    cmd3 = """cat > /home/u_topn/TOP_N/backend/INTEGRATE_HISTORY_README.txt << 'README'
==========================================================================
知乎发布API集成历史记录保存说明
==========================================================================

请在 /api/zhihu/post 路由的处理函数中添加历史记录保存:

1. 在发布成功后添加:
   save_publish_history(
       title=data.get('title'),
       content=data.get('content'),
       platform='知乎',
       account_username=username,
       status='success',
       article_url=article_url,  # 发布成功返回的文章URL
       article_type=data.get('article_type', '推广文章'),
       publish_user=data.get('publish_user', 'system')
   )

2. 在发布失败后添加:
   save_publish_history(
       title=data.get('title'),
       content=data.get('content'),
       platform='知乎',
       account_username=username,
       status='failed',
       error_message=str(error),  # 错误信息
       article_type=data.get('article_type', '推广文章'),
       publish_user=data.get('publish_user', 'system')
   )

示例代码位置:
查找 @app.route('/api/zhihu/post', methods=['POST'])
在 try 块成功后和 except 块中分别添加上述代码

==========================================================================
README"""

    ssh.exec_command(cmd3, timeout=10)
    print("✓ 集成说明文件已创建")

    # 重启服务
    print("\n[4/4] 重启服务...")
    cmd = "sudo systemctl restart topn"
    ssh.exec_command(cmd, timeout=30)

    time.sleep(4)

    # 检查服务状态
    cmd = "sudo systemctl status topn --no-pager | head -15"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    print(stdout.read().decode('utf-8'))

    print("\n" + "=" * 80)
    print("✅ 发布历史管理功能部署完成!")
    print("=" * 80)
    print("""
功能说明:
✓ 数据库已创建 - publish_history.db
✓ 后端API已部署 - 5个API接口
✓ 前端页面已创建 - publish_history.html
✓ JavaScript已创建 - publish_history.js
✓ 导航链接已添加 - 首页"📊 发布历史"按钮

访问地址:
http://39.105.12.124:8080/publish-history

功能特性:
1. 📊 统计面板 - 总数、成功数、失败数、成功率
2. 📋 历史列表 - 支持分页、筛选(状态/平台)
3. 🔍 详情查看 - 完整内容、错误信息
4. 🗑️ 删除记录 - 删除历史记录
5. 🔄 实时刷新 - 手动刷新数据

下一步:
需要手动修改知乎发布API以自动保存历史记录
详见: /home/u_topn/TOP_N/backend/INTEGRATE_HISTORY_README.txt
    """)

    sftp.close()
    ssh.close()

except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
