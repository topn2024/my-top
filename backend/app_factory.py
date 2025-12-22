"""
应用工厂
创建和配置Flask应用
"""
from flask import Flask
from flask_cors import CORS
import logging
import sys
import io

from config import get_config


def create_app(config_name='default'):
    """
    应用工厂函数

    Args:
        config_name: 配置名称 ('development', 'production', 'testing', 'default')

    Returns:
        配置好的Flask应用实例
    """
    # 创建Flask应用
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')

    # 加载配置
    config = get_config(config_name)
    app.config.from_object(config)

    # 配置JSON编码支持中文 (Flask 3.x使用json_encoder参数)
    app.json.ensure_ascii = False

    # 初始化配置（创建目录等）
    config.init_app()

    # 生产环境配置验证
    if config_name == 'production' and hasattr(config, 'validate_config'):
        try:
            config.validate_config()
        except RuntimeError as e:
            # 配置验证失败，记录错误并退出
            logging.error(f"Configuration validation failed: {e}")
            raise

    # 配置CORS
    CORS(app)

    # 配置日志
    setup_logging(config)

    # 初始化权限系统
    from auth import init_permissions
    init_permissions(app)

    # 注册蓝图
    register_blueprints(app)

    # 注册错误处理器
    register_error_handlers(app)

    # 注册上下文处理器
    register_context_processors(app)

    # 添加 favicon 路由
    @app.route('/favicon.ico')
    def favicon():
        from flask import send_from_directory, Response
        import os
        # 尝试从 static 目录发送 favicon.ico，如果不存在则返回 204
        favicon_path = os.path.join(app.root_path, '..', 'static', 'favicon.ico')
        if os.path.exists(favicon_path):
            return send_from_directory(os.path.join(app.root_path, '..', 'static'),
                                     'favicon.ico', mimetype='image/vnd.microsoft.icon')
        else:
            # 返回 204 No Content，避免 404 错误
            return Response(status=204)

    return app


def setup_logging(config):
    """配置日志"""
    import os
    from logging.handlers import RotatingFileHandler

    # 设置Windows控制台输出编码
    # 注意：在某些环境下（如后台执行），不应重新包装stdout/stderr
    # if sys.platform == 'win32':
    #     sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    #     sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    # 创建根logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.LOG_LEVEL))

    # 创建格式化器
    formatter = logging.Formatter(config.LOG_FORMAT)

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, config.LOG_LEVEL))
    console_handler.setFormatter(formatter)

    # all.log文件处理器 - 所有日志
    all_log_file = os.path.join(config.LOGS_FOLDER, 'all.log')
    all_file_handler = RotatingFileHandler(
        all_log_file,
        maxBytes=50*1024*1024,  # 50MB
        backupCount=5,
        encoding='utf-8'
    )
    all_file_handler.setLevel(logging.DEBUG)  # 记录所有级别
    all_file_handler.setFormatter(formatter)

    # 清除现有处理器
    root_logger.handlers.clear()

    # 添加处理器
    root_logger.addHandler(console_handler)
    root_logger.addHandler(all_file_handler)

    # 设置第三方库日志级别
    logging.getLogger('werkzeug').setLevel(logging.INFO)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('selenium').setLevel(logging.INFO)

    logging.info(f'日志配置完成: 控制台输出 + {all_log_file}')


def register_blueprints(app):
    """注册蓝图"""
    from blueprints.pages import pages_bp
    from blueprints.auth import auth_bp
    from blueprints.api import api_bp
    from blueprints.task_api import task_bp
    from blueprints.prompt_template_api import bp as prompt_template_bp

    # 新增：三模块提示词系统API蓝图
    from blueprints.analysis_prompt_api import analysis_prompt_bp
    from blueprints.article_prompt_api import article_prompt_bp
    from blueprints.platform_style_api import platform_style_bp
    from blueprints.prompt_combination_api import combination_bp
    from blueprints.article_style_api import article_style_bp

    # 注册页面蓝图
    app.register_blueprint(pages_bp)

    # 注册认证蓝图
    app.register_blueprint(auth_bp)

    # 注册API蓝图
    app.register_blueprint(api_bp)

    # 注册任务API蓝图
    app.register_blueprint(task_bp, url_prefix='/task')

    # 注册提示词模板API蓝图（旧系统，保留兼容）
    app.register_blueprint(prompt_template_bp)

    # 注册三模块提示词系统API蓝图（新系统）
    app.register_blueprint(analysis_prompt_bp)
    app.register_blueprint(article_prompt_bp)
    app.register_blueprint(platform_style_bp)
    app.register_blueprint(combination_bp)
    app.register_blueprint(article_style_bp)

    logging.info('Blueprints registered successfully')


def register_error_handlers(app):
    """注册错误处理器"""
    from flask import jsonify

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': '请求参数错误'}), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': '未授权，请先登录'}), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': '无权访问'}), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': '资源不存在'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        logging.error(f'Internal error: {error}', exc_info=True)
        return jsonify({'error': '服务器内部错误'}), 500


def register_context_processors(app):
    """注册上下文处理器"""
    @app.context_processor
    def inject_config():
        """注入配置到模板上下文"""
        return {
            'app_name': 'TOP_N',
            'version': '2.0'
        }


# 创建应用实例（用于向后兼容）
# 从环境变量读取配置，默认为production
import os
_config_name = os.environ.get('FLASK_ENV', 'production')
app = create_app(_config_name)


if __name__ == '__main__':
    import os
    # 从环境变量获取端口，默认3001
    port = int(os.environ.get('PORT', 3001))

    # 从命令行参数获取端口
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    app.run(host='0.0.0.0', port=port, debug=False)
