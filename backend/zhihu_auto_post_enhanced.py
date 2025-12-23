#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知乎自动发帖模块（增强版）
支持Cookie登录和自动密码登录fallback
"""
import time
import logging
import json
import os
import sys

logger = logging.getLogger(__name__)

class ZhihuAutoPost:
    """知乎自动发帖"""

    def __init__(self, mode='drission'):
        self.mode = mode
        self.page = None
        self.is_logged_in = False

    def init_browser(self):
        """初始化浏览器"""
        try:
            from DrissionPage import ChromiumPage, ChromiumOptions
            co = ChromiumOptions()

            # 服务器环境检测：如果没有显示器则使用headless模式
            import os
            is_server = not os.environ.get('DISPLAY')
            import shutil
            # 明确指定Chrome浏览器路径（修复DrissionPage找不到chrome的问题）
            chrome_path = shutil.which("google-chrome") or shutil.which("chrome") or "/usr/bin/google-chrome"
            co.set_browser_path(chrome_path)
            logger.info(f"使用Chrome路径: {chrome_path}")

            if is_server:
                logger.info("检测到服务器环境，使用headless模式")
                co.headless(True)
                co.set_argument('--no-sandbox')
                co.set_argument('--disable-dev-shm-usage')
                co.set_argument('--disable-gpu')
            else:
                co.headless(False)  # 可见模式,方便调试

            co.set_argument('--disable-blink-features=AutomationControlled')
            co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            self.page = ChromiumPage(addr_or_opts=co)
            logger.info("✓ 浏览器初始化成功")
            return True
        except Exception as e:
            logger.error(f"✗ 浏览器初始化失败: {e}", exc_info=True)
            return False

    def load_cookies(self, username):
        """加载已保存的Cookie"""
        try:
            # 尝试从backend/cookies目录加载
            cookies_dir = os.path.join(os.path.dirname(__file__), 'cookies')
            cookie_file = os.path.join(cookies_dir, f'zhihu_{username}.json')

            if not os.path.exists(cookie_file):
                logger.warning(f"Cookie文件不存在: {cookie_file}")
                return False

            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)

            # 先访问知乎主页
            self.page.get('https://www.zhihu.com')
            time.sleep(1)

            # 加载Cookie
            for cookie in cookies:
                try:
                    self.page.set.cookies(cookie)
                except Exception as e:
                    logger.debug(f"设置Cookie失败: {cookie.get('name')} - {e}")

            logger.info(f"✓ Cookie加载完成,共{len(cookies)}个")

            # 刷新页面验证登录状态
            self.page.refresh()
            time.sleep(2)

            return self.verify_login()

        except Exception as e:
            logger.error(f"✗ 加载Cookie失败: {e}")
            return False

    def auto_login_with_password(self, username, password):
        """
        使用密码自动登录（当Cookie不存在或失效时的fallback）

        Args:
            username: 知乎账号
            password: 密码

        Returns:
            bool: 是否登录成功
        """
        try:
            logger.info("=" * 60)
            logger.info("开始自动密码登录流程（Cookie失效，使用测试账号登录）")
            logger.info("=" * 60)

            # 尝试导入login_tester模块
            try:
                # 添加backend目录到sys.path
                backend_dir = os.path.dirname(__file__)
                if backend_dir not in sys.path:
                    sys.path.insert(0, backend_dir)

                from login_tester import LoginTester
                logger.info("✓ login_tester模块导入成功")
            except ImportError as e:
                logger.error(f"✗ 无法导入login_tester模块: {e}")
                logger.error("自动登录功能需要login_tester.py模块支持")
                return False

            # 创建登录测试器实例（使用headless模式）
            tester = LoginTester(headless=True)

            # 初始化WebDriver
            if not tester.init_driver():
                logger.error("✗ WebDriver初始化失败")
                return False

            try:
                # 执行知乎登录
                logger.info(f"正在使用测试账号登录: {username}")
                result = tester.test_zhihu_login(username, password, use_cookie=False)

                if result.get('success'):
                    logger.info("✓✓ 测试账号自动登录成功！")

                    # 保存Cookie
                    logger.info("正在保存登录Cookie...")
                    if tester.save_cookies('知乎', username):
                        logger.info("✓ Cookie已保存，下次可以直接使用Cookie登录")
                    else:
                        logger.warning("⚠ Cookie保存失败，下次仍需要密码登录")

                    # 关闭测试用的driver
                    tester.close_driver()

                    # 重新加载Cookie到DrissionPage
                    logger.info("正在将Cookie加载到DrissionPage...")
                    if self.load_cookies(username):
                        logger.info("✓ Cookie已加载到发布浏览器")
                        return True
                    else:
                        logger.error("✗ Cookie加载到发布浏览器失败")
                        return False
                else:
                    logger.error(f"✗ 自动登录失败: {result.get('message', '未知错误')}")
                    return False

            finally:
                # 确保关闭driver
                tester.close_driver()

        except Exception as e:
            logger.error(f"✗ 自动登录过程中发生异常: {e}", exc_info=True)
            return False

    def verify_login(self):
        """验证是否已登录"""
        try:
            current_url = self.page.url
            page_html = self.page.html

            # 检查登录标识
            login_indicators = ['我的主页', '退出登录', '个人中心', '创作中心']

            for indicator in login_indicators:
                if indicator in page_html:
                    self.is_logged_in = True
                    logger.info(f"✓✓ 登录验证成功,检测到: {indicator}")
                    return True

            logger.warning("⚠ 未检测到登录标识,可能未登录")
            return False

        except Exception as e:
            logger.error(f"✗ 登录验证失败: {e}")
            return False

    def create_article(self, title, content, topics=None, draft=False):
        """创建文章

        Args:
            title: 文章标题
            content: 文章内容(支持HTML或Markdown)
            topics: 话题列表,如 ['Python', '编程']
            draft: 是否保存为草稿(True)或直接发布(False)
        """
        try:
            if not self.is_logged_in:
                logger.error("未登录,无法发帖")
                return {'success': False, 'message': '未登录'}

            # 访问创作页面
            logger.info("正在进入创作页面...")
            self.page.get('https://zhuanlan.zhihu.com/write')
            time.sleep(3)

            # 等待编辑器加载
            logger.info("等待编辑器加载...")
            time.sleep(2)

            # 输入标题
            logger.info("正在输入标题...")
            try:
                title_input = self.page.ele('css:.WriteIndex-titleInput', timeout=5)
                if title_input:
                    title_input.clear()
                    title_input.input(title)
                    logger.info(f"✓ 标题已输入: {title[:30]}...")
                else:
                    # 备用选择器
                    title_input = self.page.ele('css:textarea[placeholder*="标题"]', timeout=3)
                    if title_input:
                        title_input.clear()
                        title_input.input(title)
                        logger.info(f"✓ 标题已输入(备用方法): {title[:30]}...")
            except Exception as e:
                logger.error(f"✗ 标题输入失败: {e}")
                return {'success': False, 'message': f'标题输入失败: {e}'}

            time.sleep(1)

            # 输入正文内容
            logger.info("正在输入正文...")
            try:
                # 尝试多种编辑器定位方式
                editor_selectors = [
                    'css:.public-DraftEditor-content',
                    'css:[contenteditable="true"]',
                    'css:.notranslate',
                    'css:[data-text="true"]'
                ]

                editor = None
                for selector in editor_selectors:
                    try:
                        editor = self.page.ele(selector, timeout=2)
                        if editor:
                            logger.info(f"✓ 找到编辑器: {selector}")
                            break
                    except:
                        continue

                if editor:
                    # 点击编辑器激活
                    editor.click()
                    time.sleep(0.5)

                    # 输入内容 - 一次性输入完整内容，避免被覆盖
                    logger.info(f"准备输入内容，长度: {len(content)} 字符")
                    editor.input(content, clear=True)
                    time.sleep(1)

                    # 验证内容是否输入成功
                    paragraphs = content.split('\n\n')
                    logger.info(f"✓ 正文已输入,共{len(paragraphs)}段")
                else:
                    logger.error("✗ 未找到编辑器元素")
                    return {'success': False, 'message': '未找到编辑器'}

            except Exception as e:
                logger.error(f"✗ 正文输入失败: {e}")
                return {'success': False, 'message': f'正文输入失败: {e}'}

            time.sleep(2)

            # 添加话题标签(如果提供)
            if topics:
                logger.info(f"正在添加话题: {topics}")
                try:
                    # 查找话题输入框
                    topic_input = self.page.ele('css:input[placeholder*="话题"]', timeout=3)
                    if topic_input:
                        for topic in topics:
                            topic_input.input(topic)
                            time.sleep(0.5)
                            # 按回车确认
                            topic_input.input('\n')
                            time.sleep(0.5)
                        logger.info(f"✓ 话题已添加: {topics}")
                except Exception as e:
                    logger.warning(f"话题添加失败(非关键): {e}")

            # 发布或保存草稿
            if draft:
                logger.info("正在保存草稿...")
                try:
                    save_draft_btn = self.page.ele('text:保存草稿', timeout=3)
                    if save_draft_btn:
                        save_draft_btn.click()
                        time.sleep(2)
                        logger.info("✓✓ 草稿保存成功")
                        return {'success': True, 'message': '草稿保存成功', 'type': 'draft'}
                except Exception as e:
                    logger.warning(f"保存草稿按钮未找到: {e}")
            else:
                logger.info("正在发布文章...")
                try:
                    # 查找发布按钮
                    publish_selectors = [
                        'text:发布文章',
                        'text:发布',
                        'css:button.PublishButton',
                        'css:button[type="submit"]'
                    ]

                    publish_btn = None
                    for selector in publish_selectors:
                        try:
                            publish_btn = self.page.ele(selector, timeout=2)
                            if publish_btn:
                                logger.info(f"✓ 找到发布按钮: {selector}")
                                break
                        except:
                            continue

                    if publish_btn:
                        logger.info("步骤3/5: 点击发布按钮...")
                        publish_btn.click()
                        logger.info("✓ 已点击发布按钮，等待页面响应...")
                        time.sleep(8)  # 延长等待时间从3秒到8秒

                        # 步骤4/5: 处理发布设置弹窗（重要！）
                        logger.info("步骤4/5: 检查发布设置弹窗...")

                        # 调试：保存当前页面截图和HTML(仅在DEBUG模式)
                        try:
                            import tempfile
                            debug_dir = '/tmp/zhihu_debug'
                            os.makedirs(debug_dir, exist_ok=True)

                            # 保存截图
                            screenshot_path = os.path.join(debug_dir, 'after_publish_click.png')
                            self.page.get_screenshot(screenshot_path)
                            logger.debug(f"✓ 截图已保存: {screenshot_path}")

                            # 保存HTML
                            html_path = os.path.join(debug_dir, 'after_publish_click.html')
                            with open(html_path, 'w', encoding='utf-8') as f:
                                f.write(self.page.html)
                            logger.debug(f"✓ HTML已保存: {html_path}")
                        except Exception as e:
                            logger.debug(f"保存调试信息失败: {e}")

                        # 知乎现在显示"发布设置"面板，需要点击面板底部的"发布"按钮
                        modal_found = False
                        modal_publish_selectors = [
                            # 新版知乎发布设置面板中的发布按钮
                            'css:button.Button--primary.Button--blue',  # 主要按钮样式
                            'css:.css-1ppjin3 button.Button--primary',  # 发布设置面板底部的主按钮
                            # 旧版选择器（向后兼容）
                            'text:发布文章',
                            'css:.Modal button.Button--primary',
                            'css:div[role="dialog"] button:has-text("发布")',
                            'css:.PublishPanel button.Button--primary',
                        ]

                        for selector in modal_publish_selectors:
                            try:
                                modal_btn = self.page.ele(selector, timeout=2)
                                if modal_btn:
                                    modal_text = modal_btn.text.strip()
                                    logger.info(f"✓ 找到可能的发布按钮: selector='{selector}', text='{modal_text}'")

                                    # 确保这是发布设置对话框中的按钮
                                    if '发布' in modal_text:
                                        logger.info(f"✓ 确认为发布按钮，准备点击")
                                        modal_btn.click()
                                        logger.info("✓ 已点击弹窗中的发布按钮")
                                        modal_found = True
                                        time.sleep(8)  # 延长等待时间
                                        break
                            except Exception as e:
                                logger.debug(f"选择器 '{selector}' 未找到元素: {e}")
                                continue

                        if not modal_found:
                            logger.warning("⚠ 未检测到发布设置弹窗，可能已直接发布或页面结构变化")

                        # 步骤5/5: 验证发布结果(带重试机制)
                        logger.info("步骤5/5: 验证发布结果...")

                        # 重试机制: 最多验证2次
                        max_retries = 2
                        publish_success = False
                        current_url = None
                        success_indicators = []

                        for retry_count in range(max_retries):
                            if retry_count > 0:
                                logger.info(f"第{retry_count + 1}次验证(重试 {retry_count})...")
                                time.sleep(6)  # 重试前额外等待6秒
                            else:
                                time.sleep(5)  # 首次验证等待5秒

                            current_url = self.page.url
                            logger.info(f"当前URL: {current_url}")

                            # 判断发布成功的标准
                            success_indicators = []

                            # 1. URL必须不包含 /edit（关键！）
                            if '/edit' not in current_url:
                                success_indicators.append("URL不包含/edit（已退出编辑模式）")
                            else:
                                logger.warning("⚠ URL仍然包含/edit，文章可能未真正发布")

                            # 2. URL应该包含文章ID
                            if '/p/' in current_url or '/zhuanlan/' in current_url:
                                success_indicators.append("URL包含文章路径")

                            # 3. URL应该不是write页面
                            if 'write' not in current_url:
                                success_indicators.append("URL已离开写作页面")

                            # 4. 检查页面是否有编辑按钮（发布后的文章页会有编辑按钮）
                            try:
                                # 如果能找到"编辑文章"按钮，说明在文章查看页面
                                edit_btn = self.page.ele('text:编辑文章', timeout=2)
                                if edit_btn:
                                    success_indicators.append("找到文章编辑按钮（说明在已发布文章页面）")
                            except:
                                pass

                            # 5. 检查是否有发布成功的提示
                            try:
                                page_html = self.page.html
                                if '发布成功' in page_html or '已发布' in page_html:
                                    success_indicators.append("页面显示发布成功")
                            except:
                                pass

                            # 综合判断
                            logger.info(f"成功指标数量: {len(success_indicators)}")
                            logger.info(f"成功指标: {success_indicators}")

                            # 关键判断:URL不能包含/edit
                            if '/edit' not in current_url:
                                logger.info(f"✓ 发布验证成功(第{retry_count + 1}次尝试)")
                                publish_success = True
                                break
                            else:
                                if retry_count < max_retries - 1:
                                    logger.warning(f"⚠ 第{retry_count + 1}次验证失败,URL仍包含/edit,将进行重试...")
                                else:
                                    logger.error("✗ 所有重试均失败,文章未真正发布")

                        # 最终判断
                        if not publish_success:
                            error_msg = "文章未真正发布，仍在编辑状态"
                            logger.error(f"✗ {error_msg}")
                            return {
                                'success': False,
                                'message': error_msg,
                                'url': current_url
                            }

                        # 发布成功
                        logger.info(f"✓✓✓ 文章已成功发布! URL: {current_url}")
                        return {
                            'success': True,
                            'message': '文章发布成功',
                            'type': 'published',
                            'url': current_url
                        }

                    else:
                        logger.error("✗ 未找到发布按钮")
                        return {'success': False, 'message': '未找到发布按钮'}

                except Exception as e:
                    logger.error(f"✗ 发布失败: {e}")
                    return {'success': False, 'message': f'发布失败: {e}'}

        except Exception as e:
            logger.error(f"✗ 创建文章异常: {e}", exc_info=True)
            return {'success': False, 'message': str(e)}

    def close(self):
        """关闭浏览器"""
        try:
            if self.page:
                logger.info("正在关闭浏览器...")
                self.page.quit()
                logger.info("✓ 浏览器已关闭")
        except Exception as e:
            logger.warning(f"关闭浏览器时出错: {e}")


# 便捷函数 - 增强版支持自动登录
def post_article_to_zhihu(username, title, content, password=None, topics=None, draft=False):
    """
    一键发布文章到知乎（增强版 - 支持自动登录）

    Args:
        username: 知乎账号(用于加载Cookie)
        title: 文章标题
        content: 文章内容
        password: 密码（可选，当Cookie不存在时使用）
        topics: 话题列表
        draft: 是否保存为草稿

    Returns:
        {'success': True/False, 'message': '...', 'url': '...'}
    """
    logger.info("[发布流程-发布器] ========== 知乎发布器开始 ==========")
    logger.info(f"[发布流程-发布器] 用户名: {username}")
    logger.info(f"[发布流程-发布器] 文章标题: {title[:50]}")
    logger.info(f"[发布流程-发布器] 文章长度: {len(content)} 字符")
    logger.info(f"[发布流程-发布器] 是否草稿: {draft}")
    logger.info(f"[发布流程-发布器] 是否提供密码: {'是' if password else '否'}")

    poster = ZhihuAutoPost()

    try:
        # 初始化浏览器
        logger.info("[发布流程-发布器] 步骤1: 初始化浏览器")
        if not poster.init_browser():
            logger.error("[发布流程-发布器] 浏览器初始化失败")
            return {'success': False, 'message': '浏览器初始化失败'}

        logger.info("[发布流程-发布器] ✓ 浏览器初始化成功")

        # 尝试加载Cookie登录
        logger.info("=" * 60)
        logger.info("[发布流程-发布器] 步骤2: 尝试使用Cookie登录")
        logger.info("=" * 60)

        cookie_login_success = poster.load_cookies(username)

        if not cookie_login_success:
            # Cookie登录失败，尝试使用密码自动登录
            logger.warning("[发布流程-发布器] Cookie登录失败或Cookie不存在")

            if password:
                logger.info("=" * 60)
                logger.info("[发布流程-发布器] 步骤2.1: Cookie失效，尝试使用测试账号自动登录")
                logger.info("=" * 60)

                if not poster.auto_login_with_password(username, password):
                    logger.error("[发布流程-发布器] 自动登录失败")
                    return {
                        'success': False,
                        'message': 'Cookie登录失败，且测试账号自动登录也失败。请检查账号密码是否正确。'
                    }
                else:
                    logger.info("[发布流程-发布器] ✓✓ 自动登录成功，继续发布流程")
            else:
                logger.error("[发布流程-发布器] Cookie不存在且未提供密码")
                return {
                    'success': False,
                    'message': 'Cookie不存在且未提供密码，无法登录。请先在账号管理中配置知乎账号密码。'
                }
        else:
            logger.info("[发布流程-发布器] ✓ Cookie登录成功")

        # 登录成功，发布文章
        logger.info("=" * 60)
        logger.info("[发布流程-发布器] 步骤3: 开始发布文章到知乎")
        logger.info("=" * 60)

        result = poster.create_article(title, content, topics, draft)

        if result.get('success'):
            logger.info("[发布流程-发布器] ✓✓✓ 文章发布成功!")
            logger.info(f"[发布流程-发布器] 文章URL: {result.get('url')}")
        else:
            logger.error(f"[发布流程-发布器] ✗ 文章发布失败: {result.get('message')}")

        logger.info("[发布流程-发布器] ========== 知乎发布器结束 ==========")
        return result

    except Exception as e:
        logger.error(f"[发布流程-发布器] 发布过程异常: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'message': f'发布异常: {str(e)}'
        }
    finally:
        logger.debug("[发布流程-发布器] 关闭浏览器")
        poster.close()
