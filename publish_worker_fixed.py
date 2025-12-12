"""
发布Worker - RQ任务执行器
负责实际执行发布任务
"""
import logging
from datetime import datetime
from typing import Dict

from backend.models import PublishTask, get_db_session, User
from backend.services.webdriver_pool import get_driver_pool
from backend.services.user_rate_limiter import get_rate_limiter

logger = logging.getLogger(__name__)


def execute_publish_task(task_db_id: int) -> Dict:
    """
    执行发布任务(RQ Worker调用的函数)

    Args:
        task_db_id: 任务数据库ID

    Returns:
        执行结果
    """
    db = None
    driver = None
    driver_pool = None
    task = None

    try:
        # 1. 获取任务信息
        db = get_db_session()
        task = db.query(PublishTask).filter(PublishTask.id == task_db_id).first()

        if not task:
            logger.error(f"任务不存在: {task_db_id}")
            return {'success': False, 'error': '任务不存在'}

        logger.info(f"开始执行任务: {task.task_id}, user={task.user_id}, title={task.article_title[:30]}")

        # 2. 更新状态为running
        task.status = 'running'
        task.started_at = datetime.now()
        task.progress = 10
        db.commit()

        # 3. 获取WebDriver
        driver_pool = get_driver_pool(max_drivers=8, idle_timeout=300)
        driver = driver_pool.acquire(timeout=60)

        if not driver:
            raise Exception("无法获取WebDriver,连接池已满或超时")

        task.progress = 30
        db.commit()

        # 4. 执行发布
        logger.info(f"开始发布到{task.platform}: {task.article_title[:30]}")

        if task.platform == 'zhihu' or task.platform == '知乎':
            result = _publish_to_zhihu(
                driver=driver,
                title=task.article_title,
                content=task.article_content,
                user_id=task.user_id,
                db=db
            )
        else:
            raise Exception(f"不支持的平台: {task.platform}")

        task.progress = 90
        db.commit()

        # 5. 更新结果
        if result['success']:
            task.status = 'success'
            task.result_url = result.get('url')
            task.progress = 100
            task.completed_at = datetime.now()
            logger.info(f"任务成功: {task.task_id}, URL={task.result_url}")
        else:
            raise Exception(result.get('error', '发布失败'))

        db.commit()

        # 6. 释放限流令牌
        rate_limiter = get_rate_limiter()
        rate_limiter.release(task.user_id)

        return {
            'success': True,
            'task_id': task.task_id,
            'url': task.result_url
        }

    except Exception as e:
        logger.error(f"任务执行失败: {e}", exc_info=True)

        # 更新失败状态
        if task and db:
            try:
                task.status = 'failed'
                task.error_message = str(e)
                task.completed_at = datetime.now()
                db.commit()

                # 释放限流令牌
                rate_limiter = get_rate_limiter()
                rate_limiter.release(task.user_id)

            except Exception as update_error:
                logger.error(f"更新失败状态出错: {update_error}")
                if db:
                    db.rollback()

        return {
            'success': False,
            'error': str(e)
        }

    finally:
        # 7. 清理资源
        if driver and driver_pool:
            try:
                driver_pool.release(driver)
                logger.debug("WebDriver已释放回池")
            except Exception as e:
                logger.error(f"释放WebDriver失败: {e}")

        if db:
            try:
                db.close()
            except Exception as e:
                logger.error(f"关闭数据库连接失败: {e}")


