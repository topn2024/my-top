"""
WebDriver连接池管理
提供Selenium WebDriver的池化管理，支持并发访问
"""
import logging
import queue
import threading
import time
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException

logger = logging.getLogger(__name__)


class WebDriverPool:
    """Selenium WebDriver连接池"""

    def __init__(self, max_drivers=8, idle_timeout=300, driver_path=None):
        """
        初始化WebDriver池

        Args:
            max_drivers: 最大driver数量
            idle_timeout: 空闲超时时间(秒)
            driver_path: ChromeDriver路径
        """
        self.max_drivers = max_drivers
        self.idle_timeout = idle_timeout
        self.driver_path = driver_path or "/usr/bin/chromedriver"

        # 可用的driver队列
        self.available = queue.Queue()
        # 正在使用的driver集合
        self.in_use = set()
        # driver使用时间记录
        self.last_used = {}
        # 锁
        self.lock = threading.RLock()
        # 池是否关闭
        self._closed = False

        # 启动清理线程
        self._start_cleanup_thread()

        logger.info(f"WebDriver池初始化: max={max_drivers}, timeout={idle_timeout}s")

    def _create_driver(self) -> webdriver.Chrome:
        """创建新的WebDriver实例"""
        try:
            options = Options()
            # Headless模式
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            # 禁用图片加载以提高速度
            prefs = {"profile.managed_default_content_settings.images": 2}
            options.add_experimental_option("prefs", prefs)
            # 设置窗口大小
            options.add_argument("--window-size=1920,1080")

            # 创建Service对象
            service = Service(executable_path=self.driver_path)

            driver = webdriver.Chrome(service=service, options=options)
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)

            logger.debug(f"创建了新的WebDriver实例")
            return driver

        except Exception as e:
            logger.error(f"创建WebDriver失败: {e}", exc_info=True)
            raise

    def acquire(self, timeout=30) -> Optional[webdriver.Chrome]:
        """
        获取一个WebDriver实例

        Args:
            timeout: 获取超时时间(秒)

        Returns:
            WebDriver实例，如果超时则返回None
        """
        if self._closed:
            raise RuntimeError("WebDriver池已关闭")

        start_time = time.time()

        while True:
            with self.lock:
                # 首先尝试从可用队列获取
                try:
                    driver = self.available.get_nowait()
                    # 检查driver是否仍然有效
                    if self._is_driver_valid(driver):
                        self.in_use.add(driver)
                        self.last_used[id(driver)] = time.time()
                        logger.debug(f"从池中获取driver,当前使用:{len(self.in_use)}/{self.max_drivers}")
                        return driver
                    else:
                        # driver无效，关闭它
                        self._close_driver(driver)
                        continue
                except queue.Empty:
                    pass

                # 如果没有可用的且未达上限，创建新的
                total_drivers = len(self.in_use) + self.available.qsize()
                if total_drivers < self.max_drivers:
                    try:
                        driver = self._create_driver()
                        self.in_use.add(driver)
                        self.last_used[id(driver)] = time.time()
                        logger.info(f"创建新driver,当前总数:{total_drivers + 1}/{self.max_drivers}")
                        return driver
                    except Exception as e:
                        logger.error(f"创建driver失败: {e}")
                        return None

            # 已达上限,等待
            if time.time() - start_time > timeout:
                logger.warning(f"获取WebDriver超时({timeout}秒)")
                return None

            time.sleep(0.5)

    def release(self, driver: webdriver.Chrome):
        """
        释放WebDriver回池中

        Args:
            driver: 要释放的WebDriver实例
        """
        if driver is None:
            return

        with self.lock:
            if driver not in self.in_use:
                logger.warning("尝试释放不在使用中的driver")
                return

            try:
                # 清理driver状态
                self._cleanup_driver_state(driver)
                # 从使用中移除
                self.in_use.discard(driver)
                # 放回可用队列
                self.available.put(driver)
                # 更新最后使用时间
                self.last_used[id(driver)] = time.time()
                logger.debug(f"释放driver回池,当前使用:{len(self.in_use)}/{self.max_drivers}")
            except Exception as e:
                logger.error(f"释放driver失败: {e}", exc_info=True)
                # 出错就关闭这个driver
                self._close_driver(driver)
                self.in_use.discard(driver)

    def _cleanup_driver_state(self, driver: webdriver.Chrome):
        """清理driver状态"""
        try:
            # 删除所有cookies
            driver.delete_all_cookies()
            # 清除local storage
            driver.execute_script("window.localStorage.clear();")
            driver.execute_script("window.sessionStorage.clear();")
        except Exception as e:
            logger.debug(f"清理driver状态时出错: {e}")

    def _is_driver_valid(self, driver: webdriver.Chrome) -> bool:
        """检查driver是否有效"""
        try:
            # 尝试获取当前URL来测试driver是否有效
            _ = driver.current_url
            return True
        except WebDriverException:
            return False
        except Exception:
            return False

    def _close_driver(self, driver: webdriver.Chrome):
        """关闭driver"""
        try:
            driver.quit()
            logger.debug("关闭了一个driver")
        except Exception as e:
            logger.debug(f"关闭driver时出错: {e}")
        finally:
            # 清理记录
            self.last_used.pop(id(driver), None)

    def _cleanup_idle_drivers(self):
        """清理空闲超时的driver"""
        with self.lock:
            current_time = time.time()
            drivers_to_close = []

            # 检查可用队列中的driver
            temp_queue = queue.Queue()
            while not self.available.empty():
                try:
                    driver = self.available.get_nowait()
                    driver_id = id(driver)
                    last_used_time = self.last_used.get(driver_id, current_time)

                    if current_time - last_used_time > self.idle_timeout:
                        # 超时，需要关闭
                        drivers_to_close.append(driver)
                    else:
                        # 未超时，放回临时队列
                        temp_queue.put(driver)
                except queue.Empty:
                    break

            # 将未超时的driver放回可用队列
            while not temp_queue.empty():
                self.available.put(temp_queue.get())

            # 关闭超时的driver
            for driver in drivers_to_close:
                self._close_driver(driver)

            if drivers_to_close:
                logger.info(f"清理了{len(drivers_to_close)}个空闲driver")

    def _start_cleanup_thread(self):
        """启动清理线程"""
        def cleanup_loop():
            while not self._closed:
                time.sleep(60)  # 每分钟检查一次
                if not self._closed:
                    self._cleanup_idle_drivers()

        thread = threading.Thread(target=cleanup_loop, daemon=True, name="WebDriverPool-Cleanup")
        thread.start()
        logger.info("WebDriver池清理线程已启动")

    def get_stats(self) -> dict:
        """获取池的统计信息"""
        with self.lock:
            return {
                "max_drivers": self.max_drivers,
                "in_use": len(self.in_use),
                "available": self.available.qsize(),
                "total": len(self.in_use) + self.available.qsize()
            }

    def close_all(self):
        """关闭所有driver"""
        self._closed = True

        with self.lock:
            # 关闭正在使用的
            for driver in list(self.in_use):
                self._close_driver(driver)
            self.in_use.clear()

            # 关闭可用队列中的
            while not self.available.empty():
                try:
                    driver = self.available.get_nowait()
                    self._close_driver(driver)
                except queue.Empty:
                    break

            logger.info("WebDriver池已关闭")

    def __del__(self):
        """析构时关闭所有driver"""
        self.close_all()


# 全局WebDriver池实例
_driver_pool = None
_pool_lock = threading.Lock()


def get_driver_pool(max_drivers=8, idle_timeout=300) -> WebDriverPool:
    """
    获取全局WebDriver池实例(单例模式)

    Args:
        max_drivers: 最大driver数量
        idle_timeout: 空闲超时时间

    Returns:
        WebDriverPool实例
    """
    global _driver_pool

    if _driver_pool is None:
        with _pool_lock:
            if _driver_pool is None:
                _driver_pool = WebDriverPool(
                    max_drivers=max_drivers,
                    idle_timeout=idle_timeout
                )

    return _driver_pool
