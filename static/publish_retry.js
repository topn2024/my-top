// 重试发布失败的文章
async function retryPublish(historyId, articleTitle, button) {
    if (!confirm(`确定要重新发布《${articleTitle}》吗？`)) {
        return;
    }

    // 禁用按钮
    button.disabled = true;
    const originalHTML = button.innerHTML;
    button.innerHTML = '<span>⏳</span>重试中...';
    button.style.background = 'linear-gradient(135deg, #ccc 0%, #999 100%)';
    button.style.cursor = 'not-allowed';

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
            // 刷新发布历史
            loadPublishHistory();
        } else {
            alert(`重新发布失败：${data.error || data.message || '未知错误'}`);
            // 恢复按钮
            button.disabled = false;
            button.innerHTML = originalHTML;
            button.style.background = 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)';
            button.style.cursor = 'pointer';
        }
    } catch (error) {
        alert('重新发布失败: ' + error.message);
        // 恢复按钮
        button.disabled = false;
        button.innerHTML = originalHTML;
        button.style.background = 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)';
        button.style.cursor = 'pointer';
    }
}
