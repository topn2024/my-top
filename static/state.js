// 状态管理 - 使用 localStorage 实现持久化
const WorkflowState = {
    // 获取完整状态
    get() {
        const stateStr = localStorage.getItem('topn_workflow_state');
        return stateStr ? JSON.parse(stateStr) : this.getDefault();
    },

    // 获取默认状态
    getDefault() {
        return {
            companyName: '',
            companyDesc: '',
            uploadedText: '',
            uploadedFilename: '',
            analysis: null,
            articles: [],
            articleCount: 3,
            platforms: [],
            currentStep: 1,
            timestamp: new Date().toISOString()
        };
    },

    // 保存完整状态
    save(state) {
        state.timestamp = new Date().toISOString();
        localStorage.setItem('topn_workflow_state', JSON.stringify(state));
    },

    // 更新部分状态
    update(partialState) {
        const currentState = this.get();
        const newState = { ...currentState, ...partialState };
        this.save(newState);
        return newState;
    },

    // 清空状态
    clear() {
        localStorage.removeItem('topn_workflow_state');
    },

    // 获取特定字段
    getField(field) {
        const state = this.get();
        return state[field];
    },

    // 设置特定字段
    setField(field, value) {
        this.update({ [field]: value });
    }
};

// 导航功能
const WorkflowNav = {
    goToInput() {
        window.location.href = '/platform';
    },

    goToAnalysis() {
        const state = WorkflowState.get();
        if (!state.companyName) {
            alert('请先输入公司信息');
            this.goToInput();
            return;
        }
        window.location.href = '/analysis';
    },

    goToArticles() {
        const state = WorkflowState.get();
        if (!state.analysis) {
            alert('请先完成分析');
            this.goToAnalysis();
            return;
        }
        window.location.href = '/articles';
    },

    goToPublish() {
        const state = WorkflowState.get();
        if (state.articles.length === 0) {
            alert('请先生成文章');
            this.goToArticles();
            return;
        }
        window.location.href = '/publish';
    },

    startOver() {
        if (confirm('确定要清空当前数据并重新开始吗？')) {
            WorkflowState.clear();
            this.goToInput();
        }
    }
};

// 检查状态是否已过期（24小时）
function isStateExpired() {
    const state = WorkflowState.get();
    if (!state.timestamp) return false;

    const timestamp = new Date(state.timestamp);
    const now = new Date();
    const hoursDiff = (now - timestamp) / (1000 * 60 * 60);

    return hoursDiff > 24;
}

// 页面加载时检查过期状态
window.addEventListener('load', () => {
    if (isStateExpired()) {
        if (confirm('检测到超过24小时的旧数据，是否清空重新开始？')) {
            WorkflowState.clear();
            WorkflowNav.goToInput();
        }
    }
});
