"""
API路由蓝图
处理所有API请求
"""
from flask import Blueprint, request, jsonify

# 从父目录导入
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import login_required, get_current_user
from config import get_config
from logger_config import setup_logger, log_api_request

# 初始化配置
config = get_config()

logger = setup_logger(__name__)

# 创建蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'service': 'TOP_N API',
        'version': '2.0'
    })


@api_bp.route('/upload', methods=['POST'])
@login_required
@log_api_request("上传文件并提取文本")
def upload_file():
    """文件上传"""
    from services.file_service import FileService

    file_service = FileService(config)
    file = request.files.get('file')

    if not file:
        return jsonify({'error': '没有选择文件'}), 400

    # 保存文件
    success, message, filepath = file_service.save_file(file)

    if not success:
        return jsonify({'error': message}), 400

    # 提取文本
    text = file_service.extract_text(filepath)

    if text is None:
        return jsonify({
            'success': False,
            'error': '无法从文件中提取文本内容，请检查文件格式是否正确'
        }), 400

    return jsonify({
        'success': True,
        'message': message,
        'text': text,
        'filename': file.filename
    })


@api_bp.route('/analyze', methods=['POST'])
@login_required
@log_api_request("分析公司信息")
def analyze_company():
    """公司分析"""
    from services.ai_service import AIService
    from services.workflow_service import WorkflowService
    from services.prompt_template_service import PromptTemplateService
    from services.analysis_prompt_service import AnalysisPromptService
    from services.ai_service_v2 import AIServiceV2

    user = get_current_user()
    data = request.json

    if not data.get('company_name'):
        return jsonify({'error': '请输入公司名称'}), 400

    try:
        # 检查是否使用新的三模块提示词系统
        analysis_prompt_id = data.get('analysis_prompt_id')

        if analysis_prompt_id:
            # 使用新的三模块系统
            logger.info(f'Using V2 analysis prompt: {analysis_prompt_id}')

            # 获取分析提示词
            analysis_prompt = AnalysisPromptService.get_prompt(analysis_prompt_id)
            if not analysis_prompt:
                return jsonify({'error': f'分析提示词不存在: {analysis_prompt_id}'}), 404

            # 使用AIServiceV2进行分析
            ai_service_v2 = AIServiceV2(config)
            company_info = {
                'company_name': data.get('company_name'),
                'company_desc': data.get('company_desc', ''),
                'uploaded_text': data.get('uploaded_text', '')
            }
            analysis = ai_service_v2.analyze_with_prompt(company_info, analysis_prompt)

            # 更新使用统计
            AnalysisPromptService.increment_usage(analysis_prompt_id)

        else:
            # 兼容旧系统
            ai_service = AIService(config)

            # 检查是否使用旧模板
            template_id = data.get('template_id')
            template = None
            if template_id:
                template = PromptTemplateService.get_template(template_id)
                if not template:
                    return jsonify({'error': f'模板不存在: {template_id}'}), 404
                logger.info(f'Using template: {template["name"]} (ID: {template_id})')

            # 使用模板或默认方法进行分析
            if template:
                company_info = {
                    'company_name': data.get('company_name'),
                    'company_desc': data.get('company_desc', ''),
                    'uploaded_text': data.get('uploaded_text', '')
                }
                analysis = ai_service.analyze_company_with_template(company_info, template)
            else:
                analysis = ai_service.analyze_company(
                    company_name=data.get('company_name'),
                    company_desc=data.get('company_desc', ''),
                    uploaded_text=data.get('uploaded_text', '')
                )

        # 保存工作流（包含新的prompt IDs）
        workflow_service = WorkflowService()
        workflow_data = {
            'company_name': data.get('company_name'),
            'company_desc': data.get('company_desc'),
            'uploaded_text': data.get('uploaded_text', ''),
            'uploaded_filename': data.get('uploaded_filename', ''),
            'template_id': data.get('template_id'),
            'analysis': analysis,
            'current_step': 2
        }

        # 添加新的三模块提示词ID
        if analysis_prompt_id:
            workflow_data['analysis_prompt_id'] = analysis_prompt_id
        if data.get('article_prompt_id'):
            workflow_data['article_prompt_id'] = data.get('article_prompt_id')
        if data.get('platform_style_prompt_id'):
            workflow_data['platform_style_prompt_id'] = data.get('platform_style_prompt_id')

        workflow = workflow_service.save_workflow(
            user_id=user.id,
            workflow_id=data.get('workflow_id'),
            data=workflow_data
        )

        logger.info(f'Analysis completed for: {data.get("company_name")}')
        return jsonify({
            'success': True,
            'analysis': analysis,
            'company_name': data.get('company_name'),
            'workflow_id': workflow['workflow']['id']
        })

    except Exception as e:
        logger.error(f'Analysis failed: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@api_bp.route('/generate_articles', methods=['POST'])
@login_required
@log_api_request("生成推广文章")
def generate_articles():
    """生成文章"""
    from services.ai_service import AIService
    from services.workflow_service import WorkflowService
    from services.prompt_template_service import PromptTemplateService
    from services.article_prompt_service import ArticlePromptService
    from services.platform_style_service import PlatformStyleService
    from services.ai_service_v2 import AIServiceV2

    user = get_current_user()
    data = request.json

    try:
        # 检查是否使用新的三模块提示词系统
        article_prompt_id = data.get('article_prompt_id')
        platform_style_prompt_id = data.get('platform_style_prompt_id')

        if article_prompt_id:
            # 使用新的三模块系统
            logger.info(f'Using V2 article prompt: {article_prompt_id}')

            # 获取文章提示词
            article_prompt = ArticlePromptService.get_prompt(article_prompt_id)
            if not article_prompt:
                return jsonify({'error': f'文章提示词不存在: {article_prompt_id}'}), 404

            # 获取平台风格提示词（如果指定）
            platform_style = None
            if platform_style_prompt_id:
                platform_style = PlatformStyleService.get_style(platform_style_prompt_id)
                if platform_style:
                    logger.info(f'Using platform style: {platform_style["name"]} ({platform_style["platform"]})')

            # 使用AIServiceV2生成文章
            ai_service_v2 = AIServiceV2(config)
            articles = ai_service_v2.generate_articles_with_prompts(
                company_name=data.get('company_name'),
                analysis=data.get('analysis'),
                article_prompt=article_prompt,
                article_count=data.get('article_count', 3),
                platform_style=platform_style
            )

            # 更新使用统计
            ArticlePromptService.increment_usage(article_prompt_id)
            if platform_style_prompt_id:
                PlatformStyleService.increment_usage(platform_style_prompt_id)

        else:
            # 兼容旧系统
            ai_service = AIService(config)

            # 检查是否使用旧模板
            template_id = data.get('template_id')
            template = None
            if template_id:
                template = PromptTemplateService.get_template(template_id)
                if template:
                    logger.info(f'Using template for article generation: {template["name"]} (ID: {template_id})')

            # 使用模板或默认方法生成文章
            if template:
                articles = ai_service.generate_articles_with_template(
                    company_name=data.get('company_name'),
                    analysis=data.get('analysis'),
                    template=template,
                    article_count=data.get('article_count', 3)
                )
            else:
                articles = ai_service.generate_articles(
                    company_name=data.get('company_name'),
                    analysis=data.get('analysis'),
                    article_count=data.get('article_count', 3)
                )

        # 保存文章到数据库
        saved_articles = articles
        if data.get('workflow_id'):
            workflow_service = WorkflowService()
            saved_articles = workflow_service.save_articles(
                user_id=user.id,
                workflow_id=data.get('workflow_id'),
                articles=articles
            )

            # 如果使用了旧模板，记录使用情况
            if data.get('template_id'):
                PromptTemplateService.increment_usage_count(data.get('template_id'))

        logger.info(f'Generated and saved {len(saved_articles)} articles for {data.get("company_name")}')
        return jsonify({
            'success': True,
            'articles': saved_articles
        })

    except Exception as e:
        logger.error(f'Article generation failed: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@api_bp.route('/models', methods=['GET'])
def get_models():
    """获取支持的AI模型列表"""
    try:
        models = []
        for model_id, model_info in config.SUPPORTED_MODELS.items():
            models.append({
                'id': model_id,
                'name': model_info['name'],
                'description': model_info['description']
            })

        return jsonify({
            'success': True,
            'models': models,
            'default': config.DEFAULT_AI_MODEL
        })
    except Exception as e:
        logger.error(f'Failed to get models: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@api_bp.route('/accounts', methods=['GET'])
@login_required
@log_api_request("获取平台账号列表")
def get_accounts():
    """获取账号列表"""
    from services.account_service import AccountService

    user = get_current_user()

    try:
        account_service = AccountService(config)
        accounts = account_service.get_user_accounts(user.id)

        return jsonify({
            'success': True,
            'accounts': accounts
        })

    except Exception as e:
        logger.error(f'Get accounts failed: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@api_bp.route('/accounts', methods=['POST'])
@login_required
@log_api_request("添加平台账号")
def add_account():
    """添加账号"""
    from services.account_service import AccountService

    user = get_current_user()
    data = request.json

    try:
        account_service = AccountService(config)
        result = account_service.add_account(
            user_id=user.id,
            platform=data.get('platform'),
            username=data.get('username'),
            password=data.get('password'),
            config=data.get('config')
        )

        logger.info(f'Account added: {data.get("platform")} - {data.get("username")}')
        return jsonify(result)

    except Exception as e:
        logger.error(f'Add account failed: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@api_bp.route('/accounts/<int:account_id>', methods=['DELETE'])
@login_required
@log_api_request("删除平台账号")
def delete_account(account_id):
    """删除账号"""
    from services.account_service import AccountService

    user = get_current_user()

    try:
        account_service = AccountService(config)
        success = account_service.delete_account(user.id, account_id)

        if success:
            logger.info(f'Account deleted: {account_id}')
            return jsonify({'success': True})
        else:
            return jsonify({'error': '账号不存在'}), 404

    except Exception as e:
        logger.error(f'Delete account failed: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@api_bp.route('/publish_zhihu', methods=['POST'])
@login_required
@log_api_request("发布文章到知乎")
def publish_to_zhihu():
    """发布到知乎（异步任务队列版本）"""
    from services.task_queue_manager import get_task_manager

    user = get_current_user()
    data = request.json

    # 验证必填参数
    if not data.get('title'):
        return jsonify({'error': '缺少文章标题'}), 400
    if not data.get('content'):
        return jsonify({'error': '缺少文章内容'}), 400

    # 获取article_id (如果前端传了就用，没传就用0表示临时文章)
    article_id = data.get('article_id')
    if article_id is None:
        logger.warning('Publishing without article_id - article will not be archived')
        article_id = 0

    try:
        # 使用任务队列管理器创建异步任务
        task_manager = get_task_manager()
        result = task_manager.create_publish_task(
            user_id=user.id,
            article_title=data.get('title'),
            article_content=data.get('content'),
            platform='zhihu',
            article_id=article_id
        )

        if result['success']:
            logger.info(f'Task created: {result["task_id"]} for user {user.id}')
            return jsonify({
                'success': True,
                'task_id': result['task_id'],
                'status': result['status'],
                'message': '发布任务已创建，正在后台处理'
            })
        else:
            logger.error(f'Failed to create task: {result.get("error")}')
            return jsonify(result), 400

    except Exception as e:
        logger.error(f'Publish to Zhihu failed: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/publish_zhihu_batch', methods=['POST'])
@login_required
@log_api_request("批量发布文章到知乎")
def publish_to_zhihu_batch():
    """批量发布到知乎（异步）"""
    from services.task_queue_manager import get_task_manager

    user = get_current_user()
    data = request.json

    logger.info(f'[发布流程-API] ========== 批量发布API调用开始 ==========')
    logger.info(f'[发布流程-API] 用户: {user.username} (ID: {user.id})')
    logger.info(f'[发布流程-API] 请求IP: {request.remote_addr}')

    # 验证参数
    articles = data.get('articles', [])
    logger.info(f'[发布流程-API] 接收到 {len(articles)} 篇文章')

    if not articles:
        logger.warning('[发布流程-API] 文章列表为空，返回错误')
        return jsonify({'error': '缺少文章列表'}), 400

    # 记录每篇文章的标题（前30字符）
    for idx, article in enumerate(articles, 1):
        title = article.get('title', '未命名')[:30]
        article_id = article.get('article_id', 0)
        logger.info(f'[发布流程-API] 文章{idx}: {title} (ID: {article_id})')

    try:
        logger.info('[发布流程-API] 调用任务队列管理器创建批量任务')
        task_manager = get_task_manager()

        result = task_manager.create_batch_tasks(
            user_id=user.id,
            articles=articles,
            platform='zhihu'
        )

        logger.info(f'[发布流程-API] 批量任务创建完成: 成功 {result["success_count"]}/{result["total"]}')

        if result['failed_count'] > 0:
            logger.warning(f'[发布流程-API] 有 {result["failed_count"]} 个任务创建失败')
            for idx, item in enumerate(result.get('results', []), 1):
                if not item['result'].get('success'):
                    logger.warning(f'[发布流程-API] 失败任务{idx}: {item.get("article_title")} - {item["result"].get("error")}')

        logger.info('[发布流程-API] ========== 批量发布API调用结束 ==========')
        return jsonify(result)

    except Exception as e:
        logger.error(f'[发布流程-API] 批量发布失败，异常: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/publish_task/<task_id>', methods=['GET'])
@login_required
@log_api_request("查询发布任务状态")
def get_publish_task_status(task_id):
    """获取发布任务状态"""
    from services.task_queue_manager import get_task_manager

    user = get_current_user()

    try:
        task_manager = get_task_manager()
        task = task_manager.get_task_status(task_id)

        if not task:
            return jsonify({'error': '任务不存在'}), 404

        # 验证任务所有权
        if task['user_id'] != user.id:
            return jsonify({'error': '无权访问此任务'}), 403

        return jsonify({
            'success': True,
            'task': task
        })

    except Exception as e:
        logger.error(f'Get task status failed: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/publish_tasks', methods=['GET'])
@login_required
@log_api_request("获取发布任务列表")
def get_publish_tasks():
    """获取用户的发布任务列表"""
    from services.task_queue_manager import get_task_manager

    user = get_current_user()

    # 获取查询参数
    status = request.args.get('status')
    limit = int(request.args.get('limit', 20))
    offset = int(request.args.get('offset', 0))

    try:
        task_manager = get_task_manager()
        result = task_manager.get_user_tasks(
            user_id=user.id,
            status=status,
            limit=limit,
            offset=offset
        )

        return jsonify(result)

    except Exception as e:
        logger.error(f'Get user tasks failed: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/publish_task/<task_id>/cancel', methods=['POST'])
@login_required
@log_api_request("取消发布任务")
def cancel_publish_task(task_id):
    """取消发布任务"""
    from services.task_queue_manager import get_task_manager

    user = get_current_user()

    try:
        task_manager = get_task_manager()
        result = task_manager.cancel_task(task_id, user.id)

        return jsonify(result)

    except Exception as e:
        logger.error(f'Cancel task failed: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/publish_task/<task_id>/retry', methods=['POST'])
@login_required
@log_api_request("重试失败的发布任务")
def retry_publish_task(task_id):
    """重试失败的任务"""
    from services.task_queue_manager import get_task_manager

    user = get_current_user()

    try:
        task_manager = get_task_manager()
        result = task_manager.retry_task(task_id, user.id)

        return jsonify(result)

    except Exception as e:
        logger.error(f'Retry task failed: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/workflow/current', methods=['GET'])
@login_required
@log_api_request("获取当前工作流")
def get_current_workflow():
    """获取当前工作流"""
    from services.workflow_service import WorkflowService

    user = get_current_user()

    try:
        workflow_service = WorkflowService()
        workflow = workflow_service.get_current_workflow(user.id)

        return jsonify({
            'success': True,
            'workflow': workflow
        })

    except Exception as e:
        logger.error(f'Get workflow failed: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@api_bp.route('/workflow/save', methods=['POST'])
@login_required
@log_api_request("保存工作流")
def save_workflow():
    """保存工作流"""
    from services.workflow_service import WorkflowService

    user = get_current_user()
    data = request.json

    try:
        workflow_service = WorkflowService()
        result = workflow_service.save_workflow(
            user_id=user.id,
            workflow_id=data.get('workflow_id'),
            data=data.get('data', {})
        )

        logger.info(f'Workflow saved: {result["workflow"]["id"]}')
        return jsonify(result)

    except Exception as e:
        logger.error(f'Save workflow failed: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@api_bp.route('/workflow/list', methods=['GET'])
@login_required
@log_api_request("获取工作流列表")
def get_workflow_list():
    """获取工作流列表"""
    from services.workflow_service import WorkflowService

    user = get_current_user()
    limit = request.args.get('limit', 10, type=int)

    try:
        workflow_service = WorkflowService()
        workflows = workflow_service.get_workflow_list(user.id, limit)

        return jsonify({
            'success': True,
            'workflows': workflows
        })

    except Exception as e:
        logger.error(f'Get workflow list failed: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@api_bp.route('/zhihu/qr_login/start', methods=['POST'])
@login_required
@log_api_request("开始知乎二维码登录")
def start_zhihu_qr_login():
    """开始知乎二维码登录流程"""
    from zhihu_auth.zhihu_qr_login import ZhihuQRLogin

    user = get_current_user()

    try:
        qr_login = ZhihuQRLogin()
        success, qr_base64, message = qr_login.get_qr_code()

        if success:
            # 将登录会话存储(简单实现,生产环境需要更安全的方式)
            session_id = f"zhihu_login_{user.id}"
            # 存储QR登录会话到全局变量(后续可以改为Redis)
            if not hasattr(api_bp, 'qr_login_sessions'):
                api_bp.qr_login_sessions = {}
            api_bp.qr_login_sessions[session_id] = qr_login

            return jsonify({
                'success': True,
                'qr_code': f'data:image/png;base64,{qr_base64}',
                'session_id': session_id,
                'message': '请使用知乎APP扫码登录'
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 500

    except Exception as e:
        logger.error(f'Start QR login failed: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/zhihu/qr_login/check', methods=['POST'])
@login_required
@log_api_request("检查知乎二维码登录状态")
def check_zhihu_qr_login():
    """检查二维码登录状态"""
    user = get_current_user()
    data = request.json
    session_id = data.get('session_id')

    if not session_id:
        return jsonify({'success': False, 'error': '缺少session_id'}), 400

    try:
        # 获取QR登录会话
        if not hasattr(api_bp, 'qr_login_sessions') or session_id not in api_bp.qr_login_sessions:
            return jsonify({'success': False, 'error': '登录会话不存在或已过期'}), 404

        qr_login = api_bp.qr_login_sessions[session_id]

        # 检查登录状态(非阻塞,快速检查)
        import time
        current_url = qr_login.driver.url if qr_login.driver else ''

        # 检查是否已经登录成功
        if 'zhihu.com' in current_url and '/signin' not in current_url:
            # 登录成功,保存Cookie
            qr_login.save_cookies(user.username)

            # 清理会话
            qr_login.close()
            del api_bp.qr_login_sessions[session_id]

            return jsonify({
                'success': True,
                'logged_in': True,
                'message': '登录成功'
            })
        else:
            # 还在等待扫码
            return jsonify({
                'success': True,
                'logged_in': False,
                'message': '等待扫码中...'
            })

    except Exception as e:
        logger.error(f'Check QR login failed: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/publish_history', methods=['GET'])
@login_required
@log_api_request("获取发布历史记录")
def get_publish_history():
    """获取发布历史记录"""
    from services.publish_service import PublishService

    user = get_current_user()
    limit = request.args.get('limit', 20, type=int)
    platform = request.args.get('platform')  # 可选的平台筛选

    try:
        publish_service = PublishService(config)
        history = publish_service.get_publish_history(
            user_id=user.id,
            limit=limit,
            platform=platform
        )

        return jsonify({
            'success': True,
            'history': history,
            'count': len(history)
        })

    except Exception as e:
        logger.error(f'Get publish history failed: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@api_bp.route('/articles/history', methods=['GET'])
@login_required
@log_api_request("获取用户文章归档")
def get_user_articles():
    """获取用户的文章归档（包含已发布和未发布的文章）"""
    from services.workflow_service import WorkflowService
    from models import get_db_session, Article, Workflow, PublishHistory

    user = get_current_user()
    limit = request.args.get('limit', 50, type=int)
    workflow_id = request.args.get('workflow_id', type=int)  # 可选：按工作流筛选

    db = get_db_session()
    try:
        # 查询用户的文章
        query = db.query(Article).join(Workflow).filter(Workflow.user_id == user.id)

        # 如果指定了workflow_id，则筛选
        if workflow_id:
            query = query.filter(Article.workflow_id == workflow_id)

        # 按创建时间倒序排列
        articles = query.order_by(Article.created_at.desc()).limit(limit).all()

        # 构建返回数据，包含文章和发布历史
        result = []
        for article in articles:
            article_dict = article.to_dict()

            # 获取该文章的发布历史
            publish_records = db.query(PublishHistory).filter_by(
                article_id=article.id
            ).order_by(PublishHistory.published_at.desc()).all()

            article_dict['publish_history'] = [record.to_dict() for record in publish_records]
            article_dict['publish_count'] = len(publish_records)

            # 添加工作流信息
            if article.workflow:
                article_dict['company_name'] = article.workflow.company_name

            result.append(article_dict)

        logger.info(f'Retrieved {len(result)} articles for user {user.id}')
        return jsonify({
            'success': True,
            'articles': result,
            'count': len(result)
        })

    except Exception as e:
        logger.error(f'Get user articles failed: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()
