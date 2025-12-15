/**
 * 认证和权限工具
 */

// 用户角色常量
const ROLE_GUEST = 'guest';
const ROLE_USER = 'user';
const ROLE_ADMIN = 'admin';

// 当前用户信息（缓存）
let currentUserCache = null;

/**
 * 获取当前用户信息
 */
async function getCurrentUser() {
    if (currentUserCache) {
        return currentUserCache;
    }

    try {
        const response = await fetch('/api/auth/me');
        const data = await response.json();

        if (data.success && data.user) {
            currentUserCache = data.user;
            return data.user;
        }
    } catch (error) {
        console.error('Failed to get current user:', error);
    }

    return null;
}

/**
 * 获取用户角色
 */
async function getUserRole() {
    const user = await getCurrentUser();
    return user ? (user.role || ROLE_USER) : ROLE_GUEST;
}

/**
 * 检查是否已登录
 */
async function isLoggedIn() {
    const role = await getUserRole();
    return role !== ROLE_GUEST;
}

/**
 * 检查是否是管理员
 */
async function isAdmin() {
    const role = await getUserRole();
    return role === ROLE_ADMIN;
}

/**
 * 清除用户缓存（退出登录时调用）
 */
function clearUserCache() {
    currentUserCache = null;
}

/**
 * 根据用户角色显示/隐藏元素
 */
async function updateUIBasedOnRole() {
    const role = await getUserRole();
    const user = await getCurrentUser();

    console.log('=== updateUIBasedOnRole Debug ===');
    console.log('Current user:', user);
    console.log('Current user role:', role);

    // 更新所有带有data-role-required属性的元素
    const elementsWithRole = document.querySelectorAll('[data-role-required]');
    console.log('Found elements with data-role-required:', elementsWithRole.length);

    elementsWithRole.forEach(element => {
        const requiredRole = element.dataset.roleRequired;

        let shouldShow = false;

        if (requiredRole === 'guest') {
            // 公开元素，所有人可见
            shouldShow = true;
        } else if (requiredRole === 'user') {
            // 需要登录
            shouldShow = role !== ROLE_GUEST;
        } else if (requiredRole === 'admin') {
            // 仅管理员
            shouldShow = role === ROLE_ADMIN;
        }

        console.log('Element:', element.tagName, 'Required:', requiredRole, 'Should show:', shouldShow);

        if (shouldShow) {
            element.style.display = '';
            element.classList.remove('hidden');
        } else {
            element.style.display = 'none';
            element.classList.add('hidden');
        }
    });

    // 更新登录/用户信息显示
    const loginBtn = document.getElementById('login-btn');
    if (loginBtn) {
        if (user) {
            loginBtn.textContent = `👤 ${user.username}`;
            loginBtn.onclick = handleUserMenu;
        } else {
            loginBtn.textContent = '🔑 登录/注册';
            loginBtn.onclick = () => { window.location.href = '/login'; };
        }
    }

    // 更新导航链接的点击处理
    document.querySelectorAll('a[href^="/platform"], a[href^="/analysis"], a[href^="/articles"], a[href^="/publish"]').forEach(link => {
        link.addEventListener('click', async function(e) {
            if (role === ROLE_GUEST) {
                e.preventDefault();
                alert('请先登录后再使用此功能');
                window.location.href = '/login';
            }
        });
    });

    // 更新模板管理链接的点击处理
    document.querySelectorAll('a[href^="/templates"], a[href^="/template-guide"]').forEach(link => {
        // 移除旧的监听器，避免重复绑定
        const newLink = link.cloneNode(true);
        link.parentNode.replaceChild(newLink, link);

        newLink.addEventListener('click', async function(e) {
            const currentRole = await getUserRole();
            if (currentRole !== ROLE_ADMIN) {
                e.preventDefault();
                alert('此功能仅限管理员访问');
                if (currentRole === ROLE_GUEST) {
                    window.location.href = '/login';
                }
            }
        });
    });
}

/**
 * 处理用户菜单点击
 */
async function handleUserMenu() {
    const user = await getCurrentUser();
    if (!user) return;

    const role = user.role || ROLE_USER;
    let menuText = `当前用户: ${user.username}\n角色: ${role === ROLE_ADMIN ? '管理员' : '注册用户'}\n\n是否退出登录?`;

    if (confirm(menuText)) {
        await handleLogout();
    }
}

/**
 * 处理退出登录
 */
async function handleLogout() {
    try {
        const response = await fetch('/api/auth/logout', {
            method: 'POST'
        });
        const data = await response.json();

        if (data.success) {
            clearUserCache();
            alert('已成功退出登录');
            window.location.href = '/';
        } else {
            alert('退出登录失败: ' + (data.error || '未知错误'));
        }
    } catch (error) {
        console.error('Logout error:', error);
        alert('退出登录失败: ' + error.message);
    }
}

/**
 * 页面加载时初始化权限检查
 */
if (typeof window !== 'undefined') {
    window.addEventListener('DOMContentLoaded', function() {
        updateUIBasedOnRole();
    });
}
