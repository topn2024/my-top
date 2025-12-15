/**
 * 发布历史模块
 * 负责发布历史的加载、显示和分页
 */

class PublishHistoryManager {
    constructor() {
        this.currentPage = 1;
        this.pageSize = 10;
        this.totalCount = 0;
        this.allHistory = [];
    }

    /**
     * 初始化发布历史
     */
    async init() {
        await this.loadHistory();
    }

    /**
     * 加载发布历史
     */
    async loadHistory() {
        try {
            const response = await fetch('/api/publish_history');
            const data = await response.json();

            if (data.success && data.history) {
                this.allHistory = data.history;
                this.totalCount = data.count || data.history.length;
                this.currentPage = 1;
                this.renderHistory();
                this.renderPagination();
            } else {
                this.showNoHistory();
            }
        } catch (error) {
            console.error('加载发布历史失败:', error);
            this.showError('加载发布历史失败，请刷新页面重试');
        }
    }

    /**
     * 显示发布历史
     */
    renderHistory() {
        const container = document.getElementById('history-container');
        if (!container) return;

        // 清空容器
        container.innerHTML = '';

        if (this.allHistory.length === 0) {
            this.showNoHistory();
            return;
        }

        // 计算当前页的数据
        const startIndex = (this.currentPage - 1) * this.pageSize;
        const endIndex = startIndex + this.pageSize;
        const pageData = this.allHistory.slice(startIndex, endIndex);

        // 创建表格
        const table = document.createElement('table');
        table.className = 'history-table';

        // 表头
        table.innerHTML = `
            <thead>
                <tr>
                    <th style="width: 35%;">文章标题</th>
                    <th style="width: 10%;">平台</th>
                    <th style="width: 10%;">状态</th>
                    <th style="width: 20%;">发布时间</th>
                    <th style="width: 25%;">操作</th>
                </tr>
            </thead>
            <tbody id="history-tbody"></tbody>
        `;

        container.appendChild(table);
        const tbody = document.getElementById('history-tbody');

        // 填充数据
        pageData.forEach(item => {
            this.renderHistoryRow(tbody, item);
        });

        // 显示统计信息
        this.renderStats();
    }

