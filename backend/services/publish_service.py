"""
发布服务模块
负责文章发布到各个平台
"""
import logging
from typing import Dict, Optional
from models import PublishHistory, get_db_session

logger = logging.getLogger(__name__)


class PublishService:
    """发布服务类"""

    def __init__(self, config):
        """初始化发布服务"""
        self.config = config

    def publish_to_zhihu(self, user_id: int, account_id: int,
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
            from zhihu_auto_post import post_article_to_zhihu
            from services.account_service import AccountService

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
                # 没有配置账号，需要二维码登录
                logger.info('No account configured, QR login required')
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

    def _save_publish_history(self, user_id: int, article_id: int,
                             platform: str, status: str,
                             url: Optional[str] = None,
                             message: Optional[str] = None):
        """保存发布历史"""
        db = get_db_session()
        try:
            # 临时发布时article_id为0，需要转换为NULL
            if article_id == 0:
                article_id = None

            history = PublishHistory(
                user_id=user_id,
                article_id=article_id,
                platform=platform,
                status=status,
                url=url,
                message=message
            )
            db.add(history)
            db.commit()
            logger.info(f'Publish history saved: article_id={article_id}, platform={platform}, status={status}')
        except Exception as e:
            db.rollback()
            logger.error(f'Failed to save publish history: {e}')
        finally:
            db.close()

    def get_publish_history(self, user_id: int, limit: int = 20, platform: str = None):
        """
        获取发布历史

        Args:
            user_id: 用户ID
            limit: 返回记录数量限制
            platform: 平台筛选(可选)

        Returns:
            发布历史列表,包含文章标题等详细信息
        """
        from models import Article, PublishTask
        from sqlalchemy.orm import joinedload

        db = get_db_session()
        try:
            # 使用LEFT JOIN来包含临时发布(article_id为NULL)的记录
            query = db.query(PublishHistory).outerjoin(
                Article, PublishHistory.article_id == Article.id
            ).filter(
                PublishHistory.user_id == user_id
            )

            # 如果指定平台,添加平台筛选
            if platform:
                query = query.filter(PublishHistory.platform == platform)

            # 按发布时间倒序排列
            history = query.order_by(
                PublishHistory.published_at.desc()
            ).limit(limit).all()

            # 转换为字典并添加文章标题
            result = []
            for h in history:
                item = h.to_dict()
                # 添加文章标题
                if h.article:
                    item['article_title'] = h.article.title
                    item['article_type'] = h.article.article_type
                else:
                    # 没有关联文章，尝试从URL和时间匹配PublishTask获取标题
                    title_found = False
                    if h.url:
                        # 尝试通过URL和时间范围匹配publish_tasks表
                        task = db.query(PublishTask).filter(
                            PublishTask.user_id == user_id,
                            PublishTask.result_url == h.url,
                            PublishTask.article_title.isnot(None)
                        ).first()

                        if task and task.article_title:
                            item['article_title'] = task.article_title
                            item['article_type'] = 'temp'
                            title_found = True

                    # 如果还是没找到标题，使用默认值
                    if not title_found:
                        item['article_title'] = '临时发布'
                        item['article_type'] = 'temp'

                result.append(item)

            return result
        finally:
            db.close()
