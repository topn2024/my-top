#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理后台API
提供管理员专用的API端点
"""
from flask import Blueprint, request, jsonify
from sqlalchemy import func, or_
from datetime import datetime, timedelta
import sys
import os

# 从父目录导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import admin_required, get_current_user
from models import SessionLocal, User, Workflow, Article, PublishHistory, PlatformAccount
from logger_config import setup_logger, log_api_request
import bcrypt

logger = setup_logger(__name__)

# 创建蓝图
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


# ============================================================================
# 用户管理 API
# ============================================================================

@admin_bp.route('/users', methods=['GET'])
@admin_required
@log_api_request("获取用户列表")
def get_users():
    """获取用户列表（分页、搜索、筛选）"""
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    search = request.args.get('search', '', type=str).strip()
    role = request.args.get('role', '', type=str).strip()

    db = SessionLocal()
    try:
        # 构建查询
        query = db.query(User)

        # 搜索过滤
        if search:
            query = query.filter(
                or_(
                    User.username.like(f'%{search}%'),
                    User.email.like(f'%{search}%'),
                    User.full_name.like(f'%{search}%')
                )
            )

        # 角色过滤
        if role:
            query = query.filter(User.role == role)

        # 获取总数
        total = query.count()

        # 分页
        users = query.order_by(User.created_at.desc())\
                    .limit(limit)\
                    .offset((page - 1) * limit)\
                    .all()

        # 转换为字典
        user_list = [user.to_dict() for user in users]

        return jsonify({
            'success': True,
            'users': user_list,
            'total': total,
            'page': page,
            'limit': limit,
            'pages': (total + limit - 1) // limit  # 向上取整
        })

    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        return jsonify({'success': False, 'error': '获取用户列表失败'}), 500
    finally:
        db.close()


@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@admin_required
@log_api_request("获取用户详情")
def get_user(user_id):
    """获取单个用户详情"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            return jsonify({'success': False, 'error': '用户不存在'}), 404

        # 获取用户统计信息
        workflow_count = db.query(func.count(Workflow.id))\
            .filter(Workflow.user_id == user_id).scalar()

        article_count = db.query(func.count(Article.id))\
            .join(Workflow)\
            .filter(Workflow.user_id == user_id).scalar()

        publish_count = db.query(func.count(PublishHistory.id))\
            .filter(PublishHistory.user_id == user_id).scalar()

        user_data = user.to_dict()
        user_data['stats'] = {
            'workflows': workflow_count,
            'articles': article_count,
            'publishes': publish_count
        }

        return jsonify({
            'success': True,
            'user': user_data
        })

    except Exception as e:
        logger.error(f"获取用户详情失败: {str(e)}")
        return jsonify({'success': False, 'error': '获取用户详情失败'}), 500
    finally:
        db.close()


