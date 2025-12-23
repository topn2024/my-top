"""
配置管理模块
集中管理所有配置项，提高可维护性
"""
import os
from pathlib import Path

# 加载.env文件
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # dotenv未安装，跳过

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
    # 智谱 AI 配置 - 必须通过环境变量或.env文件设置
    ZHIPU_API_KEY = os.environ.get('ZHIPU_API_KEY', '')
    ZHIPU_API_BASE = 'https://open.bigmodel.cn/api/paas/v4'
    ZHIPU_CHAT_URL = f'{ZHIPU_API_BASE}/chat/completions'
    ZHIPU_MODEL = 'glm-4-flash'  # 可选: glm-4, glm-4-flash, glm-4-plus

    # 千问API配置（备用）- 必须通过环境变量或.env文件设置
    QIANWEN_API_KEY = os.environ.get('QIANWEN_API_KEY', '')
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
    DEFAULT_AI_MODEL = os.environ.get('DEFAULT_AI_MODEL', 'glm-4-flash')

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

    @classmethod
    def validate_config(cls):
        """
        验证生产环境必需的配置项

        检查关键配置是否已设置，避免使用默认值导致安全问题

        Raises:
            RuntimeError: 当缺少必需的配置项时

        Returns:
            bool: 验证通过返回 True
        """
        import sys

        # 不安全的默认值（用于检查是否使用了开发默认值）
        DEFAULT_VALUES = {
            'TOPN_SECRET_KEY': 'TopN_Secret_Key_2024_Please_Change_In_Production',
        }
        # 注意: 所有API密钥现在都必须通过环境变量设置，不再有硬编码的默认值

        # 必需的环境变量
        required_vars = {
            'TOPN_SECRET_KEY': '应用密钥（用于session加密）',
            'ZHIPU_API_KEY': '智谱AI API密钥',
        }

        # 推荐设置的环境变量
        recommended_vars = {
            'ENCRYPTION_KEY': '账号密码加密密钥',
            'DATABASE_URL': '数据库连接URL',
        }

        missing_required = []
        missing_recommended = []

        # 检查必需变量
        for var, description in required_vars.items():
            value = os.environ.get(var)
            if not value:
                missing_required.append(f"  - {var}: {description}")
            elif var in DEFAULT_VALUES and value == DEFAULT_VALUES[var]:
                # 检查是否使用了默认值
                missing_required.append(f"  - {var}: {description} (当前使用默认值，不安全)")

        # 检查推荐变量
        for var, description in recommended_vars.items():
            value = os.environ.get(var)
            if not value:
                missing_recommended.append(f"  - {var}: {description}")

        # 如果有缺失的必需变量，抛出异常
        if missing_required:
            error_msg = (
                "\n" + "="*70 + "\n"
                "❌ 生产环境配置验证失败\n"
                "="*70 + "\n\n"
                "缺少以下必需的环境变量:\n"
                + "\n".join(missing_required) + "\n\n"
                "请按以下步骤修复:\n"
                "1. 复制 .env.template 为 .env\n"
                "2. 填入实际的配置值\n"
                "3. 确保 .env 文件在项目根目录\n"
                "4. 重启应用\n\n"
                "提示: 使用 python -c \"import secrets; print(secrets.token_hex(32))\" 生成密钥\n"
                "="*70 + "\n"
            )

            # 打印到标准错误
            print(error_msg, file=sys.stderr)
            raise RuntimeError(error_msg)

        # 警告推荐变量缺失（不阻止启动）
        if missing_recommended:
            warning_msg = (
                "\n" + "="*70 + "\n"
                "⚠️  生产环境配置警告\n"
                "="*70 + "\n\n"
                "建议设置以下环境变量以提高安全性:\n"
                + "\n".join(missing_recommended) + "\n\n"
                "这些变量不是必需的，但强烈建议在生产环境中设置。\n"
                "="*70 + "\n"
            )
            print(warning_msg, file=sys.stderr)

        return True


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
