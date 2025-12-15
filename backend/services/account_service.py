"""
账号服务模块
负责平台账号的管理和测试
"""
import json
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger_config import setup_logger, log_service_call
from typing import List, Dict, Optional
from models import PlatformAccount, get_db_session
from encryption import encrypt_password, decrypt_password

logger = setup_logger(__name__)


class AccountService:
    """账号服务类"""

    def __init__(self, config):
        """初始化账号服务"""
        self.config = config
        self.accounts_file = config.ACCOUNTS_FILE


    @log_service_call("获取用户账号列表")
    def get_user_accounts(self, user_id: int) -> List[Dict]:
        """
        获取用户的所有账号

        Args:
            user_id: 用户ID

        Returns:
            账号列表
        """
        db = get_db_session()
        try:
            accounts = db.query(PlatformAccount).filter_by(
                user_id=user_id
            ).all()
            return [acc.to_dict() for acc in accounts]
        finally:
            db.close()


    @log_service_call("添加平台账号")
    def add_account(self, user_id: int, platform: str, username: str,
                   password: str, config: Optional[str] = None) -> Dict:
        """
        添加新账号

        Args:
            user_id: 用户ID
            platform: 平台名称
            username: 用户名
            password: 密码
            config: 额外配置(JSON字符串)

        Returns:
            添加结果
        """
        db = get_db_session()
        try:
            # 加密密码
            encrypted_pwd = encrypt_password(password)

            # 创建账号
            account = PlatformAccount(
                user_id=user_id,
                platform=platform,
                username=username,
                password=encrypted_pwd,
                config=config
            )

            db.add(account)
            db.commit()

            logger.info(f'Account added: {platform} - {username}')
            return {
                'success': True,
                'account': account.to_dict()
            }

        except Exception as e:
            db.rollback()
            logger.error(f'Failed to add account: {e}', exc_info=True)
            raise
        finally:
            db.close()


    @log_service_call("删除账号")
    def delete_account(self, user_id: int, account_id: int) -> bool:
        """
        删除账号

        Args:
            user_id: 用户ID
            account_id: 账号ID

        Returns:
            是否成功删除
        """
        db = get_db_session()
        try:
            account = db.query(PlatformAccount).filter_by(
                id=account_id,
                user_id=user_id
            ).first()

            if not account:
                logger.warning(f'Account not found: {account_id}')
                return False

            db.delete(account)
            db.commit()
            logger.info(f'Account deleted: {account_id}')
            return True

        except Exception as e:
            db.rollback()
            logger.error(f'Failed to delete account: {e}', exc_info=True)
            raise
        finally:
            db.close()

    def get_account_with_password(self, user_id: int, account_id: int) -> Optional[Dict]:
        """
        获取账号及解密后的密码（用于测试和发布）

        Args:
            user_id: 用户ID
            account_id: 账号ID

        Returns:
            账号信息（包含解密密码）
        """
        db = get_db_session()
        try:
            account = db.query(PlatformAccount).filter_by(
                id=account_id,
                user_id=user_id
            ).first()

            if not account:
                return None

            account_dict = account.to_dict()
            account_dict['password'] = decrypt_password(account.password)
            return account_dict

        finally:
            db.close()
