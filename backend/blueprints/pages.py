"""
页面路由蓝图
处理页面渲染
"""
from flask import Blueprint, render_template
import logging

logger = logging.getLogger(__name__)

# 创建蓝图
pages_bp = Blueprint('pages', __name__)


@pages_bp.route('/')
def home():
    """首页"""
    return render_template('home.html')


@pages_bp.route('/platform')
def platform_index():
    """平台页面"""
    return render_template('input.html')


@pages_bp.route('/analysis')
def analysis():
    """分析页面"""
    return render_template('analysis.html')


@pages_bp.route('/articles')
def articles():
    """文章页面"""
    return render_template('articles.html')


@pages_bp.route('/publish')
def publish():
    """发布页面"""
    return render_template('publish.html')


@pages_bp.route('/login')
def login_page():
    """登录页面"""
    return render_template('login.html')
