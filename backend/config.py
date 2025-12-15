"""
配置管理模块
集中管理所有配置项，提高可维护性
"""
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    """基础配置类"""

    # Flask配置
    SECRET_KEY = os.environ.get('TOPN_SECRET_KEY', 'TopN_Secret_Key_2024_Please_Change_In_Production')
    SESSION_COOKIE_NAME = 'topn_session'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400  # 24小时

    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'md'}
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    MAX_FILE_SIZE = MAX_CONTENT_LENGTH

    # 目录配置
    DATA_FOLDER = os.path.join(BASE_DIR, 'data')
    ACCOUNTS_FOLDER = os.path.join(BASE_DIR, 'accounts')
    COOKIES_FOLDER = os.path.join(BASE_DIR, 'backend', 'cookies')
    LOGS_FOLDER = os.path.join(BASE_DIR, 'logs')

    # 账号配置文件
    ACCOUNTS_FILE = os.path.join(ACCOUNTS_FOLDER, 'accounts.json')

    # AI API 配置 - 默认使用智谱 AI
    # 智谱 AI 配置
    ZHIPU_API_KEY = os.environ.get('ZHIPU_API_KEY', 'd6ac02f8c1f6f443cf81f3dae86fb095.7Qe6KOWcVDlDlqDJ')
    ZHIPU_API_BASE = 'https://open.bigmodel.cn/api/paas/v4'
    ZHIPU_CHAT_URL = f'{ZHIPU_API_BASE}/chat/completions'
    ZHIPU_MODEL = 'glm-4-flash'  # 可选: glm-4, glm-4-flash, glm-4-plus

    # 千问API配置（备用）
    QIANWEN_API_KEY = os.environ.get('QIANWEN_API_KEY', 'sk-f0a85d3e56a746509ec435af2446c67a')
    QIANWEN_API_BASE = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
    QIANWEN_CHAT_URL = f'{QIANWEN_API_BASE}/chat/completions'
    QIANWEN_MODEL = 'qwen-plus'

    # 默认 AI 服务商 (zhipu 或 qianwen)
    DEFAULT_AI_PROVIDER = os.environ.get('AI_PROVIDER', 'zhipu')

    # 支持的AI模型配置
    SUPPORTED_MODELS = {
        'glm-4-flash': {
            'name': '智谱AI GLM-4-Flash',
            'description': '快速响应，适合日常对话和内容生成',
            'provider': 'zhipu',
            'max_tokens': 4000
        },
        'glm-4': {
            'name': '智谱AI GLM-4',
            'description': '平衡性能，适合复杂分析和推理',
            'provider': 'zhipu',
            'max_tokens': 8000
        },
        'glm-4-plus': {
            'name': '智谱AI GLM-4-Plus',
            'description': '最强性能，适合专业深度分析',
            'provider': 'zhipu',
            'max_tokens': 8000
        },
        'qwen-plus': {
            'name': '千问Plus',
            'description': '通义千问增强版，性能均衡',
            'provider': 'qianwen',
            'max_tokens': 6000
        },
        'qwen-turbo': {
            'name': '千问Turbo',
            'description': '快速响应版本',
            'provider': 'qianwen',
            'max_tokens': 6000
        }
    }

    # 默认使用的AI模型
    DEFAULT_AI_MODEL = os.environ.get('DEFAULT_AI_MODEL', 'glm-4-plus')

    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'

    # 数据库配置(如果需要)
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///topn.db')

    @classmethod
    def init_app(cls):
        """初始化应用配置，创建必要的目录"""
        os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(cls.DATA_FOLDER, exist_ok=True)
        os.makedirs(cls.ACCOUNTS_FOLDER, exist_ok=True)
        os.makedirs(cls.COOKIES_FOLDER, exist_ok=True)
        os.makedirs(cls.LOGS_FOLDER, exist_ok=True)


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    LOG_LEVEL = 'INFO'


class TestConfig(Config):
    """测试环境配置"""
    TESTING = True
    LOG_LEVEL = 'DEBUG'


# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """获取配置对象"""
    if env is None:
        env = os.environ.get('FLASK_ENV', 'default')
    return config.get(env, config['default'])
