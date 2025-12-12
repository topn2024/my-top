#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署完整的二维码登录+自动发布流程
"""

import paramiko
import sys
import io
import time
from pathlib import Path

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

SERVER = "39.105.12.124"
USER = "u_topn"
PASSWORD = "TopN@2024"
DEPLOY_DIR = "/home/u_topn/TOP_N"

def main():
    print("部署完整的二维码登录+自动发布流程...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)

    # 1. 创建完整的二维码登录模块（使用DrissionPage获取真实二维码）
    qr_login_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知乎二维码登录模块（完整版：获取二维码 + 等待登录 + 保存Cookie）
"""
import time
import os
import base64
import logging
import json
from DrissionPage import ChromiumPage, ChromiumOptions

logger = logging.getLogger(__name__)


class ZhihuQRLogin:
    """知乎二维码登录类"""

    def __init__(self, cookies_dir=None):
        self.driver = None
        self.login_url = 'https://www.zhihu.com/signin'

        if cookies_dir is None:
            cookies_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cookies')
        self.cookies_dir = cookies_dir
        os.makedirs(self.cookies_dir, exist_ok=True)

    def init_browser(self):
        """初始化浏览器"""
        try:
            co = ChromiumOptions()
            co.auto_port(True)  # 自动分配端口

            # Headless模式
            co.headless(True)
            co.set_argument('--no-sandbox')
            co.set_argument('--disable-dev-shm-usage')
            co.set_argument('--disable-gpu')
            co.set_argument('--disable-blink-features=AutomationControlled')
            co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

            # 设置页面加载策略为eager，避免等待所有资源加载完成
            co.set_argument('--page-load-strategy=eager')

            self.driver = ChromiumPage(addr_or_opts=co)
            logger.info('✓ 浏览器初始化成功')
            return True
        except Exception as e:
            logger.error(f'浏览器初始化失败: {e}', exc_info=True)
            return False

    def get_qr_code(self):
        """获取知乎二维码图片"""
        try:
            if not self.driver:
                if not self.init_browser():
                    return False, None, '浏览器初始化失败'

            logger.info('访问知乎登录页面...')

            # 设置更短的超时时间
            self.driver.set.timeouts(base=10, page_load=30)

            try:
                self.driver.get(self.login_url)
            except Exception as e:
                logger.warning(f'页面加载超时，但继续尝试: {e}')

            # 等待页面部分加载
            time.sleep(3)

            # 尝试点击二维码登录标签
            try:
                qr_tab = self.driver.ele('text:二维码登录', timeout=3)
                if qr_tab:
                    qr_tab.click()
                    time.sleep(2)
                    logger.info('已切换到二维码登录')
            except:
                logger.info('可能已经是二维码登录页面')

            # 查找并获取二维码图片
            qr_selectors = [
                '.qrcode-img img',
                '.SignFlow-qrcode img',
                'img[alt*="二维码"]',
                '.qrcode img',
                'canvas',  # 有些网站用canvas显示二维码
            ]

            for selector in qr_selectors:
                try:
                    qr_img = self.driver.ele(selector, timeout=2)
                    if qr_img:
                        logger.info(f'找到二维码元素: {selector}')

                        # 尝试获取src
                        qr_src = qr_img.attr('src')
                        if qr_src and qr_src.startswith('data:image'):
                            qr_base64 = qr_src.split(',')[1]
                            logger.info('✓ 获取二维码成功(base64)')
                            return True, qr_base64, '二维码获取成功'
                        elif qr_src and qr_src.startswith('http'):
                            import requests
                            resp = requests.get(qr_src, timeout=10)
                            qr_base64 = base64.b64encode(resp.content).decode('utf-8')
                            logger.info('✓ 获取二维码成功(URL)')
                            return True, qr_base64, '二维码获取成功'

                        # 截图方式
                        screenshot = qr_img.get_screenshot(as_bytes=True)
                        qr_base64 = base64.b64encode(screenshot).decode('utf-8')
                        logger.info('✓ 获取二维码成功(截图)')
                        return True, qr_base64, '二维码获取成功'
                except Exception as e:
                    logger.debug(f'尝试选择器 {selector} 失败: {e}')
                    continue

            # 如果都没找到，截取整个登录区域
            logger.warning('未找到二维码元素，截取登录区域')
            login_selectors = ['.SignFlow', '.Login-content', '[class*="SignFlow"]']
            for selector in login_selectors:
                try:
                    area = self.driver.ele(selector, timeout=2)
                    if area:
                        screenshot = area.get_screenshot(as_bytes=True)
                        qr_base64 = base64.b64encode(screenshot).decode('utf-8')
                        logger.info('✓ 获取登录区域截图')
                        return True, qr_base64, '二维码获取成功'
                except:
                    continue

            # 最后降级：截取整个页面
            screenshot = self.driver.get_screenshot(as_bytes=True)
            qr_base64 = base64.b64encode(screenshot).decode('utf-8')
            logger.info('✓ 获取页面截图')
            return True, qr_base64, '二维码获取成功'

        except Exception as e:
            logger.error(f'获取二维码失败: {e}', exc_info=True)
            return False, None, str(e)

    def wait_for_login(self, timeout=120):
        """等待用户扫码登录"""
        try:
            if not self.driver:
                return False, '浏览器未初始化'

            logger.info('开始等待用户扫码登录...')
            start_time = time.time()

            while time.time() - start_time < timeout:
                try:
                    current_url = self.driver.url
                    logger.debug(f'当前URL: {current_url}')

                    # 检查是否已经跳转（登录成功）
                    if 'zhihu.com' in current_url and '/signin' not in current_url:
                        logger.info('✓ 检测到URL跳转，登录成功!')
                        time.sleep(2)  # 等待页面稳定
                        return True, '登录成功'

                    # 检查页面内容
                    try:
                        page_html = self.driver.html
                        if any(x in page_html for x in ['我的主页', '退出登录', '个人中心', '首页']):
                            logger.info('✓ 检测到登录标识，登录成功!')
                            time.sleep(2)
                            return True, '登录成功'
                    except:
                        pass

                except Exception as e:
                    logger.debug(f'检查登录状态时出错: {e}')

                time.sleep(2)

            logger.warning('等待登录超时')
            return False, '登录超时，请重试'

        except Exception as e:
            logger.error(f'等待登录失败: {e}', exc_info=True)
            return False, str(e)

    def save_cookies(self, username):
        """保存Cookie到文件"""
        try:
            if not self.driver:
                return False

            cookies = self.driver.cookies()
            cookie_file = os.path.join(self.cookies_dir, f'zhihu_{username}.json')

            # 转换为列表格式
            cookie_list = []
            for cookie in cookies:
                if isinstance(cookie, dict):
                    cookie_list.append(cookie)
                else:
                    # 如果是其他格式，尝试转换
                    cookie_list.append({
                        'name': getattr(cookie, 'name', ''),
                        'value': getattr(cookie, 'value', ''),
                        'domain': getattr(cookie, 'domain', ''),
                        'path': getattr(cookie, 'path', '/')
                    })

            with open(cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookie_list, f, ensure_ascii=False, indent=2)

            logger.info(f'✓ Cookie已保存: {cookie_file} (共{len(cookie_list)}个)')
            return True

        except Exception as e:
            logger.error(f'保存Cookie失败: {e}', exc_info=True)
            return False

    def get_driver(self):
        """获取浏览器驱动"""
        return self.driver

    def close(self):
        """关闭浏览器"""
        try:
            if self.driver:
                self.driver.quit()
                logger.info('浏览器已关闭')
                self.driver = None
        except Exception as e:
            logger.warning(f'关闭浏览器时出错: {e}')
