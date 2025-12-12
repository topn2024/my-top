let currentAnalysis = null;
let currentCompanyName = '';

// 表单提交
document.getElementById('company-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = {
        company_name: document.getElementById('company-name').value,
        company_desc: document.getElementById('company-desc').value
    };

    currentCompanyName = formData.company_name;

    showLoading('正在分析公司信息...');

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (data.success) {
            currentAnalysis = data.analysis;
            displayAnalysis(data.analysis);
            goToStep(2);
        } else {
            alert('分析失败: ' + data.error);
        }
    } catch (error) {
        alert('请求失败: ' + error.message);
    } finally {
        hideLoading();
    }
});

// 显示分析结果
function displayAnalysis(analysis) {
    const resultBox = document.getElementById('analysis-result');
    resultBox.textContent = analysis;
}

// 生成文章
async function generateArticles() {
    const articleCount = parseInt(document.getElementById('article-count').value);

    showLoading('正在生成推广文章，请稍候...');

    try {
        const response = await fetch('/api/generate_articles', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                company_name: currentCompanyName,
                analysis: currentAnalysis,
                article_count: articleCount
            })
        });

        const data = await response.json();

        if (data.success) {
            displayArticles(data.articles);
            goToStep(3);
        } else {
            alert('生成文章失败: ' + data.error);
        }
    } catch (error) {
        alert('请求失败: ' + error.message);
    } finally {
        hideLoading();
    }
}

// 显示文章
function displayArticles(articles) {
    const container = document.getElementById('articles-container');
    container.innerHTML = '';

    articles.forEach(article => {
        const card = document.createElement('div');
        card.className = 'article-card';
        card.innerHTML = `
            <span class="article-type">${article.type}</span>
            <h3>${article.title}</h3>
            <div class="article-content">${article.content}</div>
        `;
        container.appendChild(card);
    });
}

// 显示平台
async function showPlatforms() {
    showLoading('正在加载推荐平台...');

    try {
        const response = await fetch('/api/platforms');
        const data = await response.json();

        if (data.success) {
            displayPlatforms(data.platforms);
            goToStep(4);
        } else {
            alert('获取平台失败: ' + data.error);
        }
    } catch (error) {
        alert('请求失败: ' + error.message);
    } finally {
        hideLoading();
    }
}

// 显示平台列表
function displayPlatforms(platforms) {
    const container = document.getElementById('platforms-container');
    container.innerHTML = '';

    platforms.forEach(platform => {
        const card = document.createElement('div');
        card.className = 'platform-card';
        card.innerHTML = `
            <div class="platform-info">
                <h3>${platform.name}</h3>
                <p>${platform.description}</p>
                <p style="color: #667eea; font-weight: 600;">💡 ${platform.tips}</p>
            </div>
            <a href="${platform.url}" target="_blank" class="platform-link">访问平台</a>
        `;
        container.appendChild(card);
    });
}

// 步骤切换
function goToStep(stepNumber) {
    // 更新步骤指示器
    document.querySelectorAll('.step').forEach((step, index) => {
        if (index + 1 <= stepNumber) {
            step.classList.add('active');
        } else {
            step.classList.remove('active');
        }
    });

    // 切换section
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });

    const sectionMap = {
        1: 'input-section',
        2: 'analysis-section',
        3: 'articles-section',
        4: 'platforms-section'
    };

    document.getElementById(sectionMap[stepNumber]).classList.add('active');
}

// 返回功能
function backToInput() {
    goToStep(1);
}

function backToAnalysis() {
    goToStep(2);
}

function startOver() {
    document.getElementById('company-form').reset();
    currentAnalysis = null;
    currentCompanyName = '';
    goToStep(1);
}

// 加载动画
function showLoading(text = '处理中...') {
    document.getElementById('loading-text').textContent = text;
    document.getElementById('loading').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}
