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
    import logging

    logger = logging.getLogger(__name__)
    file_service = FileService(config)
    file = request.files.get('file')

    if not file:
        logger.warning("Upload attempt with no file")
        return jsonify({'error': '没有选择文件'}), 400

    logger.info(f"Upload request for file: {file.filename}, size: {file.content_length}")

    # 保存文件
    success, message, filepath = file_service.save_file(file)

    if not success:
        logger.error(f"File save failed: {message}")
        return jsonify({'error': message}), 400

    logger.info(f"File saved successfully: {filepath}")

    # 提取文本
    text = file_service.extract_text(filepath)

    if text is None:
        logger.error(f"Text extraction failed for file: {filepath}")
        return jsonify({
            'success': False,
            'error': '无法从文件中提取文本内容，请检查文件格式是否正确'
        }), 400

    logger.info(f"✓ Upload complete: file={file.filename}, text_length={len(text)}")

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
        # 获取用户选择的AI模型
        ai_model = data.get('ai_model')
        if ai_model:
            logger.info(f'User selected AI model: {ai_model}')

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
            # 传递AI模型参数
            analysis = ai_service_v2.analyze_with_prompt(company_info, analysis_prompt, model=ai_model)

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
                analysis = ai_service.analyze_company_with_template(company_info, template, model=ai_model)
            else:
                analysis = ai_service.analyze_company(
                    company_name=data.get('company_name'),
                    company_desc=data.get('company_desc', ''),
                    uploaded_text=data.get('uploaded_text', ''),
                    model=ai_model
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

# ============ 账号测试与导入 ============
@api_bp.route('/api/accounts/<int:account_id>/test', methods=['POST'])
@login_required
@log_api_request("测试平台账号连接")
def test_account(account_id):
    """测试账号登录 - 使用真实的网站登录"""
    try:
        user = get_current_user()
        db = get_db_session()

        try:
            account = db.query(PlatformAccount).filter_by(
                id=account_id,
                user_id=user.id
            ).first()

            if not account:
                return jsonify({'success': False, 'error': '账号不存在'}), 404

            platform = account.platform
            username = account.username
            password = decrypt_password(account.password_encrypted) if account.password_encrypted else ''

            logger.info(f'Testing account login: {platform} - {username}')
            logger.debug(f'Account ID: {account_id}, has password: {bool(password)}')

            if not username or not password:
                logger.warning(f'Incomplete account info - username: {bool(username)}, password: {bool(password)}')
                account.status = 'failed'
                account.last_tested = datetime.now()
                db.commit()

                return jsonify({
                    'success': False,
                    'message': '账号信息不完整，请填写用户名和密码'
                })
        finally:
            db.close()

        # 尝试导入登录测试模块
        try:
            logger.debug('Attempting to import login_tester module...')
            from login_tester import test_account_login
            selenium_available = True
            logger.info('login_tester module imported successfully')
        except ImportError as e:
            selenium_available = False
            logger.error(f'Failed to import login_tester: {e}', exc_info=True)
            logger.warning('Selenium not available, using mock login test')
        except Exception as e:
            selenium_available = False
            logger.error(f'Unexpected error importing login_tester: {e}', exc_info=True)

        # 如果Selenium可用，使用真实登录测试
        if selenium_available:
            try:
                logger.info(f'Starting real login test for {platform} - {username}')
                # 执行真实的登录测试
                result = test_account_login(platform, username, password, headless=True)
                test_success = result.get('success', False)
                message = result.get('message', '登录测试完成')
                current_url = result.get('current_url', '')

                logger.info(f'Login test completed - success: {test_success}, message: {message}')
                if current_url:
                    logger.debug(f'Login landed on URL: {current_url}')

                # 更新账号状态到数据库
                db = get_db_session()
                try:
                    account_to_update = db.query(PlatformAccount).get(account_id)
                    if account_to_update:
                        account_to_update.status = 'success' if test_success else 'failed'
                        account_to_update.last_tested = datetime.now()
                        db.commit()
                finally:
                    db.close()

                logger.info(f'Real login test result: {platform} - {username} - {"success" if test_success else "failed"}')

                return jsonify({
                    'success': test_success,
                    'message': message,
                    'current_url': current_url
                })

            except Exception as e:
                logger.error(f'Selenium login test exception: {type(e).__name__}: {str(e)}', exc_info=True)
                logger.error(f'Exception details - Platform: {platform}, Username: {username}')
                # Selenium测试失败，回退到基本验证
                selenium_available = False

        # 如果Selenium不可用或失败，使用基本验证
        if not selenium_available:
            platform_urls = {
                '知乎': 'https://www.zhihu.com',
                'CSDN': 'https://www.csdn.net',
                '掘金': 'https://juejin.cn',
                '简书': 'https://www.jianshu.com',
                '今日头条': 'https://www.toutiao.com'
            }

            platform_url = platform_urls.get(platform, '')
            message = f'账号信息已保存。\n注意：自动登录测试需要安装 Selenium 和 Chrome。\n请手动访问 {platform_url} 验证账号。'

            # 更新为未知状态
            db = get_db_session()
            try:
                account_to_update = db.query(PlatformAccount).get(account_id)
                if account_to_update:
                    account_to_update.status = 'unknown'
                    account_to_update.last_tested = datetime.now()
                    db.commit()
            finally:
                db.close()

            return jsonify({
                'success': False,
                'message': message,
                'platform_url': platform_url
            })

    except Exception as e:
        logger.error(f'Test account failed: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/api/accounts/import', methods=['POST'])
@log_api_request("批量导入平台账号")
def import_accounts():
    """批量导入账号"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '没有文件被上传'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '文件名为空'}), 400

        filename_lower = file.filename.lower()
        if not (filename_lower.endswith('.json') or filename_lower.endswith('.txt') or filename_lower.endswith('.csv')):
            return jsonify({'success': False, 'error': '仅支持 JSON, TXT, CSV 格式'}), 400

        content = file.read().decode('utf-8', errors='ignore')

        imported_accounts = []

        if filename_lower.endswith('.json'):
            imported_accounts = json.loads(content)
        elif filename_lower.endswith('.csv'):
            lines = content.strip().split('\n')
            for i, line in enumerate(lines):
                if i == 0 and ('平台' in line or 'platform' in line.lower()):
                    continue
                parts = line.split(',')
                if len(parts) >= 2:
                    imported_accounts.append({
                        'platform': parts[0].strip(),
                        'username': parts[1].strip(),
                        'password': parts[2].strip() if len(parts) > 2 else '',
                        'notes': parts[3].strip() if len(parts) > 3 else ''
                    })
        else:
            lines = content.strip().split('\n')
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    imported_accounts.append({
                        'platform': parts[0],
                        'username': parts[1],
                        'password': parts[2] if len(parts) > 2 else '',
                        'notes': ' '.join(parts[3:]) if len(parts) > 3 else ''
                    })

        if not imported_accounts:
            return jsonify({'success': False, 'error': '没有找到有效的账号信息'}), 400

        accounts = load_accounts()
        start_id = max([acc.get('id', 0) for acc in accounts], default=0) + 1

        for i, acc in enumerate(imported_accounts):
            acc['id'] = start_id + i
            acc['created_at'] = datetime.now().isoformat()
            accounts.append(acc)

        if save_accounts(accounts):
            logger.info(f'Imported {len(imported_accounts)} accounts')
            return jsonify({
                'success': True,
                'count': len(imported_accounts),
                'accounts': accounts
            })
        else:
            return jsonify({'success': False, 'error': '保存失败'}), 500

    except json.JSONDecodeError as e:
        return jsonify({'success': False, 'error': f'JSON格式错误: {str(e)}'}), 400
    except Exception as e:
        logger.error(f'Import accounts failed: {e}', exc_info=True)
        return jsonify({'success': False, 'error': f'导入失败: {str(e)}'}), 500

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
# ============ CSDN 平台管理 ============
@api_bp.route('/api/csdn/login', methods=['POST'])
@login_required
def csdn_login():
    """CSDN账号密码登录"""
    try:
        user = get_current_user()
        data = request.json
        username = data.get('username', '')
        password = data.get('password', '')

        if not username or not password:
            return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400

        logger.info(f'CSDN login attempt for user: {user.username}, csdn account: {username}')

        # 导入CSDN发布器
        try:
            from publishers import PlatformPublisherFactory

            # 创建CSDN发布器实例
            publisher = PlatformPublisherFactory.create_publisher('csdn')

            # 执行登录
            success, message = publisher.login(username, password)

            # 关闭浏览器
            publisher.close()

            if success:
                logger.info(f'CSDN login successful for: {username}')
                return jsonify({
                    'success': True,
                    'message': 'CSDN登录成功，Cookie已保存'
                })
            else:
                logger.warning(f'CSDN login failed: {message}')
                return jsonify({
                    'success': False,
                    'message': f'登录失败: {message}'
                }), 400

        except ImportError as e:
            logger.error(f'Failed to import CSDN publisher: {e}')
            return jsonify({
                'success': False,
                'message': 'CSDN发布器模块未安装，请联系管理员'
            }), 500
        except Exception as e:
            logger.error(f'CSDN login error: {e}', exc_info=True)
            return jsonify({
                'success': False,
                'message': f'登录异常: {str(e)}'
            }), 500

    except Exception as e:
        logger.error(f'CSDN login handler failed: {e}', exc_info=True)
        return jsonify({'success': False, 'message': f'请求失败: {str(e)}'}), 500


@api_bp.route('/api/csdn/check_login', methods=['POST'])
@login_required
def csdn_check_login():
    """检查CSDN登录状态"""
    try:
        user = get_current_user()
        data = request.json
        username = data.get('username', '')

        if not username:
            return jsonify({'success': False, 'message': '用户名不能为空'}), 400

        # 导入CSDN发布器
        try:
            from publishers import PlatformPublisherFactory

            # 创建CSDN发布器实例
            publisher = PlatformPublisherFactory.create_publisher('csdn')

            # 检查Cookie是否存在
            cookie_exists = publisher.cookies_exist(username)

            if not cookie_exists:
                publisher.close()
                return jsonify({
                    'success': False,
                    'logged_in': False,
                    'message': 'Cookie不存在，请先登录'
                })

            # 加载Cookie并检查登录状态
            cookies = publisher.load_cookies(username)
            if cookies:
                # 这里可以进一步验证Cookie是否有效
                # 暂时返回Cookie存在即表示已登录
                publisher.close()
                return jsonify({
                    'success': True,
                    'logged_in': True,
                    'message': 'Cookie已加载'
                })
            else:
                publisher.close()
                return jsonify({
                    'success': False,
                    'logged_in': False,
                    'message': 'Cookie加载失败'
                })

        except Exception as e:
            logger.error(f'CSDN check login error: {e}', exc_info=True)
            return jsonify({
                'success': False,
                'logged_in': False,
                'message': f'检查登录状态失败: {str(e)}'
            }), 500

    except Exception as e:
        logger.error(f'CSDN check login handler failed: {e}', exc_info=True)
        return jsonify({'success': False, 'message': f'请求失败: {str(e)}'}), 500


@api_bp.route('/api/csdn/publish', methods=['POST'])
@login_required
@log_api_request("发布文章到CSDN")
def publish_csdn():
    """发布文章到CSDN"""
    try:
        user = get_current_user()
        data = request.json
        title = data.get('title', '')
        content = data.get('content', '')
        category = data.get('category', '其他')
        tags = data.get('tags', [])
        article_type = data.get('article_type', 'original')

        if not title or not content:
            return jsonify({'success': False, 'message': '标题和内容不能为空'}), 400

        logger.info(f'Publishing to CSDN: {title} for user {user.username}')

        # 获取用户的CSDN账号
        db = get_db_session()
        try:
            csdn_account = db.query(PlatformAccount).filter_by(
                user_id=user.id,
                platform='CSDN',
                status='active'
            ).first()

            if not csdn_account:
                return jsonify({
                    'success': False,
                    'message': '未找到已配置的CSDN账号，请先在账号管理中添加CSDN账号'
                }), 400

            username = csdn_account.username

        finally:
            db.close()

        # 导入CSDN发布器
        try:
            from publishers import PlatformPublisherFactory

            # 创建CSDN发布器实例
            publisher = PlatformPublisherFactory.create_publisher('csdn')

            # 加载Cookie
            cookies = publisher.load_cookies(username)
            if not cookies:
                publisher.close()
                return jsonify({
                    'success': False,
                    'message': 'Cookie不存在或已过期，请重新登录'
                }), 400

            # 执行发布
            success, message, article_url = publisher.publish_article(
                title=title,
                content=content,
                category=category,
                tags=tags,
                article_type=article_type
            )

            # 关闭浏览器
            publisher.close()

            # 保存发布历史到数据库
            db = get_db_session()
            try:
                publish_record = PublishHistory(
                    user_id=user.id,
                    platform='CSDN',
                    status='success' if success else 'failed',
                    url=article_url if success else '',
                    message=message
                )
                db.add(publish_record)
                db.commit()
            except:
                db.rollback()
            finally:
                db.close()

            if success:
                logger.info(f'CSDN publish successful: {article_url}')
                return jsonify({
                    'success': True,
                    'message': message,
                    'url': article_url
                })
            else:
                logger.warning(f'CSDN publish failed: {message}')
                return jsonify({
                    'success': False,
                    'message': message
                }), 400

        except ImportError as e:
            logger.error(f'Failed to import CSDN publisher: {e}')
            return jsonify({
                'success': False,
                'message': 'CSDN发布器模块未安装，请联系管理员'
            }), 500
        except Exception as e:
            logger.error(f'CSDN publish error: {e}', exc_info=True)

            # 记录发布失败
            db = get_db_session()
            try:
                publish_record = PublishHistory(
                    user_id=user.id,
                    platform='CSDN',
                    status='failed',
                    message=f'发布异常: {str(e)}'
                )
                db.add(publish_record)
                db.commit()
            except:
                db.rollback()
            finally:
                db.close()

            return jsonify({
                'success': False,
                'message': f'发布异常: {str(e)}'
            }), 500

    except Exception as e:
        logger.error(f'CSDN publish handler failed: {e}', exc_info=True)
        return jsonify({'success': False, 'message': f'请求失败: {str(e)}'}), 500
# ============ 平台管理 ============
@api_bp.route('/api/platforms', methods=['GET'])
@login_required
def get_platforms():
    """获取支持的发布平台列表"""
    try:
        from publishers import PlatformPublisherFactory

        platforms = PlatformPublisherFactory.get_supported_platforms()

        # 获取每个平台的详细信息
        platform_info = []
        for platform in platforms:
            try:
                info = PlatformPublisherFactory.get_platform_info(platform)
                platform_info.append({
                    'id': platform,
                    'name': info['name'],
                    'features': info.get('features', {})
                })
            except:
                continue

        return jsonify({
            'success': True,
            'platforms': platform_info
        })

    except Exception as e:
        logger.error(f'Get platforms failed: {e}', exc_info=True)
        return jsonify({'success': False, 'error': '获取平台列表失败'}), 500