'''

    # 2. 更新API端点，支持完整的登录流程
    print("\n更新二维码登录模块...")
    stdin, stdout, stderr = ssh.exec_command(
        f"cat > {DEPLOY_DIR}/backend/zhihu_auth/zhihu_qr_login.py << 'EOFFILE'\n{qr_login_code}\nEOFFILE"
    )
    stdout.read()
    print("✓ 二维码登录模块已更新")

    # 3. 更新API路由，添加等待登录的端点
    api_update = '''
# 在api.py中的zhihu/qr_login/check端点中，需要等待登录完成
@api_bp.route('/zhihu/qr_login/wait', methods=['POST'])
@login_required
def wait_zhihu_qr_login():
    """等待二维码登录完成（阻塞式）"""
    user = get_current_user()
    data = request.json
    session_id = data.get('session_id')
    timeout = data.get('timeout', 120)  # 默认120秒超时

    if not session_id:
        return jsonify({'success': False, 'error': '缺少session_id'}), 400

    try:
        # 获取QR登录会话
        if not hasattr(api_bp, 'qr_login_sessions') or session_id not in api_bp.qr_login_sessions:
            return jsonify({'success': False, 'error': '登录会话不存在或已过期'}), 404

        qr_login = api_bp.qr_login_sessions[session_id]

        # 等待登录（阻塞式）
        success, message = qr_login.wait_for_login(timeout=timeout)

        if success:
            # 登录成功，保存Cookie
            qr_login.save_cookies(user.username)

            # 清理会话
            qr_login.close()
            del api_bp.qr_login_sessions[session_id]

            return jsonify({
                'success': True,
                'logged_in': True,
                'message': '登录成功，Cookie已保存'
            })
        else:
            # 登录失败或超时
            qr_login.close()
            del api_bp.qr_login_sessions[session_id]

            return jsonify({
                'success': False,
                'logged_in': False,
                'message': message
            })

    except Exception as e:
        logger.error(f'Wait for QR login failed: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
'''

    # 4. 读取当前的api.py
    print("\n读取当前API文件...")
    stdin, stdout, stderr = ssh.exec_command(f"cat {DEPLOY_DIR}/backend/blueprints/api.py")
    api_content = stdout.read().decode('utf-8')

    # 检查是否已经有wait端点
    if '/zhihu/qr_login/wait' not in api_content:
        print("添加wait端点到API...")
        # 在check端点后面添加wait端点
        insert_pos = api_content.find('@api_bp.route(\'/publish_history\'')
        if insert_pos > 0:
            new_api_content = api_content[:insert_pos] + api_update + '\n\n' + api_content[insert_pos:]

            stdin, stdout, stderr = ssh.exec_command(
                f"cat > {DEPLOY_DIR}/backend/blueprints/api.py << 'EOFFILE'\n{new_api_content}\nEOFFILE"
            )
            stdout.read()
            print("✓ API已更新")
        else:
            print("⚠ 无法找到插入位置，跳过API更新")
    else:
        print("✓ wait端点已存在")

    # 5. 更新前端publish.js，实现完整流程
    frontend_update = '''
// 处理二维码登录
async function handleQRLogin(article) {
    try {
        showLoading('正在获取登录二维码...');

        // 1. 获取二维码
        const response = await fetch('/api/zhihu/qr_login/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (!data.success) {
            hideLoading();
            alert(`获取二维码失败：${data.error || '未知错误'}`);
            return;
        }

        // 2. 显示二维码并开始等待登录
        showQRCodeModal(data.qr_code, data.session_id, article);

    } catch (error) {
        hideLoading();
        alert('获取二维码失败: ' + error.message);
    }
}

// 显示二维码弹窗
function showQRCodeModal(qrCodeDataUrl, sessionId, article) {
    hideLoading();

    const modal = document.createElement('div');
    modal.id = 'qr-login-modal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10000;
    `;

    modal.innerHTML = `
        <div style="background: white; padding: 30px; border-radius: 10px; text-align: center; max-width: 400px;">
            <h3 style="margin-bottom: 20px;">扫码登录知乎</h3>
            <img src="${qrCodeDataUrl}" alt="登录二维码" style="width: 250px; height: 250px; margin: 20px auto; display: block; border: 1px solid #ddd;">
            <p style="color: #666; margin: 15px 0;">请使用知乎APP扫描二维码登录</p>
            <p id="qr-login-status" style="color: #3b82f6; font-weight: bold;">等待扫码中...</p>
            <button id="qr-cancel-btn" style="margin-top: 20px; padding: 10px 30px; background: #ef4444; color: white; border: none; border-radius: 5px; cursor: pointer;">取消</button>
        </div>
    `;

    document.body.appendChild(modal);

    let cancelled = false;

    document.getElementById('qr-cancel-btn').addEventListener('click', () => {
        cancelled = true;
        document.body.removeChild(modal);
    });

    // 开始等待登录（使用长轮询）
    waitForQRLogin(sessionId, article, modal).catch(err => {
        if (!cancelled) {
            hideLoading();
            alert('登录失败: ' + err.message);
            document.body.removeChild(modal);
        }
    });
}

// 等待二维码登录完成
async function waitForQRLogin(sessionId, article, modal) {
    const statusElement = document.getElementById('qr-login-status');

    try {
        statusElement.textContent = '等待扫码登录...';
        statusElement.style.color = '#3b82f6';

        // 调用wait端点（会阻塞直到登录成功或超时）
        const response = await fetch('/api/zhihu/qr_login/wait', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId,
                timeout: 120  // 120秒超时
            })
        });

        const data = await response.json();

        if (data.success && data.logged_in) {
            // 登录成功
            statusElement.textContent = '✓ 登录成功！正在发布...';
            statusElement.style.color = '#10b981';

            // 等待1秒让用户看到成功提示
            await new Promise(resolve => setTimeout(resolve, 1000));

            // 关闭弹窗
            document.body.removeChild(modal);

            // 继续发布流程
            await publishArticleAfterLogin(article);
        } else {
            // 登录失败或超时
            statusElement.textContent = '✗ ' + (data.message || '登录失败');
            statusElement.style.color = '#ef4444';

            await new Promise(resolve => setTimeout(resolve, 2000));
            document.body.removeChild(modal);

            alert('登录失败：' + (data.message || '未知错误'));
        }

    } catch (error) {
        console.error('Wait for login error:', error);
        statusElement.textContent = '✗ 登录出错';
        statusElement.style.color = '#ef4444';

        await new Promise(resolve => setTimeout(resolve, 1000));
        document.body.removeChild(modal);

        throw error;
    }
}

// 登录后发布文章
async function publishArticleAfterLogin(article) {
    showLoading('正在发布到知乎...');

    try {
        const response = await fetch('/api/publish_zhihu', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: article.title,
                content: article.content,
                article_id: article.id || 0
            })
        });

        const data = await response.json();
        hideLoading();

        if (data.success) {
            alert(`发布成功！\\n${data.message || ''}`);
            loadPublishHistory();
        } else {
            alert(`发布失败：${data.message || data.error || '未知错误'}`);
        }
    } catch (error) {
        hideLoading();
        alert('发布失败: ' + error.message);
    }
}
'''

    print("\n更新前端JavaScript...")
    stdin, stdout, stderr = ssh.exec_command(f"cat {DEPLOY_DIR}/static/publish.js")
    publish_js = stdout.read().decode('utf-8')

    # 检查是否需要更新
    if 'waitForQRLogin' not in publish_js:
        # 找到handleQRLogin函数的位置并替换
        import_start = publish_js.find('// 处理二维码登录')
        if import_start > 0:
            import_end = publish_js.find('// 停止轮询', import_start)
            if import_end > 0:
                # 找到下一个函数的开始
                next_func = publish_js.find('\n// ', import_end + 20)
                if next_func > 0:
                    new_publish_js = publish_js[:import_start] + frontend_update + '\n\n' + publish_js[next_func:]

                    stdin, stdout, stderr = ssh.exec_command(
                        f"cat > {DEPLOY_DIR}/static/publish.js << 'EOFFILE'\n{new_publish_js}\nEOFFILE"
                    )
                    stdout.read()
                    print("✓ 前端已更新")
                else:
                    print("⚠ 无法找到插入位置")
            else:
                print("⚠ 无法找到替换位置")
        else:
            print("⚠ 无法找到handleQRLogin函数")
    else:
        print("✓ 前端已包含完整流程")

    # 6. 重启服务
    print("\n重启服务...")
    stdin, stdout, stderr = ssh.exec_command("pkill -f gunicorn; sleep 2")
    stdout.read()

    start_cmd = f"bash {DEPLOY_DIR}/start_service.sh"
    stdin, stdout, stderr = ssh.exec_command(start_cmd)
    print(stdout.read().decode('utf-8', errors='ignore'))

    time.sleep(3)

    # 测试
    print("\n测试健康检查...")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8080/api/health")
    print(stdout.read().decode('utf-8', errors='ignore'))

    print("\n✓ 部署完成")
    print("\n完整流程说明:")
    print("1. 用户点击'开始发布'按钮")
    print("2. 系统检测到未配置账号，弹出二维码")
    print("3. 用户使用知乎APP扫码登录")
    print("4. 系统检测到登录成功，自动保存Cookie")
    print("5. 自动调用发布接口发布文章")
    print("6. 下次发布时直接使用Cookie，无需再次扫码")

    ssh.close()

if __name__ == '__main__':
    main()
