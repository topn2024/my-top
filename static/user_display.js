/**
 * 用户信息显示模块
 * 在页面右上角显示当前用户信息，未登录显示"游客"
 */

class UserDisplay {
    constructor() {
        this.currentUser = null;
        this.initialized = false;
    }

    /**
     * 初始化用户显示
     * 在页面加载时调用
     */
    async init() {
        if (this.initialized) return;

        try {
            // 获取当前用户信息
            await this.fetchCurrentUser();

            // 更新显示
            this.updateDisplay();

            this.initialized = true;
        } catch (error) {
            console.error('初始化用户显示失败:', error);
            // 出错时显示游客
            this.updateDisplay();
        }
    }

    /**
     * 从后端获取当前用户信息
     */
    async fetchCurrentUser() {
        try {
            const response = await fetch('/api/auth/me', {
                method: 'GET',
                credentials: 'same-origin'
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success && data.user) {
                    this.currentUser = data.user;
                } else {
                    this.currentUser = null;
                }
            } else {
                // 401或其他错误表示未登录
                this.currentUser = null;
            }
        } catch (error) {
            console.log('获取用户信息失败，可能未登录:', error);
            this.currentUser = null;
        }
    }

    /**
     * 更新页面上的用户显示
     */
    updateDisplay() {
        const userInfoElement = document.getElementById('user-info-display');
        if (!userInfoElement) {
            console.warn('未找到用户信息显示元素 #user-info-display');
            return;
        }

        if (this.currentUser) {
            // 已登录：显示用户名和下拉菜单
            const displayName = this.currentUser.full_name || this.currentUser.username || '用户';

            userInfoElement.innerHTML = `
                <div class="user-info-container">
                    <button class="user-info-btn" onclick="userDisplay.toggleMenu()">
                        <span class="user-icon">👤</span>
                        <span class="user-name">${displayName}</span>
                        <span class="dropdown-arrow">▼</span>
                    </button>
                    <div class="user-menu" id="user-menu" style="display: none;">
                        <div class="user-menu-item user-menu-header">
                            <strong>${displayName}</strong>
                            ${this.currentUser.email ? `<small>${this.currentUser.email}</small>` : ''}
                        </div>
                        <div class="user-menu-divider"></div>
                        <a href="/" class="user-menu-item">
                            <span>🏠</span> 月栖首页
                        </a>
                        <a href="/platform" class="user-menu-item">
                            <span>🚀</span> 推广平台
                        </a>
                        <div class="user-menu-divider"></div>
                        <button class="user-menu-item" onclick="userDisplay.logout()">
                            <span>🚪</span> 退出登录
                        </button>
                    </div>
                </div>
            `;
        } else {
            // 未登录：显示"游客"和登录按钮
            userInfoElement.innerHTML = `
                <div class="user-info-container">
                    <button class="user-info-btn guest" onclick="handleLoginClick()">
                        <span class="user-icon">👤</span>
                        <span class="user-name">游客</span>
                    </button>
                </div>
            `;
        }
    }

    /**
     * 切换用户菜单显示/隐藏
     */
    toggleMenu() {
        const menu = document.getElementById('user-menu');
        if (menu) {
            const isVisible = menu.style.display !== 'none';
            menu.style.display = isVisible ? 'none' : 'block';
        }
    }

    /**
     * 退出登录
     */
    async logout() {
        try {
            const response = await fetch('/api/auth/logout', {
                method: 'POST',
                credentials: 'same-origin'
            });

            if (response.ok) {
                // 清除用户信息
                this.currentUser = null;

                // 更新显示
                this.updateDisplay();

                // 跳转到月栖公司首页
                window.location.href = '/';
            } else {
                alert('退出登录失败，请重试');
            }
        } catch (error) {
            console.error('退出登录出错:', error);
            alert('退出登录失败，请重试');
        }
    }

    /**
     * 获取当前用户对象
     */
    getCurrentUser() {
        return this.currentUser;
    }

    /**
     * 检查是否已登录
     */
    isLoggedIn() {
        return this.currentUser !== null;
    }

    /**
     * 刷新用户信息
     */
    async refresh() {
        await this.fetchCurrentUser();
        this.updateDisplay();
    }
}

// 创建全局实例
const userDisplay = new UserDisplay();

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', () => {
    userDisplay.init();
});

// 点击页面其他地方时关闭菜单
document.addEventListener('click', (event) => {
    const userMenu = document.getElementById('user-menu');
    const userInfoContainer = event.target.closest('.user-info-container');

    if (userMenu && !userInfoContainer && userMenu.style.display === 'block') {
        userMenu.style.display = 'none';
    }
});
