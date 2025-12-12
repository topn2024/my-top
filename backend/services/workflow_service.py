"""
工作流服务模块
负责工作流程的管理和文章保存
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional
from models import Workflow, Article, get_db_session

logger = logging.getLogger(__name__)


class WorkflowService:
    """工作流服务类"""

    def get_current_workflow(self, user_id: int) -> Optional[Dict]:
        """
        获取用户当前工作流

        Args:
            user_id: 用户ID

        Returns:
            工作流信息或None
        """
        db = get_db_session()
        try:
            workflow = db.query(Workflow).filter_by(
                user_id=user_id
            ).order_by(Workflow.updated_at.desc()).first()

            return workflow.to_dict() if workflow else None
        finally:
            db.close()

    def save_workflow(self, user_id: int, workflow_id: Optional[int],
                     data: Dict) -> Dict:
        """
        保存工作流

        Args:
            user_id: 用户ID
            workflow_id: 工作流ID（新建时为None）
            data: 工作流数据

        Returns:
            保存结果
        """
        db = get_db_session()
        try:
            if workflow_id:
                # 更新现有工作流
                workflow = db.query(Workflow).filter_by(
                    id=workflow_id,
                    user_id=user_id
                ).first()

                if not workflow:
                    raise ValueError(f'Workflow not found: {workflow_id}')

                # 更新字段
                for key, value in data.items():
                    if hasattr(workflow, key):
                        setattr(workflow, key, value)
            else:
                # 创建新工作流
                workflow = Workflow(user_id=user_id, **data)
                db.add(workflow)

            db.commit()
            logger.info(f'Workflow saved: {workflow.id}')

            return {
                'success': True,
                'workflow': workflow.to_dict()
            }

        except Exception as e:
            db.rollback()
            logger.error(f'Failed to save workflow: {e}', exc_info=True)
            raise
        finally:
            db.close()

    def save_articles(self, user_id: int, workflow_id: int,
                     articles: List[Dict]) -> List[Dict]:
        """
        保存生成的文章

        Args:
            user_id: 用户ID
            workflow_id: 工作流ID
            articles: 文章列表

        Returns:
            保存后的文章列表（包含ID）
        """
        db = get_db_session()
        try:
            # 验证工作流属于该用户
            workflow = db.query(Workflow).filter_by(
                id=workflow_id,
                user_id=user_id
            ).first()

            if not workflow:
                raise ValueError(f'Workflow not found: {workflow_id}')

            # 删除旧文章
            db.query(Article).filter_by(workflow_id=workflow_id).delete()

            # 保存新文章
            saved_articles = []
            for idx, article_data in enumerate(articles):
                article = Article(
                    workflow_id=workflow_id,
                    title=article_data.get('title', ''),
                    content=article_data.get('content', ''),
                    article_type=article_data.get('type', ''),
                    article_order=idx
                )
                db.add(article)
                db.flush()  # 刷新以获取ID

                # 构建返回的文章数据
                saved_article = {
                    'id': article.id,
                    'title': article.title,
                    'content': article.content,
                    'type': article.article_type,
                    'order': article.article_order
                }
                saved_articles.append(saved_article)

            db.commit()
            logger.info(f'Saved {len(articles)} articles for workflow {workflow_id}')
            return saved_articles

        except Exception as e:
            db.rollback()
            logger.error(f'Failed to save articles: {e}', exc_info=True)
            raise
        finally:
            db.close()

    def get_workflow_list(self, user_id: int, limit: int = 10) -> List[Dict]:
        """
        获取用户的工作流列表

        Args:
            user_id: 用户ID
            limit: 返回数量限制

        Returns:
            工作流列表
        """
        db = get_db_session()
        try:
            workflows = db.query(Workflow).filter_by(
                user_id=user_id
            ).order_by(Workflow.updated_at.desc()).limit(limit).all()

            return [wf.to_dict() for wf in workflows]
        finally:
            db.close()
