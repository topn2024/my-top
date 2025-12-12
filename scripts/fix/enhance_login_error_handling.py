#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强登录错误处理 - 捕获知乎网站的具体错误信息
"""
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def main():
    try:
        print("="*80)
        print("🔧 增强登录错误处理")
        print("="*80)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("✓ SSH连接成功\n")

        # 备份原文件
        print("[1/3] 备份原文件...")
        cmd = """
cd /home/u_topn/TOP_N/backend
cp login_tester_ultimate.py login_tester_ultimate.py.backup_$(date +%Y%m%d_%H%M%S)
echo "✓ 备份完成"
"""
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        print(stdout.read().decode('utf-8'))

        # 创建增强版的登录验证函数
        print("\n[2/3] 创建增强版登录验证...")
        enhanced_code = """
cat > /tmp/enhanced_login.py << 'PYEOF'
# 读取原文件
with open('/home/u_topn/TOP_N/backend/login_tester_ultimate.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 找到 _password_login_drission 方法并增强错误处理
import re

# 查找并替换 _password_login_drission 方法
old_method_pattern = r'(def _password_login_drission\(self, username, password\):.*?)(return \{[^}]+\})'

enhanced_method = '''def _password_login_drission(self, username, password):
        """使用 DrissionPage 进行密码登录"""
        from DrissionPage import ChromiumPage, ChromiumOptions

        try:
            # 初始化配置
            co = ChromiumOptions()
            if self.headless:
                co.headless()

            # 反检测设置
            co.set_argument('--disable-blink-features=AutomationControlled')
            co.set_argument('--disable-dev-shm-usage')
            co.set_argument('--no-sandbox')
            co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

            page = ChromiumPage(addr_or_opts=co)
            self.logger.info("✓ DrissionPage initialized successfully")

            # 访问知乎登录页
            page.get('https://www.zhihu.com/signin', timeout=15)
            page.wait(2)

            # 切换到密码登录
            try:
                password_tab = page.ele('text:密码登录', timeout=5)
                if password_tab:
                    password_tab.click()
                    page.wait(1)
                    self.logger.info("✓ 切换到密码登录模式")
            except Exception as e:
                self.logger.warning(f"未找到密码登录标签，可能已在密码登录模式: {e}")

            # 输入用户名
            try:
                username_input = page.ele('@name=username', timeout=5)
                if username_input:
                    username_input.clear()
                    username_input.input(username)
                    page.wait(0.5)
                    self.logger.info("✓ 用户名输入完成")
            except Exception as e:
                error_msg = f"输入用户名失败: {str(e)}"
                self.logger.error(error_msg)
                page.quit()
                return {"success": False, "message": error_msg}

            # 输入密码
            try:
                password_input = page.ele('@name=password', timeout=5)
                if password_input:
                    password_input.clear()
                    password_input.input(password)
                    page.wait(0.5)
                    self.logger.info("✓ 密码输入完成")
            except Exception as e:
                error_msg = f"输入密码失败: {str(e)}"
                self.logger.error(error_msg)
                page.quit()
                return {"success": False, "message": error_msg}

            # 点击登录按钮
            try:
                login_btn = page.ele('text:登录', timeout=5)
                if login_btn:
                    login_btn.click()
                    self.logger.info("✓ 登录按钮已点击")
                    page.wait(3)
            except Exception as e:
                error_msg = f"点击登录按钮失败: {str(e)}"
                self.logger.error(error_msg)
                page.quit()
                return {"success": False, "message": error_msg}

            # 等待并检查登录结果
            page.wait(5)

            # 检查是否有错误提示
            error_messages = []
            try:
                # 知乎常见错误提示选择器
                error_selectors = [
                    '.SignFlow-error',
                    '.Error-message',
                    '[class*="error"]',
                    '[class*="Error"]',
                    'text:账号或密码错误',
                    'text:请输入验证码',
                    'text:请先完成验证',
                    'text:登录失败'
                ]

                for selector in error_selectors:
                    try:
                        error_ele = page.ele(selector, timeout=1)
                        if error_ele:
                            error_text = error_ele.text.strip()
                            if error_text and error_text not in error_messages:
                                error_messages.append(error_text)
                                self.logger.warning(f"发现错误提示: {error_text}")
                    except:
                        continue

            except Exception as e:
                self.logger.debug(f"检查错误提示时出现异常: {e}")

            # 检查验证码
            captcha_detected = False
            try:
                captcha_elements = [
                    page.ele('.yidun', timeout=1),
                    page.ele('[class*="captcha"]', timeout=1),
                    page.ele('[class*="Captcha"]', timeout=1),
                ]
                for ele in captcha_elements:
                    if ele:
                        captcha_detected = True
                        error_messages.append("检测到验证码，需要人工处理")
                        self.logger.warning("⚠ 检测到验证码")
                        break
            except:
                pass

            # 检查是否登录成功
            current_url = page.url
            page_html = page.html

            # 登录成功的特征
            success_indicators = [
                'www.zhihu.com' in current_url and 'signin' not in current_url,
                'Topstory' in page_html,
                '退出登录' in page_html,
                '我的主页' in page_html,
            ]

            is_success = any(success_indicators)

            # 截图保存（用于调试）
            try:
                screenshot_path = f'/tmp/zhihu_login_{username}.png'
                page.get_screenshot(path=screenshot_path)
                self.logger.info(f"截图已保存: {screenshot_path}")
            except Exception as e:
                self.logger.debug(f"截图失败: {e}")

            page.quit()

            if is_success:
                self.logger.info("✅ 登录成功")
                return {"success": True, "message": "登录成功"}
            else:
                # 构建详细的失败信息
                if error_messages:
                    error_detail = " | ".join(error_messages)
                    fail_msg = f"登录失败: {error_detail}"
                elif captcha_detected:
                    fail_msg = "登录失败: 需要完成验证码验证"
                else:
                    fail_msg = "登录失败: 未检测到登录成功标识，可能是账号密码错误或需要额外验证"

                self.logger.error(fail_msg)
                return {"success": False, "message": fail_msg}

        except Exception as e:
            error_msg = f"DrissionPage 登录异常: {str(e)}"
            self.logger.error(error_msg)
            import traceback
            self.logger.error(traceback.format_exc())
            try:
                page.quit()
            except:
                pass
            return {"success": False, "message": error_msg}'''

# 使用正则替换
content_new = re.sub(
    old_method_pattern,
    enhanced_method,
    content,
    flags=re.DOTALL
)

# 如果没有匹配到，说明方法签名可能不同，直接追加
if content_new == content:
    print("警告: 未找到 _password_login_drission 方法，可能需要手动修改")
else:
    # 写入文件
    with open('/home/u_topn/TOP_N/backend/login_tester_ultimate.py', 'w', encoding='utf-8') as f:
        f.write(content_new)
    print("✓ 已增强登录错误处理")

PYEOF

# 执行Python脚本
python3 /tmp/enhanced_login.py
"""
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        print(output)
        if error:
            print(f"错误输出: {error}")

        # 重启服务
        print("\n[3/3] 重启服务...")
        cmd = "sudo systemctl restart topn && sleep 3"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
        import time
        time.sleep(4)

        # 验证服务状态
        cmd = "sudo systemctl status topn --no-pager -l | head -20"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        print(stdout.read().decode('utf-8'))

        print("\n" + "="*80)
        print("✅ 增强完成！")
        print("="*80)
        print("\n现在登录测试会显示详细的错误信息:")
        print("1. 捕获知乎页面上的错误提示")
        print("2. 检测验证码要求")
        print("3. 提供详细的失败原因")
        print("4. 保存截图到 /tmp/ 用于调试")
        print("\n请重新测试账号登录")

        ssh.close()
        return True

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