@admin_bp.route('/users', methods=['POST'])
@admin_required
@log_api_request("创建用户")
def create_user():
    """创建新用户"""
    data = request.json

    # 验证必填字段
    required_fields = ['username', 'email', 'password']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'缺少必填字段: {field}'}), 400

    db = SessionLocal()
    try:
        # 检查用户名是否存在
        existing_user = db.query(User).filter(User.username == data['username']).first()
        if existing_user:
            return jsonify({'success': False, 'error': '用户名已存在'}), 400

        # 检查邮箱是否存在
        existing_email = db.query(User).filter(User.email == data['email']).first()
        if existing_email:
            return jsonify({'success': False, 'error': '邮箱已存在'}), 400

        # 加密密码
        password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # 创建用户
        new_user = User(
            username=data['username'],
            email=data['email'],
            password_hash=password_hash,
            full_name=data.get('full_name', ''),
            role=data.get('role', 'user'),
            is_active=data.get('is_active', True)
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        logger.info(f"创建用户成功: {new_user.username}")

        return jsonify({
            'success': True,
            'message': '用户创建成功',
            'user': new_user.to_dict()
        }), 201

    except Exception as e:
        db.rollback()
        logger.error(f"创建用户失败: {str(e)}")
        return jsonify({'success': False, 'error': '创建用户失败'}), 500
    finally:
        db.close()


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
@log_api_request("更新用户信息")
def update_user(user_id):
    """更新用户信息"""
    data = request.json

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            return jsonify({'success': False, 'error': '用户不存在'}), 404

        # 更新允许的字段
        if 'email' in data:
            # 检查邮箱是否被其他用户使用
            existing = db.query(User).filter(
                User.email == data['email'],
                User.id != user_id
            ).first()
            if existing:
                return jsonify({'success': False, 'error': '邮箱已被使用'}), 400
            user.email = data['email']

        if 'full_name' in data:
            user.full_name = data['full_name']

        if 'role' in data and data['role'] in ['user', 'admin']:
            user.role = data['role']

        if 'is_active' in data:
            user.is_active = data['is_active']

        db.commit()
        db.refresh(user)

        logger.info(f"更新用户成功: {user.username}")

        return jsonify({
            'success': True,
            'message': '用户更新成功',
            'user': user.to_dict()
        })

    except Exception as e:
        db.rollback()
        logger.error(f"更新用户失败: {str(e)}")
        return jsonify({'success': False, 'error': '更新用户失败'}), 500
    finally:
        db.close()


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
@log_api_request("删除用户")
def delete_user(user_id):
    """删除用户"""
    current_user = get_current_user()

    # 不能删除自己
    if current_user.id == user_id:
        return jsonify({'success': False, 'error': '不能删除自己的账号'}), 400

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            return jsonify({'success': False, 'error': '用户不存在'}), 404

        username = user.username

        # 删除用户（级联删除相关数据）
        db.delete(user)
        db.commit()

        logger.info(f"删除用户成功: {username}")

        return jsonify({
            'success': True,
            'message': f'用户 {username} 已删除'
        })

    except Exception as e:
        db.rollback()
        logger.error(f"删除用户失败: {str(e)}")
        return jsonify({'success': False, 'error': '删除用户失败'}), 500
    finally:
        db.close()


@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@admin_required
@log_api_request("重置用户密码")
def reset_user_password(user_id):
    """重置用户密码"""
    data = request.json

    if not data.get('new_password'):
        return jsonify({'success': False, 'error': '请提供新密码'}), 400

    if len(data['new_password']) < 6:
        return jsonify({'success': False, 'error': '密码长度至少6位'}), 400

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            return jsonify({'success': False, 'error': '用户不存在'}), 404

        # 加密新密码
        password_hash = bcrypt.hashpw(
            data['new_password'].encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        user.password_hash = password_hash
        db.commit()

        logger.info(f"重置用户密码成功: {user.username}")

        return jsonify({
            'success': True,
            'message': '密码重置成功'
        })

    except Exception as e:
        db.rollback()
        logger.error(f"重置用户密码失败: {str(e)}")
        return jsonify({'success': False, 'error': '重置密码失败'}), 500
    finally:
        db.close()


# ============================================================================
# 仪表板统计 API
# ============================================================================

@admin_bp.route('/stats/overview', methods=['GET'])
@admin_required
@log_api_request("获取概览统计")
def get_overview_stats():
    """获取仪表板概览统计数据"""
    db = SessionLocal()
    try:
        # 总用户数
        total_users = db.query(func.count(User.id)).scalar()

        # 活跃用户（最近7天登录）
        seven_days_ago = datetime.now() - timedelta(days=7)
        active_users = db.query(func.count(User.id))\
            .filter(User.last_login >= seven_days_ago).scalar()

        # 今日文章生成数
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_articles = db.query(func.count(Article.id))\
            .filter(Article.created_at >= today_start).scalar()

        # 今日发布成功数
        today_publishes = db.query(func.count(PublishHistory.id))\
            .filter(
                PublishHistory.published_at >= today_start,
                PublishHistory.status == 'success'
            ).scalar()

        # 计算增长率（与昨天对比）
        yesterday_start = today_start - timedelta(days=1)

        yesterday_articles = db.query(func.count(Article.id))\
            .filter(
                Article.created_at >= yesterday_start,
                Article.created_at < today_start
            ).scalar()

        yesterday_publishes = db.query(func.count(PublishHistory.id))\
            .filter(
                PublishHistory.published_at >= yesterday_start,
                PublishHistory.published_at < today_start,
                PublishHistory.status == 'success'
            ).scalar()

        # 计算增长率
        article_growth = ((today_articles - yesterday_articles) / yesterday_articles * 100) \
            if yesterday_articles > 0 else 0

        publish_growth = ((today_publishes - yesterday_publishes) / yesterday_publishes * 100) \
            if yesterday_publishes > 0 else 0

        return jsonify({
            'success': True,
            'data': {
                'total_users': total_users,
                'active_users': active_users,
                'today_articles': today_articles,
                'today_publishes': today_publishes,
                'article_growth': round(article_growth, 1),
                'publish_growth': round(publish_growth, 1)
            }
        })

    except Exception as e:
        logger.error(f"获取概览统计失败: {str(e)}")
        return jsonify({'success': False, 'error': '获取统计数据失败'}), 500
    finally:
        db.close()


@admin_bp.route('/stats/charts', methods=['GET'])
@admin_required
@log_api_request("获取图表数据")
def get_chart_stats():
    """获取图表统计数据"""
    period = request.args.get('period', 'week', type=str)

    db = SessionLocal()
    try:
        now = datetime.now()

        if period == 'week':
            # 最近7天
            days = 7
            labels = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        elif period == 'month':
            # 最近30天，按周统计
            days = 30
            labels = ['第1周', '第2周', '第3周', '第4周']
        else:  # year
            # 最近12个月
            days = 365
            labels = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']

        # 计算时间范围
        start_date = now - timedelta(days=days)

        # 获取文章生成数据
        if period == 'week':
            # 按天统计
            article_data = []
            for i in range(7):
                day_start = (now - timedelta(days=6-i)).replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day_start + timedelta(days=1)
                count = db.query(func.count(Article.id))\
                    .filter(
                        Article.created_at >= day_start,
                        Article.created_at < day_end
                    ).scalar()
                article_data.append(count)
        else:
            # 简化：返回模拟数据（实际项目中应该按周或月聚合）
            article_data = [0] * len(labels)

        return jsonify({
            'success': True,
            'data': {
                'labels': labels,
                'article_generation': article_data
            }
        })

    except Exception as e:
        logger.error(f"获取图表数据失败: {str(e)}")
        return jsonify({'success': False, 'error': '获取图表数据失败'}), 500
    finally:
        db.close()


@admin_bp.route('/stats/system', methods=['GET'])
@admin_required
@log_api_request("获取系统状态")
def get_system_stats():
    """获取系统状态信息"""
    import psutil
    import os

    try:
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)

        # 内存使用率
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        # 磁盘使用率
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent

        # 系统运行时间
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        uptime_days = uptime.days

        # 数据库大小
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(BASE_DIR, 'data', 'topn.db')
        db_size_mb = os.path.getsize(db_path) / (1024 * 1024) if os.path.exists(db_path) else 0

        return jsonify({
            'success': True,
            'data': {
                'cpu': round(cpu_percent, 1),
                'memory': round(memory_percent, 1),
                'disk': round(disk_percent, 1),
                'uptime_days': uptime_days,
                'service_status': 'running',
                'db_size_mb': round(db_size_mb, 2)
            }
        })

    except Exception as e:
        logger.error(f"获取系统状态失败: {str(e)}")
        return jsonify({'success': False, 'error': '获取系统状态失败'}), 500


# ============================================================================
# 工作流管理 API
# ============================================================================

@admin_bp.route('/workflows', methods=['GET'])
@admin_required
@log_api_request("获取工作流列表")
def get_workflows():
    """获取工作流列表（分页、筛选）"""
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    status = request.args.get('status', '', type=str).strip()
    user_id = request.args.get('user_id', None, type=int)

    db = SessionLocal()
    try:
        # 构建查询
        query = db.query(Workflow, User.username)\
            .join(User, Workflow.user_id == User.id)

        # 状态过滤
        if status:
            query = query.filter(Workflow.status == status)

        # 用户过滤
        if user_id:
            query = query.filter(Workflow.user_id == user_id)

        # 获取总数
        total = query.count()

        # 分页
        results = query.order_by(Workflow.created_at.desc())\
                      .limit(limit)\
                      .offset((page - 1) * limit)\
                      .all()

        # 转换为字典
        workflows = []
        for workflow, username in results:
            workflow_dict = workflow.to_dict()
            workflow_dict['username'] = username
            workflows.append(workflow_dict)

        return jsonify({
            'success': True,
            'workflows': workflows,
            'total': total,
            'page': page,
            'limit': limit,
            'pages': (total + limit - 1) // limit
        })

    except Exception as e:
        logger.error(f"获取工作流列表失败: {str(e)}")
        return jsonify({'success': False, 'error': '获取工作流列表失败'}), 500
    finally:
        db.close()


@admin_bp.route('/workflows/<int:workflow_id>', methods=['GET'])
@admin_required
@log_api_request("获取工作流详情")
def get_workflow(workflow_id):
    """获取工作流详情"""
    db = SessionLocal()
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()

        if not workflow:
            return jsonify({'success': False, 'error': '工作流不存在'}), 404

        # 获取关联的用户信息
        user = db.query(User).filter(User.id == workflow.user_id).first()

        # 获取关联的文章列表
        articles = db.query(Article)\
            .filter(Article.workflow_id == workflow_id)\
            .order_by(Article.article_order)\
            .all()

        workflow_dict = workflow.to_dict()
        workflow_dict['username'] = user.username if user else 'Unknown'
        workflow_dict['articles'] = [article.to_dict() for article in articles]

        return jsonify({
            'success': True,
            'workflow': workflow_dict
        })

    except Exception as e:
        logger.error(f"获取工作流详情失败: {str(e)}")
        return jsonify({'success': False, 'error': '获取工作流详情失败'}), 500
    finally:
        db.close()


@admin_bp.route('/workflows/<int:workflow_id>', methods=['DELETE'])
@admin_required
@log_api_request("删除工作流")
def delete_workflow(workflow_id):
    """删除工作流"""
    db = SessionLocal()
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()

        if not workflow:
            return jsonify({'success': False, 'error': '工作流不存在'}), 404

        company_name = workflow.company_name

        # 删除工作流（级联删除相关文章和发布历史）
        db.delete(workflow)
        db.commit()

        logger.info(f"删除工作流成功: {company_name}")

        return jsonify({
            'success': True,
            'message': f'工作流 {company_name} 已删除'
        })

    except Exception as e:
        db.rollback()
        logger.error(f"删除工作流失败: {str(e)}")
        return jsonify({'success': False, 'error': '删除工作流失败'}), 500
    finally:
        db.close()


# ============================================================================
# 发布管理 API
# ============================================================================

@admin_bp.route('/publishing/history', methods=['GET'])
@admin_required
@log_api_request("获取发布历史")
def get_publish_history():
    """获取发布历史（分页、筛选）"""
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    platform = request.args.get('platform', '', type=str).strip()
    status = request.args.get('status', '', type=str).strip()
    date_from = request.args.get('date_from', '', type=str).strip()
    date_to = request.args.get('date_to', '', type=str).strip()

    db = SessionLocal()
    try:
        # 构建查询
        query = db.query(PublishHistory, User.username)\
            .join(User, PublishHistory.user_id == User.id)

        # 平台过滤
        if platform:
            query = query.filter(PublishHistory.platform == platform)

        # 状态过滤
        if status:
            query = query.filter(PublishHistory.status == status)

        # 日期范围过滤
        if date_from:
            try:
                from_date = datetime.fromisoformat(date_from)
                query = query.filter(PublishHistory.published_at >= from_date)
            except ValueError:
                pass

        if date_to:
            try:
                to_date = datetime.fromisoformat(date_to)
                query = query.filter(PublishHistory.published_at <= to_date)
            except ValueError:
                pass

        # 获取总数
        total = query.count()

        # 分页
        results = query.order_by(PublishHistory.published_at.desc())\
                      .limit(limit)\
                      .offset((page - 1) * limit)\
                      .all()

        # 转换为字典
        history = []
        for publish, username in results:
            publish_dict = publish.to_dict()
            publish_dict['username'] = username
            history.append(publish_dict)

        return jsonify({
            'success': True,
            'history': history,
            'total': total,
            'page': page,
            'limit': limit,
            'pages': (total + limit - 1) // limit
        })

    except Exception as e:
        logger.error(f"获取发布历史失败: {str(e)}")
        return jsonify({'success': False, 'error': '获取发布历史失败'}), 500
    finally:
        db.close()


@admin_bp.route('/publishing/stats', methods=['GET'])
@admin_required
@log_api_request("获取发布统计")
def get_publish_stats():
    """获取发布统计数据"""
    period = request.args.get('period', 'week', type=str)

    db = SessionLocal()
    try:
        # 计算时间范围
        now = datetime.now()
        if period == 'week':
            start_date = now - timedelta(days=7)
        elif period == 'month':
            start_date = now - timedelta(days=30)
        else:  # all
            start_date = datetime(2000, 1, 1)

        # 总发布次数
        total_attempts = db.query(func.count(PublishHistory.id))\
            .filter(PublishHistory.published_at >= start_date).scalar()

        # 成功发布次数
        successful = db.query(func.count(PublishHistory.id))\
            .filter(
                PublishHistory.published_at >= start_date,
                PublishHistory.status == 'success'
            ).scalar()

        # 失败发布次数
        failed = total_attempts - successful

        # 成功率
        success_rate = (successful / total_attempts * 100) if total_attempts > 0 else 0

        # 按平台统计
        platform_stats = db.query(
                PublishHistory.platform,
                func.count(PublishHistory.id).label('total'),
                func.sum(func.case([(PublishHistory.status == 'success', 1)], else_=0)).label('success')
            )\
            .filter(PublishHistory.published_at >= start_date)\
            .group_by(PublishHistory.platform)\
            .all()

        by_platform = {}
        for platform, total, success in platform_stats:
            by_platform[platform] = {
                'total': total,
                'success': success,
                'failed': total - success
            }

        return jsonify({
            'success': True,
            'data': {
                'total_attempts': total_attempts,
                'successful': successful,
                'failed': failed,
                'success_rate': round(success_rate, 2),
                'by_platform': by_platform
            }
        })

    except Exception as e:
        logger.error(f"获取发布统计失败: {str(e)}")
        return jsonify({'success': False, 'error': '获取发布统计失败'}), 500
    finally:
        db.close()


# ============================================================================
# 数据分析 API
# ============================================================================

@admin_bp.route('/analytics/content', methods=['GET'])
@admin_required
@log_api_request("获取内容分析数据")
def get_content_analytics():
    """获取内容分析数据"""
    period = request.args.get('period', 'week', type=str)

    db = SessionLocal()
    try:
        # 计算时间范围
        now = datetime.now()
        if period == 'week':
            days = 7
            start_date = now - timedelta(days=days)
        elif period == 'month':
            days = 30
            start_date = now - timedelta(days=days)
        else:
            days = 365
            start_date = now - timedelta(days=days)

        # 总生成内容数
        total_generated = db.query(func.count(Article.id))\
            .filter(Article.created_at >= start_date).scalar()

        # 总发布内容数
        total_published = db.query(func.count(PublishHistory.id))\
            .filter(
                PublishHistory.published_at >= start_date,
                PublishHistory.status == 'success'
            ).scalar()

        # 内容质量评分（简化为发布率）
        quality_score = (total_published / total_generated * 10) \
            if total_generated > 0 else 0

        # 趋势数据（按天统计）
        if period == 'week':
            labels = []
            generated = []
            published = []

            for i in range(7):
                day_start = (now - timedelta(days=6-i)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                day_end = day_start + timedelta(days=1)

                labels.append(f'周{i+1}')

                gen_count = db.query(func.count(Article.id))\
                    .filter(
                        Article.created_at >= day_start,
                        Article.created_at < day_end
                    ).scalar()
                generated.append(gen_count)

                pub_count = db.query(func.count(PublishHistory.id))\
                    .filter(
                        PublishHistory.published_at >= day_start,
                        PublishHistory.published_at < day_end,
                        PublishHistory.status == 'success'
                    ).scalar()
                published.append(pub_count)

            trend = {
                'labels': labels,
                'generated': generated,
                'published': published
            }
        else:
            # 简化：返回空趋势
            trend = {'labels': [], 'generated': [], 'published': []}

        return jsonify({
            'success': True,
            'data': {
                'total_generated': total_generated,
                'total_published': total_published,
                'quality_score': round(quality_score, 1),
                'trend': trend
            }
        })

    except Exception as e:
        logger.error(f"获取内容分析失败: {str(e)}")
        return jsonify({'success': False, 'error': '获取内容分析失败'}), 500
    finally:
        db.close()
