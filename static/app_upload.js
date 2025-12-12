let currentAnalysis = null;
let currentCompanyName = '';
let uploadedText = '';

// 文件上传相关
const uploadArea = document.getElementById('upload-area');
const fileInput = document.getElementById('file-upload');
const uploadPlaceholder = uploadArea.querySelector('.upload-placeholder');
const uploadResult = document.getElementById('upload-result');
const uploadedFilename = document.getElementById('uploaded-filename');

// 点击上传区域触发文件选择
uploadArea.addEventListener('click', () => {
    fileInput.click();
});

// 拖拽上传
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.style.borderColor = '#667eea';
    uploadArea.style.background = '#f8f9ff';
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.style.borderColor = '#e0e0e0';
    uploadArea.style.background = 'white';
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.style.borderColor = '#e0e0e0';
    uploadArea.style.background = 'white';

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileUpload(files[0]);
    }
});

// 文件选择change事件
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileUpload(e.target.files[0]);
    }
});

// 处理文件上传
async function handleFileUpload(file) {
    const allowedTypes = ['text/plain', 'application/pdf', 'application/msword',
                          'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                          'text/markdown'];
    const allowedExtensions = ['.txt', '.pdf', '.doc', '.docx', '.md'];

    const fileName = file.name.toLowerCase();
    const hasValidExtension = allowedExtensions.some(ext => fileName.endsWith(ext));

    if (!hasValidExtension) {
        alert('不支持的文件格式！仅支持 TXT, PDF, DOC, DOCX, MD 格式');
        return;
    }

    if (file.size > 10 * 1024 * 1024) {
        alert('文件太大！最大支持 10MB');
        return;
    }

    showLoading('正在读取文件...');

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            uploadedText = data.text;
            uploadedFilename.textContent = data.filename;
            uploadPlaceholder.style.display = 'none';
            uploadResult.style.display = 'block';

            // 将提取的文本添加到描述框
            const descTextarea = document.getElementById('company-desc');
            if (descTextarea.value) {
                descTextarea.value += '\n\n--- 文件内容 ---\n' + data.text;
            } else {
                descTextarea.value = data.text;
            }

            alert('文件上传成功！内容已自动填充到描述框中');
        } else {
            alert('文件上传失败: ' + data.error);
        }
    } catch (error) {
        alert('文件上传失败: ' + error.message);
    } finally {
        hideLoading();
    }
}

// 清除上传的文件
function clearUpload() {
    uploadedText = '';
    fileInput.value = '';
    uploadPlaceholder.style.display = 'block';
    uploadResult.style.display = 'none';

    // 从描述框中移除文件内容
    const descTextarea = document.getElementById('company-desc');
    if (descTextarea.value.includes('--- 文件内容 ---')) {
        const parts = descTextarea.value.split('--- 文件内容 ---');
        descTextarea.value = parts[0].trim();
    }
}

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
    clearUpload();
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
