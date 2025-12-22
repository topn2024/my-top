from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from werkzeug.utils import secure_filename
from functools import wraps
import openai
import os
import json
from datetime import datetime
import sys
import logging
import requests

# 导入数据库和认证模块
from models import User, Workflow, Article, PlatformAccount, PublishHistory, get_db_session
from auth import hash_password, verify_password, create_user, authenticate_user, login_required, get_current_user, admin_required
from encryption import encrypt_password, decrypt_password
from database import get_db_context

# 导入统一日志配置
from logger_config import setup_logger, log_api_request, log_function_call

# 导入AI服务辅助函数
from services.ai_service import remove_markdown_and_ai_traces, AIService

# 配置日志
logger = setup_logger(__name__)

# 设置第三方库的日志级别
logging.getLogger('werkzeug').setLevel(logging.INFO)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('selenium').setLevel(logging.INFO)

# 条件导入文档处理库
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logger.warning("python-docx not available, .doc/.docx support disabled")

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("PyPDF2 not available, PDF support disabled")

app = Flask(__name__, template_folder='../templates', static_folder='../static')
CORS(app)

# Session配置（用于用户认证）
app.config['SECRET_KEY'] = os.environ.get('TOPN_SECRET_KEY', 'TopN_Secret_Key_2024_Please_Change_In_Production')
app.config['SESSION_COOKIE_NAME'] = 'topn_session'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24小时

# 千问API配置
# 使用 Chat Completion API (通过 requests 库直接调用)
QIANWEN_API_KEY = 'sk-f0a85d3e56a746509ec435af2446c67a'
QIANWEN_API_BASE = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
QIANWEN_CHAT_URL = f'{QIANWEN_API_BASE}/chat/completions'

# 配置
UPLOAD_FOLDER = '../uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'md'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# 创建必要的目录
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('../data', exist_ok=True)
os.makedirs('../accounts', exist_ok=True)

