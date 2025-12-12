#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSDN平台发布器

实现CSDN平台的自动化登录和文章发布功能
支持密码登录、滑动验证码处理、Markdown编辑器
"""
import time
import os
from typing import Tuple, Optional
from DrissionPage import ChromiumPage, ChromiumOptions
from .base_publisher import (
    BasePlatformPublisher,
    LoginFailedException,
    PublishFailedException,
    NetworkException
)
from .config import get_platform_config


class CSDNPublisher(BasePlatformPublisher):
    """
    CSDN平台发布器

    支持功能:
    - 账号密码登录
    - 滑动验证码自动处理
    - Markdown文章发布
    - 分类、标签设置
    - 文章类型选择(原创/转载/翻译)
    """

    def __init__(self):
        """初始化CSDN发布器"""
        super().__init__('csdn')

        # 获取平台配置
        self.config = get_platform_config('csdn')
        self.login_url = self.config['login_url']
        self.write_url = self.config['write_url']
        self.timeout = self.config['timeout']

        # 初始化浏览器
        self._init_browser()

        self.logger.info('CSDN发布器初始化完成')

    def _init_browser(self):
        """初始化浏览器实例"""
        try:
            co = ChromiumOptions()
            co.set_argument('--disable-blink-features=AutomationControlled')
            co.set_argument('--start-maximized')
            co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

            self.driver = ChromiumPage(addr_or_opts=co)
            self.logger.info('浏览器初始化成功')
        except Exception as e:
            self.logger.error(f'浏览器初始化失败: {e}')
            raise

    def login(self, username: str, password: str) -> Tuple[bool, str]:
        """
        CSDN账号密码登录

        Args:
            username: 用户名/手机号/邮箱
            password: 密码

        Returns:
            (是否成功, 消息)
        """
        try:
            self.logger.info(f'开始登录CSDN账号: {username}')

            # 1. 访问登录页面
            self.driver.get(self.login_url)
            time.sleep(2)

            # 2. 切换到密码登录tab
            try:
                password_tab = self.driver.ele('text:密码登录', timeout=5)
                if password_tab:
                    password_tab.click()
                    time.sleep(1)
            except Exception:
                self.logger.warning('未找到密码登录切换按钮，尝试直接输入')

            # 3. 输入账号密码
            try:
                username_input = self.driver.ele('#username', timeout=5)
                if not username_input:
                    username_input = self.driver.ele('@@placeholder=手机号/邮箱', timeout=5)

                password_input = self.driver.ele('#password', timeout=5)
                if not password_input:
                    password_input = self.driver.ele('@@type=password', timeout=5)

                if not username_input or not password_input:
                    raise LoginFailedException('未找到用户名或密码输入框')

                username_input.input(username)
                time.sleep(0.5)
                password_input.input(password)
                time.sleep(0.5)

                self.logger.info('账号密码已输入')
            except Exception as e:
                raise LoginFailedException(f'输入账号密码失败: {e}')

            # 4. 处理滑动验证码
            try:
                self.logger.info('检查是否有滑动验证码...')
                success, msg = self._handle_slider_captcha()
                if not success:
                    self.logger.warning(f'滑动验证码处理失败: {msg}')
                else:
                    self.logger.info('滑动验证码处理成功')
            except Exception as e:
                self.logger.warning(f'滑动验证码处理异常: {e}')

            # 5. 点击登录按钮
            try:
                login_btn = self.driver.ele('text:登 录', timeout=5)
                if not login_btn:
                    login_btn = self.driver.ele('.btn-login', timeout=5)

                if login_btn:
                    login_btn.click()
                    self.logger.info('已点击登录按钮')
                else:
                    raise LoginFailedException('未找到登录按钮')
            except Exception as e:
                raise LoginFailedException(f'点击登录按钮失败: {e}')

            # 6. 等待登录完成
            time.sleep(3)

            # 7. 验证登录状态
            if self.is_logged_in():
                # 保存Cookie
                cookies = self.driver.cookies(as_dict=False)
                self.save_cookies(cookies, username)

                self.logger.info(f'CSDN登录成功: {username}')
                return True, '登录成功'
            else:
                raise LoginFailedException('登录失败，请检查账号密码或验证码')

        except LoginFailedException as e:
            self.logger.error(f'登录失败: {e}')
            return False, str(e)
        except Exception as e:
            self.logger.error(f'登录异常: {e}')
            return False, f'登录异常: {e}'

    def _handle_slider_captcha(self) -> Tuple[bool, str]:
        """
        处理滑动验证码

        Returns:
            (是否成功, 消息)
        """
        try:
            # 查找滑块元素
            slider = self.driver.ele('.nc_iconfont btn_slide', timeout=3)
            if not slider:
                return True, '未检测到滑动验证码'

            self.logger.info('检测到滑动验证码，开始处理...')

            # 获取滑块轨道长度
            track = self.driver.ele('.nc-lang-cnt', timeout=2)
            if not track:
                return False, '未找到滑动轨道'

            # 计算需要滑动的距离（通常是轨道长度 - 滑块宽度）
            track_width = track.rect.size[0]
            slider_width = slider.rect.size[0]
            distance = track_width - slider_width - 10  # 留10px余量

            self.logger.info(f'滑动距离: {distance}px')

            # 模拟人工滑动（分段移动，速度不均匀）
            # 1. 按下滑块
            slider.click()
            time.sleep(0.1)

            # 2. 分段滑动
            moved = 0
            while moved < distance:
                # 计算本次移动距离（模拟加速-减速过程）
                if moved < distance * 0.3:
                    # 加速阶段
                    step = min(20, distance - moved)
                elif moved > distance * 0.8:
                    # 减速阶段
                    step = min(5, distance - moved)
                else:
                    # 匀速阶段
                    step = min(15, distance - moved)

                # 执行移动
                slider.drag(offset_x=step, offset_y=0, duration=0.05)
                moved += step
                time.sleep(0.02)

            # 3. 释放滑块
            time.sleep(0.2)

            # 4. 检查验证结果
            time.sleep(1)
            success_ele = self.driver.ele('.nc_iconfont nc-lang-cnt nc-success', timeout=2)
            if success_ele or not self.driver.ele('.nc_iconfont btn_slide', timeout=1):
                self.logger.info('滑动验证码验证成功')
                return True, '滑动验证成功'
            else:
                self.logger.warning('滑动验证码验证失败')
                return False, '滑动验证失败，可能需要手动处理'

        except Exception as e:
            self.logger.error(f'处理滑动验证码异常: {e}')
            return False, f'验证码处理异常: {e}'

    def login_with_qrcode(self) -> Tuple[bool, str, Optional[str]]:
        """
        CSDN不支持二维码登录

        Returns:
            (False, '不支持', None)
        """
        self.logger.warning('CSDN不支持二维码登录')
        return False, 'CSDN平台不支持二维码登录，请使用账号密码登录', None

    def is_logged_in(self) -> bool:
        """
        检查是否已登录

        Returns:
            是否已登录
        """
        try:
            # 访问写作页面，检查是否跳转到登录页
            current_url = self.driver.url

            # 如果当前不在CSDN域名下，先访问首页
            if 'csdn.net' not in current_url:
                self.driver.get('https://www.csdn.net')
                time.sleep(1)

            # 检查是否有用户头像或用户菜单
            user_avatar = self.driver.ele('.toolbar-user-avatar', timeout=2)
            user_menu = self.driver.ele('.toolbar-menu-item user', timeout=2)

            if user_avatar or user_menu:
                self.logger.info('检测到用户已登录')
                return True

            # 检查Cookie中是否有UserToken
            cookies = self.driver.cookies(as_dict=True)
            if 'UserToken' in cookies or 'uuid_tt_dd' in cookies:
                self.logger.info('检测到登录Cookie')
                return True

            self.logger.info('用户未登录')
            return False

        except Exception as e:
            self.logger.error(f'检查登录状态异常: {e}')
            return False

    def publish_article(
        self,
        title: str,
        content: str,
        **kwargs
    ) -> Tuple[bool, str, Optional[str]]:
        """
        发布文章到CSDN

        Args:
            title: 文章标题
            content: 文章内容（Markdown格式）
            **kwargs: 其他参数
                - category: 文章分类（默认: '其他'）
                - tags: 标签列表（最多3个）
                - article_type: 文章类型（'original'/'reprint'/'translate'，默认: 'original'）
                - cover_image: 封面图片路径（可选）

        Returns:
            (是否成功, 消息, 文章URL)
        """
        try:
            # 检查登录状态
            if not self.is_logged_in():
                raise PublishFailedException('未登录，请先登录')

            self.logger.info(f'开始发布文章: {title}')

            # 1. 打开写作页面
            self.driver.get(self.write_url)
            time.sleep(3)

            # 2. 切换到Markdown编辑器
            try:
                markdown_btn = self.driver.ele('text:Markdown编辑器', timeout=3)
                if markdown_btn:
                    markdown_btn.click()
                    time.sleep(1)
            except Exception:
                self.logger.info('已在Markdown编辑器模式')

            # 3. 输入标题
            try:
                title_input = self.driver.ele('#txtTitle', timeout=5)
                if not title_input:
                    title_input = self.driver.ele('@@placeholder=请输入文章标题', timeout=5)

                if title_input:
                    title_input.clear()
                    title_input.input(title)
                    time.sleep(0.5)
                    self.logger.info('标题已输入')
                else:
                    raise PublishFailedException('未找到标题输入框')
            except Exception as e:
                raise PublishFailedException(f'输入标题失败: {e}')

            # 4. 输入内容
            try:
                # CSDN使用CodeMirror编辑器
                content_area = self.driver.ele('.CodeMirror-code', timeout=5)
                if not content_area:
                    content_area = self.driver.ele('#content', timeout=5)

                if content_area:
                    # 点击编辑区域获取焦点
                    content_area.click()
                    time.sleep(0.5)

                    # 使用JavaScript设置内容（更可靠）
                    js_code = f"""
                    var editor = document.querySelector('.CodeMirror').CodeMirror;
                    editor.setValue({repr(content)});
                    """
                    self.driver.run_js(js_code)
                    time.sleep(1)

                    self.logger.info('文章内容已输入')
                else:
                    raise PublishFailedException('未找到内容编辑区域')
            except Exception as e:
                raise PublishFailedException(f'输入内容失败: {e}')

            # 5. 点击发布按钮
            try:
                publish_btn = self.driver.ele('text:发布文章', timeout=5)
                if not publish_btn:
                    publish_btn = self.driver.ele('.btn-publish', timeout=5)

                if publish_btn:
                    publish_btn.click()
                    time.sleep(2)
                    self.logger.info('已点击发布按钮')
                else:
                    raise PublishFailedException('未找到发布按钮')
            except Exception as e:
                raise PublishFailedException(f'点击发布按钮失败: {e}')

            # 6. 设置文章属性（分类、标签、类型）
            try:
                # 设置文章类型（原创/转载/翻译）
                article_type = kwargs.get('article_type', 'original')
                self._set_article_type(article_type)

                # 设置分类
                category = kwargs.get('category', '其他')
                self._set_category(category)

                # 设置标签
                tags = kwargs.get('tags', [])
                if tags:
                    self._add_tags(tags)

                time.sleep(1)
            except Exception as e:
                self.logger.warning(f'设置文章属性失败: {e}，继续发布')

            # 7. 确认发布
            try:
                confirm_btn = self.driver.ele('text:确定', timeout=5)
                if not confirm_btn:
                    confirm_btn = self.driver.ele('.btn-confirm', timeout=5)

                if confirm_btn:
                    confirm_btn.click()
                    time.sleep(3)
                    self.logger.info('已确认发布')
            except Exception as e:
                self.logger.warning(f'确认发布失败: {e}')

            # 8. 获取文章URL
            article_url = self.get_article_url_after_publish()

            if article_url:
                self.logger.info(f'文章发布成功: {article_url}')
                return True, '发布成功', article_url
            else:
                self.logger.warning('文章可能已发布，但未获取到URL')
                return True, '发布成功（未获取到URL）', None

        except PublishFailedException as e:
            self.logger.error(f'发布失败: {e}')
            return False, str(e), None
        except Exception as e:
            self.logger.error(f'发布异常: {e}')
            return False, f'发布异常: {e}', None

    def _set_article_type(self, article_type: str):
        """
        设置文章类型

        Args:
            article_type: 'original'(原创) / 'reprint'(转载) / 'translate'(翻译)
        """
        try:
            type_mapping = {
                'original': '原创',
                'reprint': '转载',
                'translate': '翻译'
            }

            type_text = type_mapping.get(article_type, '原创')
            type_btn = self.driver.ele(f'text:{type_text}', timeout=3)

            if type_btn:
                type_btn.click()
                time.sleep(0.5)
                self.logger.info(f'已设置文章类型: {type_text}')
        except Exception as e:
            self.logger.warning(f'设置文章类型失败: {e}')

    def _set_category(self, category: str):
        """
        设置文章分类

        Args:
            category: 分类名称
        """
        try:
            # 点击分类下拉框
            category_select = self.driver.ele('.select-category', timeout=3)
            if not category_select:
                category_select = self.driver.ele('text:请选择分类', timeout=3)

            if category_select:
                category_select.click()
                time.sleep(0.5)

                # 选择分类选项
                category_option = self.driver.ele(f'text:{category}', timeout=3)
                if category_option:
                    category_option.click()
                    time.sleep(0.5)
                    self.logger.info(f'已设置分类: {category}')
                else:
                    self.logger.warning(f'未找到分类: {category}')
        except Exception as e:
            self.logger.warning(f'设置分类失败: {e}')

    def _add_tags(self, tags: list):
        """
        添加文章标签

        Args:
            tags: 标签列表（最多3个）
        """
        try:
            # CSDN最多3个标签
            tags = tags[:3]

            for tag in tags:
                tag_input = self.driver.ele('.tag-input', timeout=3)
                if not tag_input:
                    tag_input = self.driver.ele('@@placeholder=请输入标签', timeout=3)

                if tag_input:
                    tag_input.input(tag)
                    time.sleep(0.3)

                    # 按Enter确认
                    tag_input.input('\n')
                    time.sleep(0.3)

                    self.logger.info(f'已添加标签: {tag}')
        except Exception as e:
            self.logger.warning(f'添加标签失败: {e}')

    def get_article_url_after_publish(self) -> Optional[str]:
        """
        获取发布后的文章URL

        Returns:
            文章URL，如果获取失败返回None
        """
        try:
            time.sleep(2)

            # 方法1: 从当前URL获取
            current_url = self.driver.url
            if 'article/details' in current_url:
                self.logger.info(f'从当前URL获取: {current_url}')
                return current_url

            # 方法2: 从成功提示中获取
            success_link = self.driver.ele('.success-link', timeout=3)
            if success_link:
                article_url = success_link.attr('href')
                if article_url:
                    self.logger.info(f'从成功提示获取: {article_url}')
                    return article_url

            # 方法3: 等待页面跳转
            time.sleep(3)
            current_url = self.driver.url
            if 'article/details' in current_url:
                self.logger.info(f'等待跳转后获取: {current_url}')
                return current_url

            self.logger.warning('未能获取文章URL')
            return None

        except Exception as e:
            self.logger.error(f'获取文章URL失败: {e}')
            return None
