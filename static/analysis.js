// 分析页面逻辑

// 页面加载时显示分析结果
window.addEventListener('load', () => {
    const state = WorkflowState.get();

    // 检查是否有分析结果
    if (!state.analysis) {
        alert('未找到分析结果，请先完成信息输入');
        WorkflowNav.goToInput();
        return;
    }

    // 显示分析结果
    displayAnalysis(state.analysis);
});

// 显示分析结果
function displayAnalysis(analysis) {
    const resultBox = document.getElementById('analysis-result');
    resultBox.textContent = analysis;
}

// 生成文章按钮
document.getElementById('generate-btn').addEventListener('click', async () => {
    const state = WorkflowState.get();

    showLoading('正在生成推广文章，请稍候...');

    try {
        const response = await fetch('/api/generate_articles', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                company_name: state.companyName,
                analysis: state.analysis,
                article_count: state.articleCount || 3
            })
        });

        const data = await response.json();

        if (data.success) {
            // 保存文章到状态
            WorkflowState.update({
                articles: data.articles,
                currentStep: 3
            });

            // 跳转到文章页面
            WorkflowNav.goToArticles();
        } else {
            alert('生成文章失败: ' + data.error);
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
