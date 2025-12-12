#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复发布服务的二维码登录流程
确保在未配置账号时，优先使用已保存的QR Cookie
"""

import paramiko
import sys
import io
import time

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

SERVER = "39.105.12.124"
USER = "u_topn"
PASSWORD = "TopN@2024"
DEPLOY_DIR = "/home/u_topn/TOP_N"

def main():
    print("修复发布服务的二维码登录流程...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)

    # 读取当前的publish_service.py
    print("\n读取当前的publish_service.py...")
    stdin, stdout, stderr = ssh.exec_command(f"cat {DEPLOY_DIR}/backend/services/publish_service.py")
    current_content = stdout.read().decode('utf-8')

    # 找到publish_to_zhihu方法
    print("\n查找publish_to_zhihu方法...")

    # 定义新的publish_to_zhihu方法实现
    new_method = '''    def publish_to_zhihu(self, user_id: int, account_id: int,
                        article_id: int, title: str, content: str) -> Dict:
        """
        发布文章到知乎

        Args:
            user_id: 用户ID
            account_id: 账号ID (0表示使用二维码登录)
            article_id: 文章ID
            title: 文章标题
            content: 文章内容

        Returns:
            发布结果
        """
        try:
            # 导入知乎发布模块
            from zhihu_auto_post_enhanced import post_article_to_zhihu
            from services.account_service import AccountService
            from models import User

            # 获取用户信息
            db = get_db_session()
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError('用户不存在')

            username_for_cookie = user.username

            # 判断是否使用账号密码登录
            if account_id > 0:
                # 使用保存的账号密码
                account_service = AccountService(self.config)
                account = account_service.get_account_with_password(user_id, account_id)

                if not account:
                    raise ValueError('账号不存在，请在账号管理中添加知乎账号，或使用二维码登录')

                # 调用发布函数（使用账号密码）
                result = post_article_to_zhihu(
                    username=account['username'],
                    password=account['password'],
                    title=title,
                    content=content,
                    topics=None,
                    draft=False
                )
            else:
                # account_id == 0，检查是否已有QR Cookie
                import os
                cookies_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cookies')
                cookie_file = os.path.join(cookies_dir, f'zhihu_{username_for_cookie}.json')

                if os.path.exists(cookie_file):
                    # Cookie存在，尝试使用Cookie登录并发布
                    logger.info(f'找到QR Cookie文件: {cookie_file}，尝试使用Cookie登录')
                    result = post_article_to_zhihu(
                        username=username_for_cookie,
                        password=None,  # 不使用密码，只用Cookie
                        title=title,
                        content=content,
                        topics=None,
                        draft=False
                    )
                else:
                    # Cookie不存在，需要二维码登录
                    logger.info('未找到QR Cookie，需要二维码登录')
                    return {
                        'success': False,
                        'requireQRLogin': True,  # 特殊标记，告诉前端需要二维码登录
                        'message': '请先使用二维码登录知乎账号'
                    }

            # 记录发布历史
            self._save_publish_history(
                user_id=user_id,
                article_id=article_id,
                platform='知乎',
                status='success' if result.get('success') else 'failed',
                url=result.get('url'),
                message=result.get('message') or result.get('error')
            )

            logger.info(f'Published to Zhihu: {title}')
            return result

        except Exception as e:
            logger.error(f'Failed to publish to Zhihu: {e}', exc_info=True)

            # 记录失败历史
            self._save_publish_history(
                user_id=user_id,
                article_id=article_id,
                platform='知乎',
                status='failed',
                message=str(e)
            )

            raise
'''

    # 替换方法
    import re

    # 匹配整个publish_to_zhihu方法
    pattern = r'(    def publish_to_zhihu\(self.*?\n)(?:.*?\n)*?(        except Exception as e:.*?raise\n)'

    if re.search(pattern, current_content, re.DOTALL):
        # 使用新方法替换
        new_content = re.sub(pattern, new_method + '\n', current_content, flags=re.DOTALL)

        # 上传新文件
        print("\n上传修改后的publish_service.py...")
        escaped_content = new_content.replace("'", "'\\''")
        cmd = f"cat > {DEPLOY_DIR}/backend/services/publish_service.py << 'ENDOFFILE'\n{new_content}\nENDOFFILE"

        stdin, stdout, stderr = ssh.exec_command(cmd)
        stdout.read()
        stderr_output = stderr.read().decode('utf-8')

        if stderr_output:
            print(f"⚠ stderr: {stderr_output}")

        print("✓ 已上传修改后的文件")
    else:
        print("⚠ 未找到publish_to_zhihu方法，无法替换")
        print("尝试直接在else分支前插入Cookie检查逻辑...")

        # 查找else分支（account_id == 0的情况）
        else_pattern = r"(            else:\n                # 没有配置账号，需要二维码登录\n                logger\.info\('No account configured, QR login required'\))"

        if re.search(else_pattern, current_content):
            # 构建新的else分支
            new_else_block = '''            else:
                # account_id == 0，检查是否已有QR Cookie
                import os
                cookies_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cookies')
                cookie_file = os.path.join(cookies_dir, f'zhihu_{username_for_cookie}.json')

                if os.path.exists(cookie_file):
                    # Cookie存在，尝试使用Cookie登录并发布
                    logger.info(f'找到QR Cookie文件: {cookie_file}，尝试使用Cookie登录')
                    result = post_article_to_zhihu(
                        username=username_for_cookie,
                        password=None,  # 不使用密码，只用Cookie
                        title=title,
                        content=content,
                        topics=None,
                        draft=False
                    )
                else:
                    # Cookie不存在，需要二维码登录
                    logger.info('未找到QR Cookie，需要二维码登录')'''

            new_content = re.sub(else_pattern, new_else_block, current_content)

            # 还需要在方法开始处添加user查询
            user_query_code = '''
            # 获取用户信息
            db = get_db_session()
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError('用户不存在')

            username_for_cookie = user.username

'''

            # 在导入语句后插入
            import_pattern = r"(from services\.account_service import AccountService\n)"
            new_content = re.sub(
                import_pattern,
                r"\1            from models import User" + user_query_code,
                new_content
            )

            # 上传
            print("\n上传修改后的publish_service.py...")
            cmd = f"cat > {DEPLOY_DIR}/backend/services/publish_service.py << 'ENDOFFILE'\n{new_content}\nENDOFFILE"

            stdin, stdout, stderr = ssh.exec_command(cmd)
            stdout.read()
            print("✓ 已上传修改后的文件")
        else:
            print("✗ 未找到合适的插入位置")
            ssh.close()
            return

    # 重启服务
    print("\n重启服务...")
    stdin, stdout, stderr = ssh.exec_command("pkill -f gunicorn; sleep 2")
    stdout.read()

    start_cmd = f"bash {DEPLOY_DIR}/start_service.sh"
    stdin, stdout, stderr = ssh.exec_command(start_cmd)
    print(stdout.read().decode('utf-8', errors='ignore'))

    time.sleep(3)

    # 测试健康检查
    print("\n测试健康检查...")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8080/api/health")
    print(stdout.read().decode('utf-8', errors='ignore'))

    print("\n✓ 修复完成")
    print("\n改进内容:")
    print("1. 在account_id=0时，首先检查是否已有QR Cookie文件")
    print("2. 如果Cookie存在，直接使用Cookie登录并发布")
    print("3. 如果Cookie不存在，才返回requireQRLogin要求扫码")
    print("4. 用户首次扫码后，Cookie会被保存")
    print("5. 后续发布会自动使用Cookie，无需重复扫码")

    ssh.close()

if __name__ == '__main__':
    main()