def _publish_to_zhihu(driver, title: str, content: str, user_id: int, db) -> Dict:
    """
    发布到知乎

    Args:
        driver: WebDriver实例
        title: 标题
        content: 内容
        user_id: 用户ID
        db: 数据库session

    Returns:
        发布结果
    """
    try:
        import os
        import json
        import time
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        # 1. 获取用户信息
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {'success': False, 'error': '用户不存在'}

        username = user.username

        # 2. 加载Cookie (JSON格式)
        cookies_dir = '/home/u_topn/TOP_N/backend/cookies'
        cookie_file = None

        # 尝试多个可能的cookie文件
        possible_files = [
            f'{cookies_dir}/zhihu_{username}.json',
            f'{cookies_dir}/zhihu_admin.json',  # 默认fallback
        ]

        for f in possible_files:
            if f and os.path.exists(f):
                cookie_file = f
                logger.info(f"找到Cookie文件: {cookie_file}")
                break

        if not cookie_file:
            logger.error(f"未找到Cookie文件,尝试的路径: {possible_files}")
            return {
                'success': False,
                'error': f'未找到知乎Cookie文件,请先在系统中登录知乎账号 (用户: {username})'
            }

        # 3. 加载并设置Cookie
        driver.get('https://www.zhihu.com')
        time.sleep(2)

        try:
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)

            for cookie in cookies:
                try:
                    # 确保cookie格式正确
                    if 'name' in cookie and 'value' in cookie:
                        driver.add_cookie(cookie)
                except Exception as e:
                    logger.warning(f"添加cookie失败: {e}, cookie={cookie.get('name', 'unknown')}")
                    continue

            logger.info(f"已加载 {len(cookies)} 个Cookie from {cookie_file}")

            # 刷新页面使cookie生效
            driver.refresh()
            time.sleep(2)

        except Exception as e:
            logger.error(f"加载Cookie失败: {e}")
            return {'success': False, 'error': f'加载Cookie失败: {str(e)}'}

        # 4. 访问写文章页面
        driver.get('https://zhuanlan.zhihu.com/write')
        time.sleep(3)

        # 5. 检查是否登录
        current_url = driver.current_url
        if 'signin' in current_url or 'login' in current_url:
            logger.error(f"Cookie已过期,当前URL: {current_url}")
            return {
                'success': False,
                'error': f'知乎Cookie已过期,请重新登录 (用户: {username})'
            }

        logger.info("知乎登录验证成功,开始填写文章")

        # 6. 输入标题
        try:
            title_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='标题']"))
            )
            title_input.clear()
            title_input.send_keys(title)
            logger.info(f"标题已输入: {title[:30]}")
        except Exception as e:
            logger.error(f"输入标题失败: {e}")
            raise Exception("无法定位标题输入框")

        time.sleep(1)

        # 7. 输入内容
        try:
            # 知乎使用contenteditable的div
            content_div = driver.find_element(By.CSS_SELECTOR, "div[contenteditable='true']")
            # 使用JavaScript设置内容
            driver.execute_script(
                "arguments[0].innerHTML = arguments[1];",
                content_div,
                content.replace('\n', '<br>')
            )
            logger.info(f"内容已输入,长度: {len(content)}")
        except Exception as e:
            logger.error(f"输入内容失败: {e}")
            raise Exception("无法定位内容编辑器")

        time.sleep(2)

        # 8. 点击发布按钮
        try:
            publish_btn = driver.find_element(By.XPATH, "//button[contains(text(), '发布')]")
            publish_btn.click()
            logger.info("已点击发布按钮")
        except Exception as e:
            logger.error(f"点击发布按钮失败: {e}")
            raise Exception("无法找到发布按钮")

        # 9. 等待发布完成
        time.sleep(5)

        # 10. 获取文章URL
        current_url = driver.current_url
        if 'zhuanlan.zhihu.com/p/' in current_url:
            article_url = current_url
            logger.info(f"发布成功,文章URL: {article_url}")
            return {
                'success': True,
                'url': article_url,
                'message': '发布成功'
            }
        else:
            # 可能是草稿或其他状态
            logger.warning(f"发布后URL异常: {current_url}")
            return {
                'success': True,
                'url': current_url,
                'message': '文章已保存(可能是草稿状态)'
            }

    except Exception as e:
        logger.error(f"知乎发布失败: {e}", exc_info=True)
        return {
            'success': False,
            'error': f'发布失败: {str(e)}'
        }
