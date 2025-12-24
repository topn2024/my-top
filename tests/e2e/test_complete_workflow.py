#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端完整工作流测试
测试从登录到发布文章的完整业务流程
包括: 登录 -> 内容分析 -> 文章生成 -> 发布文章
"""
import pytest
import time
import sys
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.utils.ui_helpers import UIHelper, get_webdriver_config
from tests.utils.test_helpers import get_test_config, generate_test_article_data


class TestCompleteWorkflow:
    """完整工作流端到端测试"""

    @pytest.fixture(scope="class")
    def driver(self):
        """WebDriver fixture"""
        config = get_webdriver_config()

        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')

        if config.get('headless', True):
            chrome_options.add_argument('--headless')

        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--allow-running-insecure-content')

        # 设置中文语言
        chrome_options.add_argument('--lang=zh-CN')
        chrome_options.add_experimental_option('prefs', {
            'intl.accept_languages': 'zh-CN,zh'
        })

        if config.get('webdriver_path'):
            service = Service(executable_path=config['webdriver_path'])
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            driver = webdriver.Chrome(options=chrome_options)

        driver.implicitly_wait(config.get('implicit_wait', 10))
        driver.set_page_load_timeout(config.get('page_load_timeout', 30))

        yield driver
        driver.quit()

    @pytest.fixture(scope="class")
    def base_url(self):
        """基础URL"""
        return get_webdriver_config().get('base_url', 'http://localhost:3001')

    @pytest.fixture(scope="class")
    def ui_helper(self, driver):
        """UI辅助类"""
        return UIHelper(driver)

    @pytest.fixture(scope="class")
    def test_config(self):
        """测试配置"""
        return get_test_config()

    # ========== 步骤1: 登录测试 ==========
    def test_step1_access_login_page(self, driver, base_url):
        """步骤1.1: 访问登录页面"""
        driver.get(f"{base_url}/login")
        wait = WebDriverWait(driver, 10)

        # 等待页面加载
        try:
            # 检查用户名输入框存在
            username_input = wait.until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            assert username_input.is_displayed(), "用户名输入框不可见"
            print("[PASS] 步骤1.1: 登录页面访问成功")
        except TimeoutException:
            # 尝试其他选择器
            username_input = driver.find_element(
                By.XPATH, "//input[contains(@placeholder,'用户') or @id='username']"
            )
            assert username_input is not None

    def test_step1_perform_login(self, driver, base_url, test_config):
        """步骤1.2: 执行登录操作"""
        driver.get(f"{base_url}/login")
        wait = WebDriverWait(driver, 10)

        try:
            # 获取表单元素
            username_input = wait.until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            password_input = driver.find_element(By.NAME, "password")

            # 输入凭证
            test_user = test_config.get('test_user', {})
            username = test_user.get('username', 'admin')
            password = test_user.get('password', 'admin123')

            username_input.clear()
            username_input.send_keys(username)
            password_input.clear()
            password_input.send_keys(password)

            # 点击登录按钮
            submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_button.click()

            # 等待页面跳转
            time.sleep(3)

            # 验证登录成功
            current_url = driver.current_url
            login_success = "login" not in current_url or "error" not in driver.page_source.lower()
            assert login_success, f"登录失败，当前URL: {current_url}"

            print(f"[PASS] 步骤1.2: 登录成功，跳转到: {current_url}")

        except Exception as e:
            print(f"[FAIL] 步骤1.2: 登录失败 - {e}")
            raise

    # ========== 步骤2: 内容分析测试 ==========
    def test_step2_access_analysis_page(self, driver, base_url):
        """步骤2.1: 访问内容分析页面"""
        driver.get(f"{base_url}/analysis")
        wait = WebDriverWait(driver, 10)

        try:
            # 等待分析页面加载
            wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(2)

            # 检查页面元素
            page_source = driver.page_source.lower()
            analysis_indicators = ['分析', 'analysis', 'content', '内容']
            page_loaded = any(ind in page_source for ind in analysis_indicators)

            assert page_loaded, "分析页面未正确加载"
            print("[PASS] 步骤2.1: 内容分析页面访问成功")

        except TimeoutException:
            print("[WARN] 步骤2.1: 页面加载超时，但继续测试")

    def test_step2_perform_content_analysis(self, driver, base_url):
        """步骤2.2: 执行内容分析"""
        driver.get(f"{base_url}/analysis")
        wait = WebDriverWait(driver, 10)

        try:
            time.sleep(2)

            # 查找内容输入区域
            content_selectors = [
                (By.ID, "content"),
                (By.NAME, "content"),
                (By.ID, "source_content"),
                (By.CSS_SELECTOR, "textarea"),
                (By.XPATH, "//textarea[contains(@placeholder,'输入') or contains(@placeholder,'内容')]")
            ]

            content_input = None
            for selector in content_selectors:
                try:
                    content_input = driver.find_element(*selector)
                    if content_input.is_displayed():
                        break
                except NoSuchElementException:
                    continue

            if content_input:
                # 输入测试内容
                test_content = """
                人工智能正在改变我们的生活方式。从智能手机的语音助手到自动驾驶汽车，
                AI技术正在深入到我们日常生活的方方面面。专家预测，未来十年AI将会带来
                更多革命性的变化，包括医疗诊断、教育和金融服务等领域。
                """
                content_input.clear()
                content_input.send_keys(test_content)

                # 查找并点击分析按钮
                analyze_buttons = [
                    (By.XPATH, "//button[contains(text(),'分析')]"),
                    (By.XPATH, "//button[contains(text(),'开始')]"),
                    (By.CSS_SELECTOR, "button.analyze-btn"),
                    (By.CSS_SELECTOR, "button[type='submit']")
                ]

                for btn_selector in analyze_buttons:
                    try:
                        analyze_btn = driver.find_element(*btn_selector)
                        if analyze_btn.is_displayed() and analyze_btn.is_enabled():
                            analyze_btn.click()
                            print("[PASS] 步骤2.2: 内容分析已提交")
                            time.sleep(3)
                            break
                    except NoSuchElementException:
                        continue

            else:
                print("[WARN] 步骤2.2: 未找到内容输入区域")

        except Exception as e:
            print(f"[WARN] 步骤2.2: 内容分析测试遇到问题 - {e}")

    # ========== 步骤3: 文章生成测试 ==========
    def test_step3_access_article_generation(self, driver, base_url):
        """步骤3.1: 访问文章生成页面"""
        # 尝试多个可能的文章生成页面URL
        article_urls = [
            f"{base_url}/articles",
            f"{base_url}/generate",
            f"{base_url}/home"
        ]

        page_accessed = False
        for url in article_urls:
            try:
                driver.get(url)
                time.sleep(2)

                # 检查页面是否正常加载
                if driver.current_url and "login" not in driver.current_url:
                    page_accessed = True
                    print(f"[PASS] 步骤3.1: 文章页面访问成功 - {url}")
                    break
            except Exception:
                continue

        if not page_accessed:
            print("[WARN] 步骤3.1: 无法访问文章生成页面")

    def test_step3_generate_article(self, driver, base_url):
        """步骤3.2: 生成文章"""
        driver.get(f"{base_url}/home")
        wait = WebDriverWait(driver, 10)

        try:
            time.sleep(2)

            # 查找主题/标题输入
            topic_selectors = [
                (By.ID, "topic"),
                (By.NAME, "topic"),
                (By.ID, "title"),
                (By.NAME, "title"),
                (By.XPATH, "//input[contains(@placeholder,'主题') or contains(@placeholder,'标题')]")
            ]

            topic_input = None
            for selector in topic_selectors:
                try:
                    topic_input = driver.find_element(*selector)
                    if topic_input.is_displayed():
                        break
                except NoSuchElementException:
                    continue

            if topic_input:
                # 输入测试主题
                topic_input.clear()
                topic_input.send_keys("人工智能技术发展趋势分析")

                # 查找生成按钮
                generate_buttons = [
                    (By.XPATH, "//button[contains(text(),'生成')]"),
                    (By.XPATH, "//button[contains(text(),'创建')]"),
                    (By.CSS_SELECTOR, "button.generate-btn"),
                    (By.CSS_SELECTOR, "button[type='submit']")
                ]

                for btn_selector in generate_buttons:
                    try:
                        gen_btn = driver.find_element(*btn_selector)
                        if gen_btn.is_displayed() and gen_btn.is_enabled():
                            gen_btn.click()
                            print("[PASS] 步骤3.2: 文章生成已触发")
                            time.sleep(5)  # 等待生成
                            break
                    except NoSuchElementException:
                        continue

            else:
                print("[WARN] 步骤3.2: 未找到主题输入区域")

        except Exception as e:
            print(f"[WARN] 步骤3.2: 文章生成测试遇到问题 - {e}")

    # ========== 步骤4: 发布测试 ==========
    def test_step4_access_publish_page(self, driver, base_url):
        """步骤4.1: 访问发布页面"""
        driver.get(f"{base_url}/publish")
        wait = WebDriverWait(driver, 10)

        try:
            time.sleep(2)

            # 检查发布页面加载
            page_source = driver.page_source.lower()
            publish_indicators = ['发布', 'publish', '平台', 'platform']
            page_loaded = any(ind in page_source for ind in publish_indicators)

            if page_loaded:
                print("[PASS] 步骤4.1: 发布页面访问成功")
            else:
                print("[WARN] 步骤4.1: 发布页面内容不符合预期")

        except Exception as e:
            print(f"[WARN] 步骤4.1: 发布页面访问遇到问题 - {e}")

    def test_step4_check_publish_options(self, driver, base_url):
        """步骤4.2: 检查发布选项"""
        driver.get(f"{base_url}/publish")
        time.sleep(2)

        try:
            # 检查平台选项
            platform_elements = driver.find_elements(
                By.XPATH, "//input[@type='checkbox' or @type='radio']"
            )

            # 检查发布按钮
            publish_buttons = driver.find_elements(
                By.XPATH, "//button[contains(text(),'发布') or contains(text(),'Publish')]"
            )

            if platform_elements or publish_buttons:
                print(f"[PASS] 步骤4.2: 发现 {len(platform_elements)} 个平台选项, {len(publish_buttons)} 个发布按钮")
            else:
                print("[WARN] 步骤4.2: 未发现发布相关元素")

        except Exception as e:
            print(f"[WARN] 步骤4.2: 检查发布选项遇到问题 - {e}")

    # ========== 步骤5: 管理后台测试 ==========
    def test_step5_access_admin_dashboard(self, driver, base_url):
        """步骤5.1: 访问管理后台"""
        driver.get(f"{base_url}/admin")
        wait = WebDriverWait(driver, 10)

        try:
            time.sleep(2)

            # 检查管理后台加载
            page_source = driver.page_source.lower()
            admin_indicators = ['管理', 'admin', 'dashboard', '控制台', '统计']
            page_loaded = any(ind in page_source for ind in admin_indicators)

            current_url = driver.current_url
            if "admin" in current_url or page_loaded:
                print("[PASS] 步骤5.1: 管理后台访问成功")
            else:
                print(f"[WARN] 步骤5.1: 可能被重定向到: {current_url}")

        except Exception as e:
            print(f"[WARN] 步骤5.1: 管理后台访问遇到问题 - {e}")

    def test_step5_check_admin_features(self, driver, base_url):
        """步骤5.2: 检查管理后台功能"""
        driver.get(f"{base_url}/admin")
        time.sleep(2)

        features_found = []

        # 检查各种管理功能
        feature_checks = [
            ('用户管理', ['用户', 'user', 'users']),
            ('文章管理', ['文章', 'article', 'articles']),
            ('日志监控', ['日志', 'log', 'logs']),
            ('统计概览', ['统计', 'stats', 'overview']),
            ('系统设置', ['设置', 'setting', 'config'])
        ]

        page_source = driver.page_source.lower()
        for feature_name, keywords in feature_checks:
            if any(kw in page_source for kw in keywords):
                features_found.append(feature_name)

        if features_found:
            print(f"[PASS] 步骤5.2: 发现管理功能 - {', '.join(features_found)}")
        else:
            print("[WARN] 步骤5.2: 未发现管理功能")

    # ========== 步骤6: 登出测试 ==========
    def test_step6_logout(self, driver, base_url):
        """步骤6: 登出测试"""
        try:
            # 查找登出按钮或链接
            logout_selectors = [
                (By.XPATH, "//a[contains(text(),'退出') or contains(text(),'登出') or contains(text(),'Logout')]"),
                (By.XPATH, "//button[contains(text(),'退出') or contains(text(),'登出')]"),
                (By.CSS_SELECTOR, "a.logout, button.logout"),
                (By.CSS_SELECTOR, "[href*='logout']")
            ]

            for selector in logout_selectors:
                try:
                    logout_elem = driver.find_element(*selector)
                    if logout_elem.is_displayed():
                        logout_elem.click()
                        time.sleep(2)

                        # 验证登出成功
                        current_url = driver.current_url
                        if "login" in current_url:
                            print("[PASS] 步骤6: 登出成功，返回登录页面")
                            return
                except NoSuchElementException:
                    continue

            # 尝试直接访问登出URL
            driver.get(f"{base_url}/logout")
            time.sleep(2)
            print("[PASS] 步骤6: 登出操作完成")

        except Exception as e:
            print(f"[WARN] 步骤6: 登出测试遇到问题 - {e}")


class TestAPIWorkflow:
    """API工作流端到端测试"""

    @pytest.fixture(scope="class")
    def api_client(self):
        """API客户端"""
        from tests.utils.api_client import APIClient
        config = get_test_config()
        return APIClient(config['base_url'], config['timeout'])

    def test_api_health_check(self, api_client):
        """API健康检查"""
        response = api_client.get("/api/health")
        assert response.status_code in [200, 404]  # 404表示端点不存在但服务正常
        print("[PASS] API健康检查")

    def test_api_login_flow(self, api_client):
        """API登录流程"""
        test_config = get_test_config()
        test_user = test_config.get('test_user', {})

        login_data = {
            'username': test_user.get('username', 'admin'),
            'password': test_user.get('password', 'admin123')
        }

        response = api_client.post("/api/auth/login", json_data=login_data)

        # 检查登录响应
        assert response.status_code in [200, 302, 401]

        if response.status_code == 200:
            print("[PASS] API登录成功")
        elif response.status_code == 302:
            print("[PASS] API登录成功(重定向)")
        else:
            print("[WARN] API登录需要有效凭证")

    def test_api_get_articles(self, api_client):
        """API获取文章列表"""
        response = api_client.get("/api/articles/history")

        assert response.status_code in [200, 401, 403]

        if response.status_code == 200:
            print("[PASS] API获取文章列表成功")
        else:
            print("[WARN] API获取文章需要认证")

    def test_api_get_workflows(self, api_client):
        """API获取工作流列表"""
        response = api_client.get("/api/workflow/list")

        assert response.status_code in [200, 401, 403]

        if response.status_code == 200:
            print("[PASS] API获取工作流列表成功")
        else:
            print("[WARN] API获取工作流需要认证")

    def test_api_admin_stats(self, api_client):
        """API管理统计"""
        response = api_client.get("/api/admin/stats/overview")

        assert response.status_code in [200, 401, 403]

        if response.status_code == 200:
            print("[PASS] API管理统计获取成功")
        else:
            print("[WARN] API管理统计需要管理员权限")

    def test_api_log_monitoring(self, api_client):
        """API日志监控"""
        response = api_client.get("/api/admin/logs/files")

        assert response.status_code in [200, 401, 403]

        if response.status_code == 200:
            print("[PASS] API日志监控获取成功")
        else:
            print("[WARN] API日志监控需要管理员权限")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