    /**
     * 渲染单条历史记录
     */
    renderHistoryRow(tbody, item) {
        const row = document.createElement('tr');
        row.setAttribute('data-id', item.id);

        const statusClass = item.status === 'success' ? 'status-success' : 'status-failed';
        const statusText = item.status === 'success' ? '✓ 成功' : '✗ 失败';

        // 格式化时间
        const publishTime = item.published_at ? new Date(item.published_at).toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        }) : 'N/A';

        // 文章标题（处理长标题）
        const title = item.article_title || '未知';
        const displayTitle = title.length > 40 ? title.substring(0, 40) + '...' : title;

        row.innerHTML = `
            <td class="article-title" title="${this.escapeHtml(title)}">${this.escapeHtml(displayTitle)}</td>
            <td>${this.escapeHtml(item.platform || 'N/A')}</td>
            <td><span class="status-badge ${statusClass}">${statusText}</span></td>
            <td>${publishTime}</td>
            <td class="action-cell">
                ${item.article_content ? `<button onclick="publishHistoryManager.viewContent(${item.id})" class="view-content-btn">📄 查看内容</button>` : '<span style="color: #999;">无内容</span>'}
                ${item.url ? `<a href="${this.escapeHtml(item.url)}" target="_blank" class="view-link">🔗 查看链接</a>` : ''}
                ${item.status === 'failed' ? `
                    <button onclick="publishHistoryManager.retryPublish(${item.id}, '${this.escapeHtml(item.article_title || '').replace(/'/g, "\\'")}', this)" class="retry-btn">
                        🔄 重试
                    </button>
                ` : ''}
            </td>
        `;

        tbody.appendChild(row);

        // 如果有消息，添加消息行
        if (item.message) {
            const msgRow = document.createElement('tr');
            msgRow.className = 'message-row';
            msgRow.innerHTML = `
                <td colspan="5" class="message-cell">
                    <small>${this.escapeHtml(item.message)}</small>
                </td>
            `;
            tbody.appendChild(msgRow);
        }
    }

    /**
     * 查看文章内容
     */
    viewContent(id) {
        const item = this.allHistory.find(h => h.id === id);
        if (!item || !item.article_content) {
            alert('没有文章内容');
            return;
        }

        // 创建模态框显示内容
        const modal = document.createElement('div');
        modal.className = 'content-modal';
        modal.innerHTML = `
            <div class="modal-overlay" onclick="this.parentElement.remove()"></div>
            <div class="modal-content">
                <div class="modal-header">
                    <h3>${this.escapeHtml(item.article_title || '文章内容')}</h3>
                    <button class="modal-close" onclick="this.closest('.content-modal').remove()">×</button>
                </div>
                <div class="modal-body">
                    <div class="content-preview">${this.escapeHtml(item.article_content).replace(/\n/g, '<br>')}</div>
                </div>
                <div class="modal-footer">
                    <button onclick="publishHistoryManager.copyContent(${id})" class="copy-btn">📋 复制内容</button>
                    <button onclick="this.closest('.content-modal').remove()" class="close-btn">关闭</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
    }

    /**
     * 复制文章内容
     */
    copyContent(id) {
        const item = this.allHistory.find(h => h.id === id);
        if (!item || !item.article_content) {
            alert('没有文章内容');
            return;
        }

        navigator.clipboard.writeText(item.article_content).then(() => {
            alert('内容已复制到剪贴板');
        }).catch(err => {
            console.error('复制失败:', err);
            alert('复制失败，请手动复制');
        });
    }

    /**
     * 渲染分页控件
     */
    renderPagination() {
        const container = document.getElementById('pagination-container');
        if (!container) return;

        container.innerHTML = '';

        if (this.allHistory.length === 0) return;

        const totalPages = Math.ceil(this.totalCount / this.pageSize);

        if (totalPages <= 1) return;

        const paginationDiv = document.createElement('div');
        paginationDiv.className = 'pagination';

        // 上一页按钮
        const prevBtn = document.createElement('button');
        prevBtn.className = 'page-btn';
        prevBtn.textContent = '‹ 上一页';
        prevBtn.disabled = this.currentPage === 1;
        prevBtn.onclick = () => this.goToPage(this.currentPage - 1);
        paginationDiv.appendChild(prevBtn);

        // 页码信息
        const pageInfo = document.createElement('span');
        pageInfo.className = 'page-info';
        pageInfo.textContent = `第 ${this.currentPage} / ${totalPages} 页`;
        paginationDiv.appendChild(pageInfo);

        // 下一页按钮
        const nextBtn = document.createElement('button');
        nextBtn.className = 'page-btn';
        nextBtn.textContent = '下一页 ›';
        nextBtn.disabled = this.currentPage === totalPages;
        nextBtn.onclick = () => this.goToPage(this.currentPage + 1);
        paginationDiv.appendChild(nextBtn);

        container.appendChild(paginationDiv);
    }

    /**
     * 渲染统计信息
     */
    renderStats() {
        const container = document.getElementById('history-stats');
        if (!container) return;

        const successCount = this.allHistory.filter(h => h.status === 'success').length;
        const failedCount = this.allHistory.filter(h => h.status === 'failed').length;

        container.innerHTML = `
            <div class="history-stats">
                <span>共 ${this.totalCount} 条记录</span>
                <span class="stat-success">成功 ${successCount}</span>
                <span class="stat-failed">失败 ${failedCount}</span>
            </div>
        `;
    }

    /**
     * 跳转到指定页
     */
    goToPage(page) {
        const totalPages = Math.ceil(this.totalCount / this.pageSize);

        if (page < 1 || page > totalPages) return;

        this.currentPage = page;
        this.renderHistory();
        this.renderPagination();

        // 滚动到表格顶部
        const container = document.getElementById('history-container');
        if (container) {
            container.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    /**
     * 显示无历史记录
     */
    showNoHistory() {
        const container = document.getElementById('history-container');
        if (container) {
            container.innerHTML = '<p class="no-history">暂无发布历史</p>';
        }

        const statsContainer = document.getElementById('history-stats');
        if (statsContainer) {
            statsContainer.innerHTML = '';
        }

        const paginationContainer = document.getElementById('pagination-container');
        if (paginationContainer) {
            paginationContainer.innerHTML = '';
        }
    }

    /**
     * 显示错误信息
     */
    showError(message) {
        const container = document.getElementById('history-container');
        if (container) {
            container.innerHTML = `<p class="error-message">${this.escapeHtml(message)}</p>`;
        }
    }

    /**
     * 重试发布
     */
    async retryPublish(historyId, articleTitle, button) {
        if (!confirm(`确定要重新发布《${articleTitle}》吗？`)) {
            return;
        }

        // 禁用按钮
        button.disabled = true;
        const originalHTML = button.innerHTML;
        button.innerHTML = '<span>⏳</span> 重试中...';
        button.style.opacity = '0.6';

        try {
            const response = await fetch(`/api/retry_publish/${historyId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (data.success) {
                alert(`重新发布成功！\n${data.message || ''}`);
                // 重新加载发布历史
                await this.loadHistory();
            } else {
                alert(`重新发布失败：${data.error || data.message || '未知错误'}`);
                // 恢复按钮
                button.disabled = false;
                button.innerHTML = originalHTML;
                button.style.opacity = '1';
            }
        } catch (error) {
            alert('重新发布失败: ' + error.message);
            // 恢复按钮
            button.disabled = false;
            button.innerHTML = originalHTML;
            button.style.opacity = '1';
        }
    }

    /**
     * HTML转义，防止XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 刷新历史记录
     */
    async refresh() {
        await this.loadHistory();
    }

    /**
     * 更新临时发布文章的标题
     */
    async updateTempTitles() {
        if (!confirm('确定要从知乎获取并更新临时发布文章的标题吗？\n这可能需要几分钟时间。')) {
            return;
        }

        try {
            // 显示加载状态
            const statsContainer = document.getElementById('history-stats');
            const originalHTML = statsContainer.innerHTML;
            statsContainer.innerHTML = '<div style="color: #3b82f6;">⏳ 正在更新标题，请稍候...</div>';

            const response = await fetch('/api/update_temp_titles', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            // 恢复原始内容
            statsContainer.innerHTML = originalHTML;

            if (data.success) {
                let message = `标题更新完成！\n\n`;
                message += `总记录数: ${data.total}\n`;
                message += `已更新: ${data.updated}\n`;
                message += `已跳过: ${data.skipped}\n`;
                message += `失败: ${data.failed}\n`;

                if (data.edit_urls && data.edit_urls.length > 0) {
                    message += `\n注意: 有 ${data.edit_urls.length} 个URL处于编辑状态`;
                }

                alert(message);

                // 重新加载历史记录
                await this.refresh();
            } else {
                alert(`标题更新失败：${data.error || '未知错误'}`);
            }
        } catch (error) {
            console.error('更新标题失败:', error);
            alert('更新标题失败: ' + error.message);
        }
    }

    /**
     * 批量清理任务
     * @param {string[]} statusFilter - 状态过滤器，如 ['success', 'failed', 'cancelled']
     */
    async clearTasksByStatus(statusFilter) {
        const statusNames = {
            'success': '成功',
            'failed': '失败',
            'cancelled': '已取消'
        };

        const statusText = statusFilter.map(s => statusNames[s] || s).join('、');

        if (!confirm(`确定要清理所有【${statusText}】的任务吗？\n此操作不可撤销！`)) {
            return;
        }

        try {
            // 显示加载状态
            const statsContainer = document.getElementById('history-stats');
            const originalHTML = statsContainer.innerHTML;
            statsContainer.innerHTML = '<div style="color: #f59e0b;">⏳ 正在清理任务，请稍候...</div>';

            const response = await fetch('/task/clear', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    status_filter: statusFilter
                })
            });

            const data = await response.json();

            // 恢复原始内容
            statsContainer.innerHTML = originalHTML;

            if (data.success) {
                let message = `清理完成！\n\n`;
                message += `已删除: ${data.deleted_count} 个任务\n`;
                if (data.failed_count > 0) {
                    message += `失败: ${data.failed_count} 个任务\n`;
                    if (data.errors && data.errors.length > 0) {
                        message += `\n错误信息:\n${data.errors.slice(0, 3).join('\n')}`;
                        if (data.errors.length > 3) {
                            message += `\n... 还有 ${data.errors.length - 3} 个错误`;
                        }
                    }
                }
                alert(message);

                // 重新加载历史记录
                await this.refresh();
            } else {
                alert(`清理任务失败：${data.error || data.message || '未知错误'}`);
            }
        } catch (error) {
            console.error('清理任务失败:', error);
            alert('清理任务失败: ' + error.message);
        }
    }

    /**
     * 清理所有成功的任务
     */
    async clearSuccessTasks() {
        await this.clearTasksByStatus(['success']);
    }

    /**
     * 清理所有失败的任务
     */
    async clearFailedTasks() {
        await this.clearTasksByStatus(['failed']);
    }

    /**
     * 清理所有已完成的任务（成功、失败、已取消）
     */
    async clearCompletedTasks() {
        await this.clearTasksByStatus(['success', 'failed', 'cancelled']);
    }
}

// 创建全局实例
const publishHistoryManager = new PublishHistoryManager();
