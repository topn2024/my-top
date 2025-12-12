// 文章页面逻辑

// 页面加载时显示文章
window.addEventListener('load', () => {
    const state = WorkflowState.get();

    // 检查是否有文章
    if (!state.articles || state.articles.length === 0) {
        alert('未找到生成的文章，请先完成分析和生成');
        WorkflowNav.goToAnalysis();
        return;
    }

    // 显示文章
    displayArticles(state.articles);
});

// 显示文章
function displayArticles(articles) {
    const container = document.getElementById('articles-container');
    container.innerHTML = '';

    articles.forEach((article, index) => {
        const card = document.createElement('div');
        card.className = 'article-card';
        card.innerHTML = `
            <span class="article-type">${article.type}</span>
            <h3>${article.title}</h3>
            <div class="article-content">${article.content.replace(/\n/g, '<br>')}</div>
        `;
        container.appendChild(card);
    });
}