# 账号配置文件路径
ACCOUNTS_FILE = '../accounts/accounts.json'

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(filepath):
    """从文件中提取文本"""
    ext = filepath.rsplit('.', 1)[1].lower()

    try:
        if ext == 'txt' or ext == 'md':
            # 尝试多种编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin1']
            for encoding in encodings:
                try:
                    with open(filepath, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            return None

        elif ext == 'pdf':
            if not PDF_AVAILABLE:
                return None
            text = ''
            with open(filepath, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    text += page.extract_text() + '\n'
            return text.strip() if text.strip() else None

        elif ext in ['doc', 'docx']:
            if not DOCX_AVAILABLE:
                return None
            doc = Document(filepath)
            text = '\n'.join([para.text for para in doc.paragraphs])
            return text.strip() if text.strip() else None

        else:
            return None
    except Exception as e:
        logger.error(f"Error extracting text from {filepath}: {e}", exc_info=True)
        return None

@app.route('/')
def home():
    """公司主页"""
    return render_template('home.html')

@app.route('/platform')
def platform_index():
    """TOP_N平台 - 信息输入"""
    return render_template('input.html')

@app.route('/analysis')
def analysis():
    """分析页面"""
    return render_template('analysis.html')

@app.route('/articles')
def articles():
    """文章生成页面"""
    return render_template('articles.html')

@app.route('/publish')
def publish():
    """发布推广页面"""
    return render_template('publish.html')

@app.route('/templates')
@login_required
def templates_page():
    """提示词模板管理页面"""
    return render_template('template_management.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """处理文件上传"""
    try:
        if 'file' not in request.files:
            logger.error("No file in request")
            return jsonify({'success': False, 'error': '没有文件被上传'}), 400

        file = request.files['file']

        if file.filename == '':
            logger.error("Empty filename")
            return jsonify({'success': False, 'error': '文件名为空'}), 400

        logger.info(f"Uploading file: {file.filename}")

        if not allowed_file(file.filename):
            logger.error(f"Unsupported file type: {file.filename}")
            return jsonify({'success': False, 'error': f'不支持的文件格式，仅支持: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

        # 保存文件
        # 先获取原始文件名和扩展名
        original_filename = file.filename
        if '.' in original_filename:
            ext = original_filename.rsplit('.', 1)[1].lower()
        else:
            logger.error(f"File has no extension: {original_filename}")
            return jsonify({'success': False, 'error': '文件名没有扩展名'}), 400

        # 使用时间戳作为文件名，保留扩展名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        unique_filename = f"{timestamp}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        logger.info(f"File saved to: {filepath} (original: {original_filename})")

        # 提取文本
        text = extract_text_from_file(filepath)

        if text is None:
            # 根据文件类型提供更详细的错误信息
            ext = filepath.rsplit('.', 1)[1].lower()
            error_msg = ''
            if ext == 'pdf' and not PDF_AVAILABLE:
                error_msg = '服务器未安装PDF处理库，请使用TXT或MD格式'
            elif ext in ['doc', 'docx'] and not DOCX_AVAILABLE:
                error_msg = '服务器未安装Word文档处理库，请使用TXT或MD格式'
            else:
                error_msg = '无法提取文件内容，请检查文件格式或内容'

            logger.error(f"Text extraction failed for {filepath}: {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 500

        # 限制文本长度
        if len(text) > 10000:
            text = text[:10000] + '...'
            logger.info(f"Text truncated to 10000 chars")

        logger.info(f"File uploaded successfully: {original_filename}, text length: {len(text)}")
        return jsonify({
            'success': True,
            'text': text,
            'filename': original_filename
        })

    except Exception as e:
        logger.error(f"Exception in upload_file: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': f'文件上传失败: {str(e)}'}), 500

@app.route('/api/analyze', methods=['POST'])
@login_required
@log_api_request("分析公司信息")
def analyze_company():
    try:
        user = get_current_user()
        data = request.json
        company_name = data.get('company_name', '')
        company_desc = data.get('company_desc', '')
        uploaded_text = data.get('uploaded_text', '')
        uploaded_filename = data.get('uploaded_filename', '')
        workflow_id = data.get('workflow_id')

        if not company_name:
            return jsonify({'success': False, 'error': '请输入公司名称'}), 400

        prompt = f'''
请分析以下公司/产品信息：

公司/产品名称：{company_name}
描述信息：{company_desc}

请从以下维度进行分析：
1. 行业定位
2. 核心优势
3. 目标用户
4. 技术特点
5. 市场前景

请详细描述每个维度的分析结果。
'''

        # 使用 Chat Completion API (通过 requests 库)
        headers = {
            'Authorization': f'Bearer {QIANWEN_API_KEY}',
            'Content-Type': 'application/json'
        }

        payload = {
            'model': 'qwen-plus',
            'messages': [
                {'role': 'system', 'content': '你是一个专业的商业分析师，擅长分析公司和产品信息。'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.7,
            'max_tokens': 2000
        }

        logger.info(f'Calling Qianwen API for company analysis: {company_name}')
        response = requests.post(QIANWEN_CHAT_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()
        analysis = result['choices'][0]['message']['content'].strip()

        # 保存到数据库
        db = get_db_session()
        try:
            if workflow_id:
                workflow = db.query(Workflow).filter_by(
                    id=workflow_id,
                    user_id=user.id
                ).first()
                if workflow:
                    workflow.analysis = analysis
                    workflow.current_step = 2
            else:
                # 创建新工作流
                workflow = Workflow(
                    user_id=user.id,
                    company_name=company_name,
                    company_desc=company_desc,
                    uploaded_text=uploaded_text,
                    uploaded_filename=uploaded_filename,
                    analysis=analysis,
                    current_step=2
                )
                db.add(workflow)

            db.commit()
            workflow_id = workflow.id
        except Exception as e:
            db.rollback()
            logger.error(f'Failed to save workflow: {e}', exc_info=True)
        finally:
            db.close()

        logger.info(f'Analysis completed for: {company_name}')
        return jsonify({
            'success': True,
            'analysis': analysis,
            'company_name': company_name,
            'workflow_id': workflow_id
        })

    except requests.exceptions.RequestException as e:
        logger.error(f'API request failed: {str(e)}', exc_info=True)
        return jsonify({'success': False, 'error': f'API调用失败: {str(e)}'}), 500
    except Exception as e:
        logger.error(f'Analysis failed: {str(e)}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/generate_articles', methods=['POST'])
@login_required
@log_api_request("生成推广文章")
def generate_articles():
    try:
        user = get_current_user()
        data = request.json
        company_name = data.get("company_name", "")
        analysis = data.get("analysis", "")
        article_count = data.get("article_count", 3)
        workflow_id = data.get("workflow_id")

        if not company_name or not analysis:
            return jsonify({"success": False, "error": "缺少必要参数"}), 400

        # 使用AIService的并发版本生成文章
        from config import Config
        ai_service = AIService(Config)
        
        logger.info(f"Using concurrent article generation for {company_name}")
        articles = ai_service.generate_articles(company_name, analysis, article_count)

        # 保存到数据库
        db = get_db_session()
        try:
            if workflow_id:
                workflow = db.query(Workflow).filter_by(
                    id=workflow_id,
                    user_id=user.id
                ).first()

                if workflow:
                    # 删除旧文章
                    db.query(Article).filter_by(workflow_id=workflow.id).delete()

                    # 添加新文章
                    for i, art_data in enumerate(articles):
                        article = Article(
                            workflow_id=workflow.id,
                            title=art_data["title"],
                            content=art_data["content"],
                            article_type=art_data.get("type", ""),
                            article_order=i
                        )
                        db.add(article)

                    workflow.article_count = len(articles)
                    workflow.current_step = 3

                    db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to save articles: {e}", exc_info=True)
        finally:
            db.close()

        # 也保存到文件系统作为备份
        save_articles(company_name, articles)

        return jsonify({
            "success": True,
            "articles": articles
        })

    except Exception as e:
        logger.error(f"Generate articles failed: {e}", exc_info=True)
        return jsonify({"success": False, "error": f"生成文章失败: {str(e)}"}), 500

def save_articles(company_name, articles):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'../data/{company_name}_{timestamp}.json'

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            'company_name': company_name,
            'timestamp': timestamp,
            'articles': articles
        }, f, ensure_ascii=False, indent=2)

def load_accounts():
    """加载账号配置"""
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f'Failed to load accounts: {e}')
            return []
    return []

def save_accounts(accounts):
    """保存账号配置"""
    try:
        with open(ACCOUNTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(accounts, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f'Failed to save accounts: {e}')
        return False

@app.route('/api/accounts', methods=['GET'])
@login_required
@log_api_request("获取平台账号列表")
def get_accounts():
    """获取当前用户的所有账号配置"""
    try:
        user = get_current_user()
        db = get_db_session()

        try:
            accounts = db.query(PlatformAccount).filter_by(
                user_id=user.id
            ).all()

            return jsonify({
                'success': True,
                'accounts': [acc.to_dict() for acc in accounts]
            })
        finally:
            db.close()

    except Exception as e:
        logger.error(f'Get accounts failed: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/accounts', methods=['POST'])
@login_required
@log_api_request("添加平台账号")
def add_account():
    """添加新账号"""
    try:
        user = get_current_user()
        data = request.json
        platform = data.get('platform', '')
        username = data.get('username', '')
        password = data.get('password', '')
        notes = data.get('notes', '')

        if not platform or not username:
            return jsonify({'success': False, 'error': '平台和用户名不能为空'}), 400

        # 加密密码
        encrypted_password = encrypt_password(password) if password else ''

        db = get_db_session()

        try:
            # 检查是否已存在
            existing = db.query(PlatformAccount).filter_by(
                user_id=user.id,
                platform=platform,
                username=username
            ).first()

            if existing:
                return jsonify({'success': False, 'error': '该平台账号已存在'}), 400

            # 创建新账号
            new_account = PlatformAccount(
                user_id=user.id,
                platform=platform,
                username=username,
                password_encrypted=encrypted_password,
                notes=notes,
                status='active'
            )

            db.add(new_account)
            db.commit()

            logger.info(f'Account added: {platform} - {username} for user {user.username}')
            return jsonify({
                'success': True,
                'account': new_account.to_dict()
            })
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    except Exception as e:
        logger.error(f'Add account failed: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/accounts/<int:account_id>', methods=['DELETE'])
@login_required
@log_api_request("删除平台账号")
def delete_account(account_id):
    """删除账号"""
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

            db.delete(account)
            db.commit()

            logger.info(f'Account deleted: {account_id} by user {user.username}')
            return jsonify({'success': True})
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    except Exception as e:
        logger.error(f'Delete account failed: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/accounts/<int:account_id>/test', methods=['POST'])
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

@app.route('/api/accounts/import', methods=['POST'])
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

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'TOP_N Platform',
        'timestamp': datetime.now().isoformat()
    })
@app.route('/api/models', methods=['GET'])
def get_ai_models():
    """获取支持的AI模型列表"""
    try:
        from config import Config

        models = []
        for model_id, model_info in Config.SUPPORTED_MODELS.items():
            models.append({
                'id': model_id,
                'name': model_info['name'],
                'description': model_info['description'],
                'provider': model_info['provider'],
                'max_tokens': model_info['max_tokens']
            })

        return jsonify({
            'success': True,
            'models': models,
            'default': Config.DEFAULT_AI_MODEL
        })
    except Exception as e:
        logger.error(f'Error getting models: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'models': [],
            'default': 'glm-4-flash'
        }), 500



# ============= 认证API =============

@app.route('/login')
def login_page():
    """登录页面"""
    return render_template('login.html')


@app.route('/help')
def help_center():
    """帮助中心页面"""
    return render_template('help.html')


@app.route('/admin')
def admin_dashboard():
    """企业级管理控制台 - 仅管理员"""
    # 检查用户登录状态
    if not session.get('username'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    # 获取用户信息进行权限验证
    user_id = session.get('user_id')
    username = session.get('username', '')

    # 如果有用户ID，验证用户角色
    if user_id and username:
        try:
            db = get_db_session()
            user = db.query(User).filter_by(id=user_id, is_active=True).first()

            if user and user.username.lower() in ['admin', 'administrator', 'superuser', 'root']:
                return render_template('admin_dashboard.html')
            elif user:
                return jsonify({'success': False, 'message': '权限不足'}), 403

        except Exception as e:
            print(f"权限检查错误: {str(e)}")
            # 如果数据库查询失败，使用简单用户名检查作为后备
            if username.lower() in ['admin', 'administrator', 'superuser', 'root']:
                return render_template('admin_dashboard.html')
            else:
                return jsonify({'success': False, 'message': '权限不足'}), 403

    # 默认检查用户名（后备方案）
    if username and username.lower() in ['admin', 'administrator', 'superuser', 'root']:
        return render_template('admin_dashboard.html')

    return jsonify({'success': False, 'message': '权限不足'}), 403

@app.route('/api/auth/register', methods=['POST'])
@log_api_request("用户注册")
def register():
    """用户注册"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        full_name = data.get('full_name', '').strip()

        if not username or not email or not password:
            return jsonify({'success': False, 'error': '用户名、邮箱和密码不能为空'}), 400

        user, error = create_user(username, email, password, full_name)

        if error:
            return jsonify({'success': False, 'error': error}), 400

        # 自动登录
        session['user_id'] = user.id
        session['username'] = user.username
        session.permanent = True

        logger.info(f'User registered and logged in: {username}')
        return jsonify({
            'success': True,
            'user': user.to_dict()
        })

    except Exception as e:
        logger.error(f'Registration failed: {e}', exc_info=True)
        return jsonify({'success': False, 'error': '注册失败，请稍后重试'}), 500

@app.route('/api/auth/login', methods=['POST'])
@log_api_request("用户登录")
def login():
    """用户登录"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            return jsonify({'success': False, 'error': '用户名和密码不能为空'}), 400

        user = authenticate_user(username, password)

        if not user:
            return jsonify({'success': False, 'error': '用户名或密码错误'}), 401

        if not user.is_active:
            return jsonify({'success': False, 'error': '账号已被禁用'}), 403

        # 创建session
        session['user_id'] = user.id
        session['username'] = user.username
        session.permanent = True

        logger.info(f'User logged in: {username}')
        return jsonify({
            'success': True,
            'user': user.to_dict()
        })

    except Exception as e:
        logger.error(f'Login failed: {e}', exc_info=True)
        return jsonify({'success': False, 'error': '登录失败，请稍后重试'}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """用户登出"""
    try:
        username = session.get('username')
        session.clear()
        logger.info(f'User logged out: {username}')
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f'Logout failed: {e}', exc_info=True)
        return jsonify({'success': False, 'error': '登出失败'}), 500

@app.route('/api/auth/me', methods=['GET'])
@login_required
def get_current_user_info():
    """获取当前用户信息"""
    try:
        user = get_current_user()
        if user:
            return jsonify({
                'success': True,
                'user': user.to_dict()
            })
        else:
            return jsonify({'success': False, 'error': '未登录'}), 401
    except Exception as e:
        logger.error(f'Get current user failed: {e}', exc_info=True)
        return jsonify({'success': False, 'error': '获取用户信息失败'}), 500

# ============= 工作流API =============

@app.route('/api/workflow/current', methods=['GET'])
@login_required
@log_api_request("获取当前工作流")
def get_current_workflow():
    """获取用户当前工作流（最新的未完成工作流）"""
    try:
        user = get_current_user()
        db = get_db_session()

        try:
            # 查找最新的未完成工作流
            workflow = db.query(Workflow).filter_by(
                user_id=user.id,
                status='in_progress'
            ).order_by(Workflow.created_at.desc()).first()

            if workflow:
                # 加载相关文章
                articles = db.query(Article).filter_by(
                    workflow_id=workflow.id
                ).order_by(Article.article_order).all()

                workflow_dict = workflow.to_dict()
                workflow_dict['articles'] = [art.to_dict() for art in articles]

                return jsonify({
                    'success': True,
                    'workflow': workflow_dict
                })
            else:
                return jsonify({
                    'success': True,
                    'workflow': None
                })
        finally:
            db.close()

    except Exception as e:
        logger.error(f'Get current workflow failed: {e}', exc_info=True)
        return jsonify({'success': False, 'error': '获取工作流失败'}), 500

@app.route('/api/workflow/save', methods=['POST'])
@login_required
@log_api_request("保存工作流")
def save_workflow():
    """保存/更新工作流状态"""
    try:
        user = get_current_user()
        data = request.json

        workflow_id = data.get('id')
        company_name = data.get('company_name', '')
        company_desc = data.get('company_desc', '')
        uploaded_text = data.get('uploaded_text', '')
        uploaded_filename = data.get('uploaded_filename', '')
        analysis = data.get('analysis', '')
        article_count = data.get('article_count', 3)
        platforms = data.get('platforms', [])
        current_step = data.get('current_step', 1)
        status = data.get('status', 'in_progress')
        articles = data.get('articles', [])

        db = get_db_session()

        try:
            if workflow_id:
                # 更新现有工作流
                workflow = db.query(Workflow).filter_by(
                    id=workflow_id,
                    user_id=user.id
                ).first()

                if not workflow:
                    return jsonify({'success': False, 'error': '工作流不存在'}), 404

                workflow.company_name = company_name
                workflow.company_desc = company_desc
                workflow.uploaded_text = uploaded_text
                workflow.uploaded_filename = uploaded_filename
                workflow.analysis = analysis
                workflow.article_count = article_count
                workflow.platforms = platforms
                workflow.current_step = current_step
                workflow.status = status
            else:
                # 创建新工作流
                workflow = Workflow(
                    user_id=user.id,
                    company_name=company_name,
                    company_desc=company_desc,
                    uploaded_text=uploaded_text,
                    uploaded_filename=uploaded_filename,
                    analysis=analysis,
                    article_count=article_count,
                    platforms=platforms,
                    current_step=current_step,
                    status=status
                )
                db.add(workflow)
                db.flush()  # 获取workflow.id

            # 保存文章
            if articles:
                # 删除旧文章
                db.query(Article).filter_by(workflow_id=workflow.id).delete()

                # 添加新文章
                for i, art_data in enumerate(articles):
                    article = Article(
                        workflow_id=workflow.id,
                        title=art_data.get('title', ''),
                        content=art_data.get('content', ''),
                        article_type=art_data.get('type', ''),
                        article_order=i
                    )
                    db.add(article)

            db.commit()

            logger.info(f'Workflow saved: {workflow.id} for user {user.username}')
            return jsonify({
                'success': True,
                'workflow': workflow.to_dict()
            })

        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    except Exception as e:
        logger.error(f'Save workflow failed: {e}', exc_info=True)
        return jsonify({'success': False, 'error': '保存工作流失败'}), 500

@app.route('/api/workflow/list', methods=['GET'])
@login_required
@log_api_request("获取工作流列表")
def get_workflow_list():
    """获取用户所有工作流列表"""
    try:
        user = get_current_user()
        db = get_db_session()

        try:
            workflows = db.query(Workflow).filter_by(
                user_id=user.id
            ).order_by(Workflow.created_at.desc()).all()

            return jsonify({
                'success': True,
                'workflows': [wf.to_dict() for wf in workflows]
            })
        finally:
            db.close()

    except Exception as e:
        logger.error(f'Get workflow list failed: {e}', exc_info=True)
        return jsonify({'success': False, 'error': '获取工作流列表失败'}), 500

# ============= 发布API =============

@app.route('/api/publish_zhihu', methods=['POST'])
@login_required
@log_api_request("发布文章到知乎(旧版)")
def publish_zhihu():
    """发布文章到知乎"""
    try:
        user = get_current_user()
        data = request.json
        title = data.get('title', '')
        content = data.get('content', '')

        if not title or not content:
            return jsonify({'success': False, 'message': '标题和内容不能为空'}), 400

        logger.info(f'Publishing to Zhihu: {title} for user {user.username}')

        # 获取用户的知乎账号
        db = get_db_session()
        try:
            zhihu_account = db.query(PlatformAccount).filter_by(
                user_id=user.id,
                platform='知乎',
                status='active'
            ).first()

            if not zhihu_account:
                return jsonify({
                    'success': False,
                    'message': '未找到已配置的知乎账号，请先在账号管理中添加知乎账号'
                }), 400

            username = zhihu_account.username
            password = decrypt_password(zhihu_account.password_encrypted) if zhihu_account.password_encrypted else ''

            if not password:
                return jsonify({
                    'success': False,
                    'message': '知乎账号密码未设置，请在账号管理中完善信息'
                }), 400

        finally:
            db.close()

        # 尝试导入知乎发布模块
        try:
            logger.debug('Attempting to import zhihu_auto_post module...')
            from zhihu_auto_post_enhanced import post_article_to_zhihu
            zhihu_publisher_available = True
            logger.info('zhihu_auto_post module imported successfully')
        except ImportError as e:
            zhihu_publisher_available = False
            logger.error(f'Failed to import zhihu_auto_post: {e}', exc_info=True)
            logger.warning('Zhihu publisher not available, will return mock response')
        except Exception as e:
            zhihu_publisher_available = False
            logger.error(f'Unexpected error importing zhihu_auto_post: {e}', exc_info=True)

        # 如果发布模块可用，执行真实发布
        if zhihu_publisher_available:
            try:
                logger.info(f'Starting real publish to Zhihu for: {title}')
                # 增强版：支持Cookie登录，若Cookie不存在则自动使用密码登录
                result = post_article_to_zhihu(
                    username=username,
                    title=title,
                    content=content,
                    topics=None,
                    password=password,
                    draft=False
                )

                success = result.get('success', False)
                message = result.get('message', '发布完成')
                article_url = result.get('url', '')

                logger.info(f'Publish result: success={success}, message={message}')

                # 保存发布历史到数据库
                db = get_db_session()
                try:
                    publish_record = PublishHistory(
                        user_id=user.id,
                        platform='知乎',
                        status='success' if success else 'failed',
                        url=article_url if success else '',
                        message=message
                    )
                    db.add(publish_record)
                    db.commit()
                    logger.info(f'Publish history saved: {publish_record.id}')
                except Exception as e:
                    db.rollback()
                    logger.error(f'Failed to save publish history: {e}', exc_info=True)
                finally:
                    db.close()

                return jsonify({
                    'success': success,
                    'message': message,
                    'url': article_url
                })

            except Exception as e:
                logger.error(f'Zhihu publish exception: {type(e).__name__}: {str(e)}', exc_info=True)

                # 保存失败记录
                db = get_db_session()
                try:
                    publish_record = PublishHistory(
                        user_id=user.id,
                        platform='知乎',
                        status='failed',
                        message=f'发布失败: {str(e)}'
                    )
                    db.add(publish_record)
                    db.commit()
                except:
                    db.rollback()
                finally:
                    db.close()

                return jsonify({
                    'success': False,
                    'message': f'发布过程中发生错误: {str(e)}'
                }), 500

        # 如果发布模块不可用，返回提示信息
        else:
            message = '''知乎自动发布功能需要Cookie文件支持。

当前系统已安装相关依赖,但缺少知乎账号的Cookie文件。

请选择以下方式之一：
1. 手动复制文章内容，访问 https://www.zhihu.com/creator 发布
2. 联系管理员提供知乎账号Cookie文件以启用自动发布功能

文章标题：{}
文章内容已准备就绪。'''.format(title)

            logger.warning(f'Zhihu publisher not available for user {user.username}')

            # 记录为未发布状态
            db = get_db_session()
            try:
                publish_record = PublishHistory(
                    user_id=user.id,
                    platform='知乎',
                    status='pending',
                    message='等待手动发布（自动发布功能未启用）'
                )
                db.add(publish_record)
                db.commit()
            except:
                db.rollback()
            finally:
                db.close()

            return jsonify({
                'success': False,
                'message': message
            })

    except Exception as e:
        logger.error(f'Publish to Zhihu failed: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'message': f'发布失败: {str(e)}'
        }), 500

# 注意：/api/publish_history 路由已在 blueprints/api.py 中定义
# 该版本使用 PublishService，支持从多个表聚合数据

@app.route('/api/retry_publish/<int:history_id>', methods=['POST'])
@login_required
@log_api_request("重试发布文章")
def retry_publish(history_id):
    """重试发布失败的文章"""
    try:
        user = get_current_user()
        db = get_db_session()

        try:
            # 获取发布历史记录
            history = db.query(PublishHistory).filter_by(
                id=history_id,
                user_id=user.id  # 确保只能重试自己的记录
            ).first()

            if not history:
                return jsonify({'success': False, 'error': '发布记录不存在'}), 404

            # 检查平台
            if history.platform != '知乎':
                return jsonify({'success': False, 'error': f'暂不支持重试{history.platform}平台'}), 400

            # 准备重新发布
            title = history.article_title
            content = history.article_content
            article_id = history.article_id

            # 如果有关联文章，从文章中获取内容
            if history.article:
                title = history.article.title
                content = history.article.content
                article_id = history.article.id
            elif not content:
                # 临时发布的文章且没有内容，无法重试
                return jsonify({
                    'success': False,
                    'error': '该记录无可用内容，无法重试。请重新选择文章发布'
                }), 400

            logger.info(f'Retry publishing article: {title} to 知乎 (history_id={history_id}) for user {user.username}')

        finally:
            db.close()

        # 导入知乎发布模块
        try:
            from zhihu_auto_post_enhanced import post_article_to_zhihu
            zhihu_publisher_available = True
        except ImportError as e:
            logger.error(f'Failed to import zhihu_auto_post: {e}', exc_info=True)
            return jsonify({
                'success': False,
                'error': '知乎发布模块不可用，请联系管理员'
            }), 500

        # 获取用户的知乎账号
        db = get_db_session()
        try:
            zhihu_account = db.query(PlatformAccount).filter_by(
                user_id=user.id,
                platform='知乎',
                status='active'
            ).first()

            if not zhihu_account:
                return jsonify({
                    'success': False,
                    'error': '未找到已配置的知乎账号，请先在账号管理中添加知乎账号'
                }), 400

            username = zhihu_account.username
            password = decrypt_password(zhihu_account.password_encrypted) if zhihu_account.password_encrypted else ''

            if not password:
                return jsonify({
                    'success': False,
                    'error': '知乎账号密码未设置，请在账号管理中完善信息'
                }), 400

        finally:
            db.close()

        # 执行发布
        try:
            result = post_article_to_zhihu(
                username=username,
                title=title,
                content=content,
                topics=None,
                password=password,
                draft=False
            )

            success = result.get('success', False)
            message = result.get('message', '重新发布完成')
            article_url = result.get('url', '')

            # 保存发布历史到数据库
            db = get_db_session()
            try:
                publish_record = PublishHistory(
                    user_id=user.id,
                    article_id=article_id,
                    article_title=title,
                    article_content=content,
                    platform='知乎',
                    status='success' if success else 'failed',
                    url=article_url if success else '',
                    message=message
                )
                db.add(publish_record)
                db.commit()
                logger.info(f'Retry publish history saved: {publish_record.id}')
            except Exception as e:
                db.rollback()
                logger.error(f'Failed to save retry publish history: {e}', exc_info=True)
            finally:
                db.close()

            if success:
                return jsonify({
                    'success': True,
                    'message': message or '重新发布成功',
                    'url': article_url
                })
            else:
                return jsonify({
                    'success': False,
                    'error': message or '重新发布失败'
                }), 500

        except Exception as e:
            logger.error(f'Zhihu retry publish exception: {type(e).__name__}: {str(e)}', exc_info=True)

            # 保存失败记录
            db = get_db_session()
            try:
                publish_record = PublishHistory(
                    user_id=user.id,
                    article_id=article_id,
                    article_title=title,
                    article_content=content,
                    platform='知乎',
                    status='failed',
                    message=f'重新发布失败: {str(e)}'
                )
                db.add(publish_record)
                db.commit()
            except:
                db.rollback()
            finally:
                db.close()

            return jsonify({
                'success': False,
                'error': f'重新发布过程中发生错误: {str(e)}'
            }), 500

    except Exception as e:
        logger.error(f'Retry publish failed: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': f'重新发布失败: {str(e)}'
        }), 500

# ============= CSDN发布API =============

@app.route('/api/csdn/login', methods=['POST'])
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


@app.route('/api/csdn/check_login', methods=['POST'])
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


@app.route('/api/csdn/publish', methods=['POST'])
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


@app.route('/api/platforms', methods=['GET'])
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

# 注册API蓝图
try:
    from blueprints.api import api_bp
    app.register_blueprint(api_bp)
    logger.info('API blueprint registered')
except Exception as e:
    logger.error(f'Failed to register API blueprint: {e}', exc_info=True)

# 注册提示词模板API蓝图
try:
    from blueprints.prompt_template_api import bp as prompt_template_bp
    app.register_blueprint(prompt_template_bp)
    logger.info('Prompt template API blueprint registered')
except Exception as e:
    logger.error(f'Failed to register prompt template blueprint: {e}', exc_info=True)

if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    app.run(host='0.0.0.0', port=port, debug=True)
