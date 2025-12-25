"""
发布服务模块
负责文章发布到各个平台
"""
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger_config import setup_logger, log_service_call
from typing import Dict, Optional
from models import PublishHistory, get_db_session

logger = setup_logger(__name__)


class PublishService:
    """发布服务类"""

    def __init__(self, config):
        """初始化发布服务"""
        self.config = config


    @log_service_call("获取发布历史")
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

                # 优先使用publish_history表中已存储的article_title
                if item.get('article_title'):
                    # 已经有标题，保持不变
                    if not item.get('article_type'):
                        item['article_type'] = 'temp'
                # 如果没有标题，尝试从关联的Article表获取
                elif h.article:
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
