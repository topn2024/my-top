// 输入页面逻辑
let uploadedText = '';

// 文件上传相关
const uploadArea = document.getElementById('upload-area');
const fileInput = document.getElementById('file-upload');
const uploadPlaceholder = uploadArea.querySelector('.upload-placeholder');
const uploadResult = document.getElementById('upload-result');
const uploadedFilename = document.getElementById('uploaded-filename');

// 页面加载时恢复之前的输入
window.addEventListener('load', () => {
    const state = WorkflowState.get();

    // 恢复表单数据
    if (state.companyName) {
        document.getElementById('company-name').value = state.companyName;
    }
    if (state.companyDesc) {
        document.getElementById('company-desc').value = state.companyDesc;
    }
    if (state.articleCount) {
        document.getElementById('article-count').value = state.articleCount;
    }
    if (state.uploadedFilename) {
        uploadedText = state.uploadedText;
        uploadedFilename.textContent = state.uploadedFilename;
        uploadPlaceholder.style.display = 'none';
        uploadResult.style.display = 'block';
    }
});

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

            // 保存到状态
            WorkflowState.update({
                uploadedText: data.text,
                uploadedFilename: data.filename
            });

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

    // 更新状态
    WorkflowState.update({
        uploadedText: '',
        uploadedFilename: ''
    });

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

    const articleCount = parseInt(document.getElementById('article-count').value);

    // 保存到状态
    WorkflowState.update({
        companyName: formData.company_name,
        companyDesc: formData.company_desc,
        articleCount: articleCount,
        currentStep: 1
    });

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
            // 保存分析结果到状态
            WorkflowState.update({
                analysis: data.analysis,
                currentStep: 2
            });

            // 跳转到分析页面
            WorkflowNav.goToAnalysis();
        } else {
            alert('分析失败: ' + data.error);
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
