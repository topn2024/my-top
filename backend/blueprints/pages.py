"""
页面路由蓝图
处理页面渲染
"""
from flask import Blueprint, render_template
from auth_decorators import login_required, admin_required
import logging

logger = logging.getLogger(__name__)

# 创建蓝图
pages_bp = Blueprint('pages', __name__)


@pages_bp.route('/')
def home():
    """首页 - 公开访问"""
    return render_template('home.html')


@pages_bp.route('/platform')
@login_required
def platform_index():
    """平台页面 - 需要登录"""
    return render_template('input.html')


@pages_bp.route('/analysis')
@login_required
def analysis():
    """分析页面 - 需要登录"""
    return render_template('analysis.html')


@pages_bp.route('/articles')
@login_required
def articles():
    """文章页面 - 需要登录"""
    return render_template('articles.html')


@pages_bp.route('/publish')
@login_required
def publish():
    """发布页面 - 需要登录"""
    return render_template('publish.html')


@pages_bp.route('/login')
def login_page():
    """登录页面 - 公开访问"""
    return render_template('login.html')


@pages_bp.route('/help')
def help_center():
    """帮助中心页面 - 公开访问"""
    return render_template('help.html')


@pages_bp.route('/templates')
@admin_required
def templates():
    """模板管理页面 - 仅管理员"""
    return render_template('template_management.html')


@pages_bp.route('/template-guide')
@admin_required
def template_guide():
    """模板使用指南页面 - 仅管理员"""
    return render_template('template_guide.html')


@pages_bp.route('/prompts-v2')
@admin_required
def prompts_v2():
    """提示词管理系统V2 - 仅管理员"""
    return render_template('prompt_management_v2.html')


@pages_bp.route('/admin')
@admin_required
def admin_dashboard():
    """企业级管理控制台 - 仅管理员"""
    return render_template('admin_dashboard.html')
