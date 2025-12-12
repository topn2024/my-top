#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知乎自动发帖模块
"""
import time
import logging
import json
import os

try:
    from DrissionPage import ChromiumPage, ChromiumOptions
    DRISSION_AVAILABLE = True
except ImportError:
    DRISSION_AVAILABLE = False
    ChromiumPage = None
    ChromiumOptions = None

logger = logging.getLogger(__name__)

class ZhihuAutoPost:
    """知乎自动发帖"""

    def __init__(self, mode='drission'):
        self.mode = mode
        self.page = None
        self.is_logged_in = False

    def init_browser(self):
        """初始化浏览器（服务器无头模式 - DrissionPage 4.x）"""
        try:
            co = ChromiumOptions()
            
            # DrissionPage 4.x 使用 set_argument 添加 headless
            co.set_argument('--headless=new')  # 新版headless模式
            co.set_argument('--no-sandbox')  # 必需
            co.set_argument('--disable-dev-shm-usage')
            co.set_argument('--disable-gpu')
            co.set_argument('--disable-software-rasterizer')
            co.set_argument('--window-size=1920,1080')
            co.set_argument('--disable-blink-features=AutomationControlled')
            
            # User-Agent
            co.set_user_agent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36')
            
            # 稳定性参数
            co.set_argument('--disable-extensions')
            co.set_argument('--disable-setuid-sandbox')
            co.set_argument('--remote-debugging-port=0')  # 随机端口避免冲突
            
            self.page = ChromiumPage(addr_or_opts=co)
            logger.info('✓ 知乎发布浏览器初始化成功（无头模式）')
            return True
        except Exception as e:
            logger.error(f'✗ 浏览器初始化失败: {e}', exc_info=True)
            return False

    def load_cookies(self, username):
        """加载已保存的Cookie"""
        try:
            cookies_dir = os.path.join(os.path.dirname(__file__), 'cookies')
            cookie_file = os.path.join(cookies_dir, f'zhihu_{username}.json')

            if not os.path.exists(cookie_file):
                logger.error(f"Cookie文件不存在: {cookie_file}")
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
                    # 优先使用class定位
                    '@class=public-DraftEditor-content',
                    '@class=notranslate public-DraftEditor-content',
                    '@class:public-DraftEditor-content',  # 包含class
                    # 备用：CSS选择器
                    'css:.public-DraftEditor-content',
                    'css:[contenteditable="true"]',
                    'css:.notranslate'
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

                    logger.info(f"开始输入正文内容，共{len(content)}字...")

                    # 方法1: 使用DrissionPage内置的input方法（最可靠）
                    try:
                        # 清空编辑器
                        editor.clear()
                        time.sleep(0.3)

                        # 使用DrissionPage的input方法输入内容
                        # 这个方法会自动触发所有必要的事件
                        editor.input(content)
                        logger.info("✓ 已使用DrissionPage.input()输入内容")
                        time.sleep(2)

                    except Exception as input_err:
                        logger.warning(f"DrissionPage.input()失败: {input_err}，尝试分段输入")

                        try:
                            # 方法2: 分段输入（每段500字符）
                            editor.clear()
                            time.sleep(0.3)

                            chunk_size = 500
                            total_len = len(content)
                            chunks = [content[i:i+chunk_size] for i in range(0, total_len, chunk_size)]

                            logger.info(f"分{len(chunks)}段输入，每段约{chunk_size}字符")
                            for i, chunk in enumerate(chunks, 1):
                                editor.input(chunk)
                                logger.info(f"✓ 已输入第{i}/{len(chunks)}段")
                                time.sleep(0.2)

                            logger.info(f"✓ 分段输入完成，共{len(chunks)}段")
                            time.sleep(2)

                        except Exception as chunk_err:
                            logger.error(f"分段输入失败: {chunk_err}，使用JavaScript备用方法")

                            # 方法3: JavaScript备用方法
                            js_content = content.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n').replace('\r', '\\r')
                            js_code = f"""
                            this.innerHTML = '';
                            this.textContent = '{js_content}';
                            var event = new Event('input', {{ bubbles: true }});
                            this.dispatchEvent(event);
                            return this.textContent.length;
                            """
                            result_length = editor.run_js(js_code)
                            logger.info(f"✓ JavaScript备用方法完成，长度: {result_length}")
                            time.sleep(2)

                    
                    # 验证内容 - 多次尝试读取
                    editor_text = None
                    for attempt in range(3):
                        time.sleep(0.5)
                        try:
                            editor_text = editor.text
                            if editor_text and len(editor_text) > 100:
                                break
                        except:
                            logger.warning(f"第{attempt+1}次读取编辑器内容失败，重试...")

                    if editor_text:
                        content_text = content.replace('\n\n', '').replace('\n', '').replace('\r', '')
                        editor_text_clean = editor_text.replace('\n', '').replace('\r', '')
                        similarity = len(editor_text_clean) / max(len(content_text), 1)

                        logger.info(f"✓ 正文验证: 编辑器{len(editor_text)}字 / 原文{len(content)}字 / 相似度{similarity*100:.1f}%")

                        if similarity < 0.8:  # 提高阈值到80%
                            error_msg = f"内容输入不完整: 相似度仅{similarity*100:.1f}%，编辑器{len(editor_text)}字，原文{len(content)}字"
                            logger.error(f"✗ {error_msg}")
                            try:
                                screenshot_path = f'/tmp/zhihu_content_error_{int(time.time())}.png'
                                self.page.get_screenshot(path=screenshot_path)
                                logger.info(f"已保存错误截图: {screenshot_path}")
                            except:
                                pass
                            return {'success': False, 'message': error_msg}
                    else:
                        error_msg = "无法读取编辑器内容，内容可能未正确输入"
                        logger.error(f"✗ {error_msg}")
                        try:
                            screenshot_path = f'/tmp/zhihu_no_content_{int(time.time())}.png'
                            self.page.get_screenshot(path=screenshot_path)
                            logger.info(f"已保存错误截图: {screenshot_path}")
                        except:
                            pass
                        return {'success': False, 'message': error_msg}

                    # 发布前截图验证
                    try:
                        screenshot_path = f'/tmp/zhihu_before_publish_{int(time.time())}.png'
                        self.page.get_screenshot(path=screenshot_path)
                        logger.info(f"发布前截图已保存: {screenshot_path}")
                    except Exception as e:
                        logger.warning(f"截图失败: {e}")
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

            # 发布或保存草稿 - 真正发布版本
            time.sleep(2)  # 确保内容已完全输入

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
                    logger.warning(f"保存草稿失败: {e}")
                    return {'success': False, 'message': f'保存草稿失败: {e}'}
            else:
                logger.info("开始发布流程...")
                try:
                    # 记录当前URL
                    start_url = self.page.url
                    logger.info(f"发布前URL: {start_url}")

                    # 第一步：查找并点击发布按钮
                    logger.info("步骤1/5: 查找发布按钮...")

                    # 知乎发布按钮选择器
                    publish_selectors = [
                        'text:发布文章',
                        'text:发布',
                        'css:button.Button--primary:has-text("发布")',
                        'css:button.PublishButton',
                    ]

                    publish_btn = None
                    for selector in publish_selectors:
                        try:
                            if selector.startswith('text:'):
                                # 查找所有匹配文本的按钮
                                btns = self.page.eles(selector, timeout=1)
                                for btn in btns:
                                    btn_text = btn.text.strip()
                                    # 必须是"发布文章"或者单纯的"发布"，不能包含"草稿"
                                    if (btn_text == '发布文章' or btn_text == '发布') and '草稿' not in btn_text:
                                        publish_btn = btn
                                        logger.info(f"✓ 找到发布按钮: 文本='{btn_text}'")
                                        break
                            else:
                                publish_btn = self.page.ele(selector, timeout=1)
                                if publish_btn:
                                    logger.info(f"✓ 找到发布按钮: {selector}")
                                    break
                        except:
                            continue

                        if publish_btn:
                            break

                    if not publish_btn:
                        error_msg = "未找到发布按钮"
                        logger.error(f"✗ {error_msg}")
                        try:
                            screenshot_path = f'/tmp/zhihu_no_publish_btn_{int(time.time())}.png'
                            self.page.get_screenshot(path=screenshot_path)
                            logger.info(f"已保存错误截图: {screenshot_path}")
                        except:
                            pass
                        return {'success': False, 'message': error_msg}

                    # 第二步：检查按钮状态
                    logger.info("步骤2/5: 检查发布按钮状态...")
                    try:
                        # 滚动到按钮
                        publish_btn.run_js('this.scrollIntoView({behavior: "smooth", block: "center"})')
                        time.sleep(1)

                        # 方法1: 检查disabled属性
                        is_disabled = publish_btn.attr('disabled')

                        # 方法2: 鼠标悬浮检测真实可点击状态
                        try:
                            # 移动鼠标到按钮上
                            self.page.actions.move_to(publish_btn)
                            time.sleep(0.5)

                            # 检查按钮样式
                            cursor_style = publish_btn.run_js('return window.getComputedStyle(this).cursor')
                            pointer_events = publish_btn.run_js('return window.getComputedStyle(this).pointerEvents')

                            logger.info(f"按钮状态: disabled={is_disabled}, cursor={cursor_style}, pointer-events={pointer_events}")

                            # 判断是否真正可点击
                            is_clickable = (
                                not is_disabled and
                                cursor_style == 'pointer' and
                                pointer_events != 'none'
                            )

                            if not is_clickable:
                                error_msg = f"发布按钮不可点击（disabled={is_disabled}, cursor={cursor_style}）"
                                logger.error(f"✗ {error_msg}")
                                try:
                                    screenshot_path = f'/tmp/zhihu_btn_not_clickable_{int(time.time())}.png'
                                    self.page.get_screenshot(path=screenshot_path)
                                    logger.info(f"已保存截图: {screenshot_path}")
                                except:
                                    pass
                                return {'success': False, 'message': error_msg}

                            logger.info("✓ 发布按钮可点击（悬浮检测通过）")

                        except Exception as hover_err:
                            logger.warning(f"鼠标悬浮检测失败: {hover_err}，使用disabled属性判断")
                            if is_disabled:
                                error_msg = "发布按钮被禁用"
                                logger.error(f"✗ {error_msg}")
                                return {'success': False, 'message': error_msg}

                            logger.info("✓ 发布按钮未禁用")

                    except Exception as e:
                        logger.warning(f"检查按钮状态时出错: {e}")

                    # 第三步：点击发布按钮
                    logger.info("步骤3/5: 点击发布按钮...")
                    publish_btn.click()
                    logger.info("✓ 已点击发布按钮，等待页面响应...")
                    time.sleep(8)  # 延长等待时间从5秒到8秒

                    # 第四步：处理发布设置弹窗（重要！）
                    logger.info("步骤4/5: 检查发布设置弹窗...")

                    # 知乎可能会弹出"发布设置"对话框，需要再次点击"发布文章"
                    modal_found = False
                    modal_publish_selectors = [
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
                                logger.info(f"✓ 找到弹窗中的发布按钮: '{modal_text}'")

                                # 确保这是发布设置对话框中的按钮
                                if '发布' in modal_text:
                                    modal_btn.click()
                                    logger.info("✓ 已点击弹窗中的发布按钮")
                                    modal_found = True
                                    time.sleep(8)  # 延长等待时间从5秒到8秒
                                    break
                        except:
                            continue

                    if not modal_found:
                        logger.info("未检测到发布设置弹窗")

                    # 第五步：验证发布结果(带重试机制)
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

                        # 截图
                        try:
                            screenshot_path = f'/tmp/zhihu_still_editing_{int(time.time())}.png'
                            self.page.get_screenshot(path=screenshot_path)
                            logger.info(f"已保存编辑状态截图: {screenshot_path}")
                        except:
                            pass

                        return {
                            'success': False,
                            'message': error_msg,
                            'url': current_url,
                            'detail': f'经过{max_retries}次验证,点击发布后仍在编辑页面'
                        }

                    # 如果有任何成功指标且URL不包含/edit，认为发布成功
                    if success_indicators:
                        logger.info(f"✓✓ 文章发布成功!")

                        # 提取文章ID
                        article_id = None
                        if '/p/' in current_url:
                            article_id = current_url.split('/p/')[-1].split('?')[0].split('/')[0].split('#')[0]
                        elif '/zhuanlan/' in current_url:
                            parts = current_url.split('/zhuanlan/')[-1].split('/')
                            if len(parts) > 0:
                                article_id = parts[0]

                        # 最终截图
                        try:
                            screenshot_path = f'/tmp/zhihu_publish_success_{int(time.time())}.png'
                            self.page.get_screenshot(path=screenshot_path)
                            logger.info(f"已保存成功截图: {screenshot_path}")
                        except:
                            pass

                        return {
                            'success': True,
                            'message': '文章发布成功',
                            'type': 'published',
                            'url': current_url,
                            'article_id': article_id,
                            'indicators': success_indicators
                        }
                    else:
                        # 没有任何成功指标
                        error_msg = "无法确认发布状态，未找到成功指标"
                        logger.warning(f"⚠ {error_msg}")

                        try:
                            screenshot_path = f'/tmp/zhihu_publish_unclear_{int(time.time())}.png'
                            self.page.get_screenshot(path=screenshot_path)
                            logger.info(f"已保存状态截图: {screenshot_path}")
                        except:
                            pass

                        return {
                            'success': False,
                            'message': error_msg,
                            'url': current_url
                        }

                except Exception as e:
                    error_msg = f'发布过程异常: {str(e)}'
                    logger.error(f"✗ {error_msg}", exc_info=True)

                    try:
                        screenshot_path = f'/tmp/zhihu_publish_exception_{int(time.time())}.png'
                        self.page.get_screenshot(path=screenshot_path)
                        logger.info(f"已保存异常截图: {screenshot_path}")
                    except:
                        pass

                    return {'success': False, 'message': error_msg}

        except Exception as e:
            logger.error(f"✗ 创建文章异常: {e}", exc_info=True)
            return {'success': False, 'message': str(e)}

    def create_answer(self, question_url, content):
        """回答问题

        Args:
            question_url: 问题链接
            content: 回答内容
        """
        try:
            if not self.is_logged_in:
                return {'success': False, 'message': '未登录'}

            logger.info(f"正在访问问题: {question_url}")
            self.page.get(question_url)
            time.sleep(3)

            # 点击写回答按钮
            logger.info("查找写回答按钮...")
            write_answer_btn = self.page.ele('text:写回答', timeout=5)
            if write_answer_btn:
                write_answer_btn.click()
                time.sleep(2)
                logger.info("✓ 已点击写回答")
            else:
                logger.warning("未找到写回答按钮")

            # 输入回答内容
            logger.info("正在输入回答...")
            editor = self.page.ele('css:[contenteditable="true"]', timeout=5)
            if editor:
                editor.click()
                time.sleep(0.5)
                editor.input(content)
                logger.info("✓ 回答内容已输入")
            else:
                return {'success': False, 'message': '未找到编辑器'}

            # 发布回答
            logger.info("正在发布回答...")
            publish_btn = self.page.ele('text:发布回答', timeout=3)
            if publish_btn:
                publish_btn.click()
                time.sleep(3)
                logger.info("✓✓ 回答发布成功")
                return {'success': True, 'message': '回答发布成功'}
            else:
                return {'success': False, 'message': '未找到发布按钮'}

        except Exception as e:
            logger.error(f"✗ 回答发布失败: {e}")
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


# 便捷函数
def post_article_to_zhihu(username, title, content, password=None, topics=None, draft=False):
    """
    一键发布文章到知乎

    Args:
        username: 知乎账号(用于加载Cookie)
        title: 文章标题
        content: 文章内容
        topics: 话题列表
        draft: 是否保存为草稿

    Returns:
        {'success': True/False, 'message': '...', 'url': '...'}
    """
    poster = ZhihuAutoPost()

    try:
        # 初始化浏览器
        if not poster.init_browser():
            return {'success': False, 'message': '浏览器初始化失败'}

        # 加载Cookie登录
        if not poster.load_cookies(username):
            return {'success': False, 'message': 'Cookie加载失败或未登录'}

        # 发布文章
        result = poster.create_article(title, content, topics, draft)

        return result

    finally:
        poster.close()
