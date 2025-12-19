#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI测试辅助工具
提供Selenium WebDriver的辅助功能和通用方法
"""
import time
import os
from typing import Optional, List, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class UIHelper:
    """UI测试辅助类"""

    def __init__(self, driver: webdriver.Chrome):
        """
        初始化UI辅助类

        Args:
            driver: WebDriver实例
        """
        self.driver = driver
        self.default_timeout = 10

    def wait_for_element(self, locator: tuple, timeout: Optional[int] = None) -> WebElement:
        """
        等待元素出现

        Args:
            locator: 元素定位器 (By.ID, "element_id")
            timeout: 超时时间

        Returns:
            WebElement对象
        """
        wait = WebDriverWait(self.driver, timeout or self.default_timeout)
        return wait.until(EC.presence_of_element_located(locator))

    def wait_for_element_visible(self, locator: tuple, timeout: Optional[int] = None) -> WebElement:
        """
        等待元素可见

        Args:
            locator: 元素定位器
            timeout: 超时时间

        Returns:
            WebElement对象
        """
        wait = WebDriverWait(self.driver, timeout or self.default_timeout)
        return wait.until(EC.visibility_of_element_located(locator))

    def wait_for_element_clickable(self, locator: tuple, timeout: Optional[int] = None) -> WebElement:
        """
        等待元素可点击

        Args:
            locator: 元素定位器
            timeout: 超时时间

        Returns:
            WebElement对象
        """
        wait = WebDriverWait(self.driver, timeout or self.default_timeout)
        return wait.until(EC.element_to_be_clickable(locator))

    def wait_for_text_present(self, text: str, timeout: Optional[int] = None) -> bool:
        """
        等待文本出现在页面中

        Args:
            text: 要等待的文本
            timeout: 超时时间

        Returns:
            文本是否出现
        """
        wait = WebDriverWait(self.driver, timeout or self.default_timeout)
        try:
            wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), text))
            return True
        except TimeoutException:
            return False

    def click_element(self, locator: tuple, timeout: Optional[int] = None):
        """
        点击元素

        Args:
            locator: 元素定位器
            timeout: 超时时间
        """
        element = self.wait_for_element_clickable(locator, timeout)
        element.click()

    def type_text(self, locator: tuple, text: str, clear_first: bool = True, timeout: Optional[int] = None):
        """
        在输入框中输入文本

        Args:
            locator: 元素定位器
            text: 要输入的文本
            clear_first: 是否先清空输入框
            timeout: 超时时间
        """
        element = self.wait_for_element_visible(locator, timeout)

        if clear_first:
            element.clear()
        element.send_keys(text)

    def select_dropdown_by_text(self, locator: tuple, text: str, timeout: Optional[int] = None):
        """
        通过文本选择下拉框选项

        Args:
            locator: 元素定位器
            text: 选项文本
            timeout: 超时时间
        """
        element = self.wait_for_element_visible(locator, timeout)
        select = Select(element)
        select.select_by_visible_text(text)

    def select_dropdown_by_index(self, locator: tuple, index: int, timeout: Optional[int] = None):
        """
        通过索引选择下拉框选项

        Args:
            locator: 元素定位器
            index: 选项索引
            timeout: 超时时间
        """
        element = self.wait_for_element_visible(locator, timeout)
        select = Select(element)
        select.select_by_index(index)

    def get_element_text(self, locator: tuple, timeout: Optional[int] = None) -> str:
        """
        获取元素文本

        Args:
            locator: 元素定位器
            timeout: 超时时间

        Returns:
            元素文本
        """
        element = self.wait_for_element_visible(locator, timeout)
        return element.text.strip()

    def get_element_attribute(self, locator: tuple, attribute: str, timeout: Optional[int] = None) -> str:
        """
        获取元素属性值

        Args:
            locator: 元素定位器
            attribute: 属性名
            timeout: 超时时间

        Returns:
            属性值
        """
        element = self.wait_for_element_visible(locator, timeout)
        return element.get_attribute(attribute)

    def is_element_present(self, locator: tuple, timeout: int = 2) -> bool:
        """
        检查元素是否存在

        Args:
            locator: 元素定位器
            timeout: 超时时间

        Returns:
            元素是否存在
        """
        try:
            WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(locator))
            return True
        except TimeoutException:
            return False

    def is_element_visible(self, locator: tuple, timeout: int = 2) -> bool:
        """
        检查元素是否可见

        Args:
            locator: 元素定位器
            timeout: 超时时间

        Returns:
            元素是否可见
        """
        try:
            WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located(locator))
            return True
        except TimeoutException:
            return False

    def scroll_to_element(self, locator: tuple, timeout: Optional[int] = None):
        """
        滚动到元素位置

        Args:
            locator: 元素定位器
            timeout: 超时时间
        """
        element = self.wait_for_element(locator, timeout)
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)

    def hover_over_element(self, locator: tuple, timeout: Optional[int] = None):
        """
        鼠标悬停在元素上

        Args:
            locator: 元素定位器
            timeout: 超时时间
        """
        element = self.wait_for_element_visible(locator, timeout)
        ActionChains(self.driver).move_to_element(element).perform()

    def double_click(self, locator: tuple, timeout: Optional[int] = None):
        """
        双击元素

        Args:
            locator: 元素定位器
            timeout: 超时时间
        """
        element = self.wait_for_element_visible(locator, timeout)
        ActionChains(self.driver).double_click(element).perform()

    def right_click(self, locator: tuple, timeout: Optional[int] = None):
        """
        右键点击元素

        Args:
            locator: 元素定位器
            timeout: 超时时间
        """
        element = self.wait_for_element_visible(locator, timeout)
        ActionChains(self.driver).context_click(element).perform()

    def switch_to_frame(self, frame_locator: tuple):
        """
        切换到iframe

        Args:
            frame_locator: iframe定位器
        """
        frame = self.wait_for_element_present(frame_locator)
        self.driver.switch_to.frame(frame)

    def switch_to_default_content(self):
        """切换回默认内容"""
        self.driver.switch_to.default_content()

    def handle_alert(self, accept: bool = True):
        """
        处理弹窗

        Args:
            accept: 是否接受弹窗（True为接受，False为取消）
        """
        try:
            alert = WebDriverWait(self.driver, 5).until(EC.alert_is_present())
            if accept:
                alert.accept()
            else:
                alert.dismiss()
        except TimeoutException:
            pass

    def take_screenshot(self, filename: str) -> bool:
        """
        截屏

        Args:
            filename: 文件名

        Returns:
            截屏是否成功
        """
        try:
            self.driver.save_screenshot(filename)
            return True
        except Exception as e:
            print(f"截屏失败: {e}")
            return False

    def get_page_title(self) -> str:
        """获取页面标题"""
        return self.driver.title

    def get_current_url(self) -> str:
        """获取当前URL"""
        return self.driver.current_url

    def refresh_page(self):
        """刷新页面"""
        self.driver.refresh()

    def go_back(self):
        """后退"""
        self.driver.back()

    def go_forward(self):
        """前进"""
        self.driver.forward()

    def execute_javascript(self, script: str, *args):
        """
        执行JavaScript

        Args:
            script: JavaScript代码
            *args: 参数

        Returns:
            执行结果
        """
        return self.driver.execute_script(script, *args)

    def wait_for_ajax_complete(self, timeout: int = 30):
        """
        等待AJAX请求完成

        Args:
            timeout: 超时时间
        """
        def ajax_complete(driver):
            return driver.execute_script("return jQuery.active == 0") if driver.execute_script("return typeof jQuery !== 'undefined'") else True

        WebDriverWait(self.driver, timeout).until(ajax_complete)

    def wait_for_page_load(self, timeout: int = 30):
        """
        等待页面加载完成

        Args:
            timeout: 超时时间
        """
        WebDriverWait(self.driver, timeout).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )

    def find_elements_by_text(self, text: str, partial_match: bool = False) -> List[WebElement]:
        """
        通过文本查找元素

        Args:
            text: 文本内容
            partial_match: 是否部分匹配

        Returns:
            元素列表
        """
        if partial_match:
            xpath = f"//*[contains(text(), '{text}')]"
        else:
            xpath = f"//*[text()='{text}']"

        return self.driver.find_elements(By.XPATH, xpath)

    def get_table_data(self, table_locator: tuple) -> List[Dict[str, str]]:
        """
        获取表格数据

        Args:
            table_locator: 表格定位器

        Returns:
            表格数据列表
        """
        table = self.wait_for_element(table_locator)
        rows = table.find_elements(By.TAG_NAME, "tr")

        if not rows:
            return []

        # 获取表头
        headers = [th.text.strip() for th in rows[0].find_elements(By.TAG_NAME, "th")]
        if not headers:
            headers = [td.text.strip() for td in rows[0].find_elements(By.TAG_NAME, "td")]

        table_data = []

        # 获取数据行
        for row in rows[1:]:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) == len(headers):
                row_data = {headers[i]: cells[i].text.strip() for i in range(len(headers))}
                table_data.append(row_data)

        return table_data

    def wait_for_element_disappear(self, locator: tuple, timeout: Optional[int] = None) -> bool:
        """
        等待元素消失

        Args:
            locator: 元素定位器
            timeout: 超时时间

        Returns:
            元素是否消失
        """
        wait = WebDriverWait(self.driver, timeout or self.default_timeout)
        try:
            wait.until_not(EC.presence_of_element_located(locator))
            return True
        except TimeoutException:
            return False

    def is_element_enabled(self, locator: tuple, timeout: int = 2) -> bool:
        """
        检查元素是否可用

        Args:
            locator: 元素定位器
            timeout: 超时时间

        Returns:
            元素是否可用
        """
        try:
            element = self.wait_for_element_present(locator, timeout)
            return element.is_enabled()
        except TimeoutException:
            return False

    def get_css_property(self, locator: tuple, property_name: str, timeout: Optional[int] = None) -> str:
        """
        获取元素CSS属性值

        Args:
            locator: 元素定位器
            property_name: CSS属性名
            timeout: 超时时间

        Returns:
            CSS属性值
        """
        element = self.wait_for_element_visible(locator, timeout)
        return element.value_of_css_property(property_name)


def get_webdriver_config() -> Dict[str, Any]:
    """
    获取WebDriver配置

    Returns:
        配置字典
    """
    from .test_helpers import get_test_config

    test_config = get_test_config()

    return {
        "base_url": test_config.get('base_url', 'http://localhost:3001'),
        "headless": os.getenv('TEST_HEADLESS', 'true').lower() == 'true',
        "implicit_wait": int(os.getenv('TEST_IMPLICIT_WAIT', '10')),
        "page_load_timeout": int(os.getenv('TEST_PAGE_LOAD_TIMEOUT', '30')),
        "webdriver_path": os.getenv('TEST_WEBDRIVER_PATH'),
        "download_dir": str(test_config.get('download_dir', './downloads')),
        "screenshot_dir": str(test_config.get('screenshot_dir', './screenshots'))
    }


def authenticate_ui_user(driver: webdriver.Chrome, base_url: str):
    """
    UI方式用户认证

    Args:
        driver: WebDriver实例
        base_url: 基础URL
    """
    from .test_helpers import get_test_credentials

    credentials = get_test_credentials()

    try:
        # 访问登录页面
        driver.get(f"{base_url}/login")

        ui_helper = UIHelper(driver)

        # 输入用户名
        username_locators = [
            (By.NAME, "username"),
            (By.NAME, "email"),
            (By.ID, "username"),
            (By.XPATH, "//input[contains(@placeholder,'用户名') or contains(@placeholder,'username')]")
        ]

        username_element = None
        for locator in username_locators:
            if ui_helper.is_element_present(locator, 2):
                username_element = ui_helper.wait_for_element_visible(locator)
                break

        if username_element:
            username_element.clear()
            username_element.send_keys(credentials['username'])

        # 输入密码
        password_element = driver.find_element(By.XPATH, "//input[@type='password']")
        password_element.clear()
        password_element.send_keys(credentials['password'])

        # 点击登录按钮
        submit_locators = [
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "//button[contains(text(), '登录') or contains(text(), 'Login')]"),
            (By.XPATH, "//input[@type='submit']")
        ]

        for locator in submit_locators:
            if ui_helper.is_element_present(locator, 2):
                ui_helper.click_element(locator)
                break

        # 等待登录完成
        time.sleep(3)

        print("✓ UI用户认证完成")

    except Exception as e:
        print(f"⚠️ UI用户认证失败: {e}")


def setup_test_environment(driver: webdriver.Chrome):
    """
    设置测试环境

    Args:
        driver: WebDriver实例
    """
    try:
        # 设置窗口大小
        driver.set_window_size(1920, 1080)

        # 设置隐式等待
        driver.implicitly_wait(10)

        # 设置页面加载超时
        driver.set_page_load_timeout(30)

        print("✓ 测试环境设置完成")

    except Exception as e:
        print(f"⚠️ 测试环境设置失败: {e}")


def cleanup_test_environment(driver: webdriver.Chrome):
    """
    清理测试环境

    Args:
        driver: WebDriver实例
    """
    try:
        # 清除cookies
        driver.delete_all_cookies()

        # 清除本地存储
        driver.execute_script("window.localStorage.clear();")
        driver.execute_script("window.sessionStorage.clear();")

        print("✓ 测试环境清理完成")

    except Exception as e:
        print(f"⚠️ 测试环境清理失败: {e}")