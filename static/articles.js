// 文章页面逻辑 - 支持富文本编辑

// 存储所有 Quill 编辑器实例
const editors = {};

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

// 显示文章（带编辑功能）
function displayArticles(articles) {
    const container = document.getElementById('articles-container');
    container.innerHTML = '';

    articles.forEach((article, index) => {
        const card = document.createElement('div');
        card.className = 'article-card';
        card.id = `article-card-${index}`;

        // 将换行符转换为HTML格式
        const formattedContent = article.content.replace(/\n/g, '<br>');

        card.innerHTML = `
            <div class="article-header">
                <span class="article-type">${article.type}</span>
                <div class="article-actions">
                    <button class="btn-icon btn-edit" onclick="toggleEdit(${index})" title="编辑文章">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                        </svg>
                    </button>
                </div>
            </div>

            <!-- 标题编辑区域 -->
            <div class="title-container">
                <h3 class="article-title" id="title-display-${index}">${article.title}</h3>
                <div class="title-edit-container" id="title-edit-${index}" style="display: none;">
                    <input type="text" class="title-input" id="title-input-${index}" value="${article.title}">
                </div>
            </div>

            <!-- 内容显示区域 -->
            <div class="article-content" id="content-display-${index}">${formattedContent}</div>

            <!-- 富文本编辑区域 -->
            <div class="editor-container" id="editor-container-${index}" style="display: none;">
                <div class="editor-toolbar" id="toolbar-${index}">
                    <span class="ql-formats">
                        <select class="ql-header">
                            <option value="1">标题1</option>
                            <option value="2">标题2</option>
                            <option value="3">标题3</option>
                            <option selected>正文</option>
                        </select>
                    </span>
                    <span class="ql-formats">
                        <button class="ql-bold"></button>
                        <button class="ql-italic"></button>
                        <button class="ql-underline"></button>
                        <button class="ql-strike"></button>
                    </span>
                    <span class="ql-formats">
                        <select class="ql-color"></select>
                        <select class="ql-background"></select>
                    </span>
                    <span class="ql-formats">
                        <button class="ql-list" value="ordered"></button>
                        <button class="ql-list" value="bullet"></button>
                    </span>
                    <span class="ql-formats">
                        <button class="ql-blockquote"></button>
                        <button class="ql-code-block"></button>
                    </span>
                    <span class="ql-formats">
                        <button class="ql-link"></button>
                    </span>
                    <span class="ql-formats">
                        <button class="ql-clean"></button>
                    </span>
                </div>
                <div class="editor-content" id="editor-${index}"></div>
            </div>

            <!-- 编辑操作按钮 -->
            <div class="edit-actions" id="edit-actions-${index}" style="display: none;">
                <button class="btn btn-secondary btn-sm" onclick="cancelEdit(${index})">取消</button>
                <button class="btn btn-primary btn-sm" onclick="saveEdit(${index})">保存修改</button>
            </div>
        `;
        container.appendChild(card);
    });
}

// 切换编辑模式
function toggleEdit(index) {
    const card = document.getElementById(`article-card-${index}`);
    const isEditing = card.classList.contains('editing');

    if (isEditing) {
        cancelEdit(index);
    } else {
        enterEditMode(index);
    }
}

// 进入编辑模式
function enterEditMode(index) {
    const card = document.getElementById(`article-card-${index}`);
    const titleDisplay = document.getElementById(`title-display-${index}`);
    const titleEdit = document.getElementById(`title-edit-${index}`);
    const contentDisplay = document.getElementById(`content-display-${index}`);
    const editorContainer = document.getElementById(`editor-container-${index}`);
    const editActions = document.getElementById(`edit-actions-${index}`);

    // 添加编辑状态
    card.classList.add('editing');

    // 切换显示
    titleDisplay.style.display = 'none';
    titleEdit.style.display = 'block';
    contentDisplay.style.display = 'none';
    editorContainer.style.display = 'block';
    editActions.style.display = 'flex';

    // 初始化编辑器（如果还没有）
    if (!editors[index]) {
        editors[index] = new Quill(`#editor-${index}`, {
            theme: 'snow',
            modules: {
                toolbar: `#toolbar-${index}`
            },
            placeholder: '编辑文章内容...'
        });

        // 设置初始内容
        const state = WorkflowState.get();
        const content = state.articles[index].content;
        // 将纯文本转换为带换行的HTML
        const htmlContent = content.replace(/\n/g, '<br>');
        editors[index].clipboard.dangerouslyPasteHTML(htmlContent);
    }

    // 更新编辑按钮样式
    const editBtn = card.querySelector('.btn-edit');
    editBtn.classList.add('active');
}

// 取消编辑
function cancelEdit(index) {
    const card = document.getElementById(`article-card-${index}`);
    const titleDisplay = document.getElementById(`title-display-${index}`);
    const titleEdit = document.getElementById(`title-edit-${index}`);
    const titleInput = document.getElementById(`title-input-${index}`);
    const contentDisplay = document.getElementById(`content-display-${index}`);
    const editorContainer = document.getElementById(`editor-container-${index}`);
    const editActions = document.getElementById(`edit-actions-${index}`);

    // 恢复原始内容
    const state = WorkflowState.get();
    titleInput.value = state.articles[index].title;
    if (editors[index]) {
        const htmlContent = state.articles[index].content.replace(/\n/g, '<br>');
        editors[index].clipboard.dangerouslyPasteHTML(htmlContent);
    }

    // 移除编辑状态
    card.classList.remove('editing');

    // 切换显示
    titleDisplay.style.display = 'block';
    titleEdit.style.display = 'none';
    contentDisplay.style.display = 'block';
    editorContainer.style.display = 'none';
    editActions.style.display = 'none';

    // 更新编辑按钮样式
    const editBtn = card.querySelector('.btn-edit');
    editBtn.classList.remove('active');
}

// 保存编辑
function saveEdit(index) {
    const titleInput = document.getElementById(`title-input-${index}`);
    const titleDisplay = document.getElementById(`title-display-${index}`);
    const contentDisplay = document.getElementById(`content-display-${index}`);

    // 获取新内容
    const newTitle = titleInput.value.trim();
    const newContent = editors[index].root.innerHTML;

    // 验证
    if (!newTitle) {
        alert('标题不能为空');
        return;
    }

    // 更新显示
    titleDisplay.textContent = newTitle;
    contentDisplay.innerHTML = newContent;

    // 更新状态
    const state = WorkflowState.get();
    state.articles[index].title = newTitle;
    // 保存HTML内容，同时保留纯文本版本用于发布
    state.articles[index].content = editors[index].getText().trim();
    state.articles[index].htmlContent = newContent;
    WorkflowState.save(state);

    // 退出编辑模式
    const card = document.getElementById(`article-card-${index}`);
    const titleEdit = document.getElementById(`title-edit-${index}`);
    const editorContainer = document.getElementById(`editor-container-${index}`);
    const editActions = document.getElementById(`edit-actions-${index}`);

    card.classList.remove('editing');
    titleDisplay.style.display = 'block';
    titleEdit.style.display = 'none';
    contentDisplay.style.display = 'block';
    editorContainer.style.display = 'none';
    editActions.style.display = 'none';

    // 更新编辑按钮样式
    const editBtn = card.querySelector('.btn-edit');
    editBtn.classList.remove('active');

    // 显示保存成功提示
    showSaveSuccess(card);
}

// 显示保存成功提示
function showSaveSuccess(card) {
    const toast = document.createElement('div');
    toast.className = 'save-toast';
    toast.textContent = '保存成功';
    card.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('show');
    }, 10);

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 2000);
}
