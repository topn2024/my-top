"""
AI服务模块
负责与千问API交互，处理分析和文章生成
"""
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger_config import setup_logger, log_service_call
import requests
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = setup_logger(__name__)


def remove_markdown_and_ai_traces(text):
    """移除Markdown格式和AI生成痕迹,使文章更像人类撰写"""
    import re

    # 移除Markdown标题
    text = re.sub(r'#{1,6}\s+', '', text)

    # 移除Markdown粗体和斜体
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)

    # 移除Markdown列表符号
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)

    # 移除AI生成常用套话
    ai_phrases = [
        '综上所述', '总的来说', '值得一提的是', '需要指出的是',
        '首先，', '其次，', '最后，', '另外，', '因此，'
    ]
    for phrase in ai_phrases:
        text = text.replace(phrase, '')

    return text.strip()


class AIService:
    """AI服务类，支持智谱AI和千问API"""

    def __init__(self, config):
        """
        初始化AI服务

        Args:
            config: 配置对象，包含API密钥和URL
        """
        # 保存config引用以便动态切换provider
        self.config = config
        # 获取默认 AI 服务商（与 config.py 保持一致，默认为 qianwen）
        self.provider = getattr(config, 'DEFAULT_AI_PROVIDER', 'qianwen')
        if self.provider == 'zhipu':
            # 使用智谱 AI
            self.api_key = config.ZHIPU_API_KEY
            self.api_base = config.ZHIPU_API_BASE
            self.chat_url = config.ZHIPU_CHAT_URL
            self.model = config.ZHIPU_MODEL
            logger.info('Using Zhipu AI as default provider')
        else:
            # 使用千问 AI（备用）
            self.api_key = config.QIANWEN_API_KEY
            self.api_base = config.QIANWEN_API_BASE
            self.chat_url = config.QIANWEN_CHAT_URL
            self.model = config.QIANWEN_MODEL
            logger.info('Using Qianwen AI as default provider')
    @log_service_call("AI API调用")
    def _call_api(self, messages: List[Dict], temperature: float = 0.7,
                  max_tokens: int = 2000, timeout: int = 60, model: Optional[str] = None) -> Optional[str]:
        """
        调用千问API
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            timeout: 超时时间(秒)
            model: 指定使用的模型（可选，默认使用self.model）
        Returns:
            API返回的文本内容，失败返回None
        """
        try:
            # 使用传入的model参数，如果没有则使用默认的self.model
            actual_model = model if model else self.model
            # 根据model参数动态选择provider和API配置
            api_key = self.api_key
            chat_url = self.chat_url
            current_provider = self.provider
            if model and hasattr(self.config, 'SUPPORTED_MODELS'):
                model_config = self.config.SUPPORTED_MODELS.get(model)
                if model_config:
                    model_provider = model_config.get('provider')
                    if model_provider == 'qianwen':
                        # 使用千问API
                        api_key = self.config.QIANWEN_API_KEY
                        chat_url = self.config.QIANWEN_CHAT_URL
                        current_provider = 'qianwen'
                        logger.info(f'Switched to Qianwen provider for model: {model}')
                    elif model_provider == 'zhipu':
                        # 使用智谱API
                        api_key = self.config.ZHIPU_API_KEY
                        chat_url = self.config.ZHIPU_CHAT_URL
                        current_provider = 'zhipu'
                        logger.info(f'Switched to Zhipu provider for model: {model}')
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            payload = {
                'model': actual_model,
                'messages': messages,
                'temperature': temperature,
                'max_tokens': max_tokens
            }
            logger.info(f'Calling {current_provider.upper()} API with model: {actual_model} (requested: {model}, default: {self.model})')
            response = requests.post(chat_url, headers=headers,
                                   json=payload, timeout=timeout)
            response.raise_for_status()
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            logger.info(f'{current_provider.upper()} API call successful with model: {actual_model}')
            return content
        except requests.exceptions.RequestException as e:
            logger.error(f'API request failed: {e}', exc_info=True)
            raise
        except Exception as e:
            logger.error(f'Unexpected error in API call: {e}', exc_info=True)
            raise
    @log_service_call("分析公司信息")
    def analyze_company(self, company_name: str, company_desc: str,
                       uploaded_text: str = '', model: Optional[str] = None) -> str:
        """
        分析公司/产品信息
        Args:
            company_name: 公司/产品名称
            company_desc: 公司/产品描述
            uploaded_text: 上传的文档内容(可选)
            model: 指定使用的AI模型（可选）
        Returns:
            分析结果文本
        Raises:
            Exception: API调用失败时抛出异常
        """
        # 构建提示词
        info_text = f"公司/产品名称：{company_name}\n描述信息：{company_desc}"
        if uploaded_text:
            info_text += f"\n\n补充资料：\n{uploaded_text}"
        prompt = f'''
请分析以下公司/产品信息：
{info_text}
请从以下维度进行分析：
1. 行业定位
2. 核心优势
3. 目标用户
4. 技术特点
5. 市场前景
请详细描述每个维度的分析结果。
'''
        messages = [
            {'role': 'system', 'content': '你是一个专业的商业分析师，擅长分析公司和产品信息。'},
            {'role': 'user', 'content': prompt}
        ]
        logger.info(f'Analyzing company: {company_name}, model: {model or "default"}')
        return self._call_api(messages, temperature=0.7, max_tokens=2000, model=model)
    def _generate_single_article(self, company_name: str, analysis: str,
                                angle: str, index: int, total: int) -> Dict:
        """
        生成单篇文章（用于并发调用）
        Args:
            company_name: 公司/产品名称
            analysis: 分析结果
            angle: 文章角度
            index: 文章序号
            total: 总文章数
        Returns:
            文章字典
        """
        try:
            prompt = f'''
基于以下分析结果，为"{company_name}"撰写一篇推广文章。
分析结果：
{analysis}
要求：
1. 重点突出：{angle}
2. 篇幅适中（800-1500字）
3. 标题吸引人且自然，避免过度营销
4. 内容专业且易懂
5. **重要**：使用真实的网络发帖风格，模仿人类写作习惯：
   - 不要使用Markdown格式（如#标题、**粗体**、列表符号等）
   - 避免过于工整的结构和AI常用套话
   - 语言要口语化、自然流畅
   - 可以有适当的个人观点和情感表达
   - 适合在知乎、CSDN等平台直接发布
请直接返回标题和正文，格式如下：
标题：[这里是标题]
正文：
[这里是正文内容]
'''
            messages = [
                {'role': 'system', 'content': '你是一个专业的内容创作者，擅长撰写技术和商业推广文章。'},
                {'role': 'user', 'content': prompt}
            ]
            logger.info(f'Generating article {index+1}/{total} ({angle}) for {company_name}')
            content = self._call_api(messages, temperature=0.8, max_tokens=3000)
            # 解析标题和正文
            title, body = self._parse_article(content)
            # 清理markdown格式和AI痕迹
            if body:
                body = remove_markdown_and_ai_traces(body)
            article = {
                'title': title or f'{company_name} - {angle}相关内容',
                'content': body or content,
                'type': angle,
                'index': index  # 保存索引以便排序
            }
            logger.info(f'Article {index+1} ({angle}) generated successfully')
            return article
        except Exception as e:
            logger.error(f'Failed to generate article {index+1} ({angle}): {e}', exc_info=True)
            return None
    @log_service_call("生成推广文章")
    def generate_articles(self, company_name: str, analysis: str,
                         article_count: int = 3) -> List[Dict]:
        """
        基于分析结果并发生成推广文章
        Args:
            company_name: 公司/产品名称
            analysis: 分析结果
            article_count: 要生成的文章数量
        Returns:
            文章列表，每篇文章包含title和content
        Raises:
            Exception: API调用失败时抛出异常
        """
        # 定义文章角度
        angles = [
            "技术创新",
            "行业应用",
            "用户价值",
            "市场趋势",
            "案例分析"
        ]
        # 使用线程池并发生成文章
        articles = []
        with ThreadPoolExecutor(max_workers=article_count) as executor:
            # 提交所有任务
            future_to_index = {}
            for i in range(article_count):
                angle = angles[i % len(angles)]
                future = executor.submit(
                    self._generate_single_article,
                    company_name, analysis, angle, i, article_count
                )
                future_to_index[future] = i
            # 收集结果
            for future in as_completed(future_to_index):
                article = future.result()
                if article:
                    articles.append(article)
        # 按索引排序以保持顺序
        articles.sort(key=lambda x: x['index'])
        # 移除索引字段
        for article in articles:
            article.pop('index', None)
        logger.info(f'Successfully generated {len(articles)}/{article_count} articles')
        return articles
    def _parse_article(self, content: str) -> tuple:
        """
        解析文章内容，提取标题和正文
        Args:
            content: API返回的内容
        Returns:
            (标题, 正文) 元组
        """
        lines = content.split('\n')
        title = ''
        body_lines = []
        body_started = False
        for line in lines:
            line = line.strip()
            if not title and line.startswith('标题：'):
                title = line.replace('标题：', '').strip()
            elif line.startswith('正文：'):
                body_started = True
            elif body_started or (title and not line.startswith('标题：')):
                body_lines.append(line)
        body = '\n'.join(body_lines).strip()
        # 如果没有找到标题，尝试将第一行作为标题
        if not title and body_lines:
            potential_title = body_lines[0].strip()
            if len(potential_title) < 100:  # 假设标题不会太长
                title = potential_title
                body = '\n'.join(body_lines[1:]).strip()
        return title, body
    def recommend_platforms(self, company_name: str, analysis: str,
                           articles: List[Dict]) -> List[Dict]:
        """
        推荐发布平台
        Args:
            company_name: 公司/产品名称
            analysis: 分析结果
            articles: 生成的文章列表
        Returns:
            推荐平台列表
        Raises:
            Exception: API调用失败时抛出异常
        """
        prompt = f'''
基于以下公司分析和文章内容，推荐最适合的发布平台。
公司：{company_name}
分析：{analysis}
文章数量：{len(articles)}
请推荐3-5个最适合的平台，并说明推荐理由。
可选平台包括：知乎、CSDN、掘金、思否、简书、微信公众号等。
请按以下格式返回：
平台：[平台名称]
理由：[推荐理由]
'''
        messages = [
            {'role': 'system', 'content': '你是一个内容运营专家，擅长根据内容特点推荐合适的发布平台。'},
            {'role': 'user', 'content': prompt}
        ]
        logger.info(f'Recommending platforms for {company_name}')
        content = self._call_api(messages, temperature=0.6, max_tokens=1000)
        # 解析推荐结果
        platforms = self._parse_platforms(content)
        return platforms
    def _parse_platforms(self, content: str) -> List[Dict]:
        """
        解析平台推荐结果
        Args:
            content: API返回的内容
        Returns:
            平台列表，每个平台包含name和reason
        """
        platforms = []
        lines = content.split('\n')
        current_platform = None
        current_reason = []
        for line in lines:
            line = line.strip()
            if line.startswith('平台：'):
                if current_platform:
                    platforms.append({
                        'name': current_platform,
                        'reason': '\n'.join(current_reason).strip()
                    })
                current_platform = line.replace('平台：', '').strip()
                current_reason = []
            elif line.startswith('理由：'):
                current_reason.append(line.replace('理由：', '').strip())
            elif current_platform and line:
                current_reason.append(line)
        # 添加最后一个平台
        if current_platform:
            platforms.append({
                'name': current_platform,
                'reason': '\n'.join(current_reason).strip()
            })
        return platforms
    def render_prompt_template(self, template_str: str, variables: Dict) -> str:
        """
        渲染提示词模板，替换变量
        Args:
            template_str: 模板字符串，使用{{variable}}格式
            variables: 变量字典
        Returns:
            渲染后的提示词
        """
        import re
        from datetime import datetime
        result = template_str
        # 添加常用默认变量
        variables = {"year": str(datetime.now().year), "current_year": str(datetime.now().year), **variables}
        for key, value in variables.items():
            # 支持 {{variable}} 格式
            result = result.replace(f'{{{{{key}}}}}', str(value or ''))
            # 支持 {variable} 单大括号格式
            result = result.replace(f'{{{key}}}', str(value or ''))
            # 支持 {% if variable %} 简单条件
            if_pattern = f'{{%\s*if\s+{key}\s*%}}(.*?){{%\s*endif\s*%}}'
            if value:
                result = re.sub(if_pattern, r'\1', result, flags=re.DOTALL)
            else:
                result = re.sub(if_pattern, '', result, flags=re.DOTALL)

        # 清理剩余未定义的占位符
        result = re.sub(r'\{\{[a-zA-Z_][a-zA-Z0-9_]*\}\}', '', result)
        result = re.sub(r'\{[a-zA-Z_][a-zA-Z0-9_]*\}', '', result)
        return result.strip()
    @log_service_call("使用模板分析公司")
    def analyze_company_with_template(self, company_info: Dict, template: Dict, model: Optional[str] = None) -> str:
        """
        使用指定模板分析公司信息
        Args:
            company_info: 公司信息字典
            template: 模板字典（包含prompts字段）
            model: 指定使用的AI模型（可选）
        Returns:
            分析结果
        """
        # 从模板中获取提示词
        analysis_prompts = template.get('prompts', {}).get('analysis', {})
        if not analysis_prompts:
            # 如果没有analysis提示词，使用默认方法
            return self.analyze_company(
                company_info.get('company_name', ''),
                company_info.get('company_desc', ''),
                company_info.get('uploaded_text', ''),
                model=model
            )
        # 渲染用户提示词模板
        user_prompt = self.render_prompt_template(
            analysis_prompts.get('user_template', ''),
            {
                'company_name': company_info.get('company_name', ''),
                'company_desc': company_info.get('company_desc', ''),
                'uploaded_text': company_info.get('uploaded_text', '')
            }
        )
        # 使用模板中的AI配置
        ai_config = template.get('ai_config', {})
        messages = [
            {'role': 'system', 'content': analysis_prompts.get('system', '')},
            {'role': 'user', 'content': user_prompt}
        ]
        logger.info(f'Using template for analysis: {template.get("name", "unknown")}, model: {model or "default"}')
        return self._call_api(
            messages,
            temperature=ai_config.get('temperature', 0.7),
            max_tokens=ai_config.get('max_tokens', 2000),
            model=model
        )
    @log_service_call("使用模板生成文章")
    def generate_articles_with_template(self, company_name: str, analysis: str,
                                       template: Dict, article_count: int = 3) -> List[Dict]:
        """
        使用指定模板生成文章
        Args:
            company_name: 公司名称
            analysis: 分析结果
            template: 模板字典
            article_count: 文章数量
        Returns:
            文章列表
        """
        # 从模板中获取提示词
        generation_prompts = template.get('prompts', {}).get('article_generation', {})
        if not generation_prompts:
            # 如果没有generation提示词，使用默认方法
            return self.generate_articles(company_name, analysis, article_count)
        # 定义文章角度
        angles = [
            "技术创新",
            "行业应用",
            "用户价值",
            "市场趋势",
            "案例分析"
        ]
        # AI配置
        ai_config = template.get('ai_config', {})
        # 使用线程池并发生成文章
        articles = []
        with ThreadPoolExecutor(max_workers=article_count) as executor:
            future_to_index = {}
            for i in range(article_count):
                angle = angles[i % len(angles)]
                future = executor.submit(
                    self._generate_single_article_with_template,
                    company_name, analysis, angle, i, article_count,
                    generation_prompts, ai_config
                )
                future_to_index[future] = i
            # 收集结果
            for future in as_completed(future_to_index):
                article = future.result()
                if article:
                    articles.append(article)
        # 按索引排序
        articles.sort(key=lambda x: x.get('index', 0))
        # 移除索引字段
        for article in articles:
            article.pop('index', None)
        logger.info(f'Successfully generated {len(articles)}/{article_count} articles using template')
        return articles
    def _generate_single_article_with_template(self, company_name: str, analysis: str,
                                              angle: str, index: int, total: int,
                                              generation_prompts: Dict, ai_config: Dict) -> Dict:
        """使用模板生成单篇文章"""
        try:
            # 渲染用户提示词
            user_prompt = self.render_prompt_template(
                generation_prompts.get('user_template', ''),
                {
                    'company_name': company_name,
                    'analysis': analysis,
                    'angle': angle
                }
            )
            messages = [
                {'role': 'system', 'content': generation_prompts.get('system', '')},
                {'role': 'user', 'content': user_prompt}
            ]
            logger.info(f'Generating article {index+1}/{total} ({angle}) using template')
            content = self._call_api(
                messages,
                temperature=ai_config.get('temperature', 0.8),
                max_tokens=ai_config.get('max_tokens', 3000)
            )
            # 解析标题和正文
            title, body = self._parse_article(content)
            # 清理markdown格式
            if body:
                body = remove_markdown_and_ai_traces(body)
            article = {
                'title': title or f'{company_name} - {angle}相关内容',
                'content': body or content,
                'type': angle,
                'index': index
            }
            logger.info(f'Article {index+1} ({angle}) generated successfully')
            return article
        except Exception as e:
            logger.error(f'Failed to generate article {index+1} ({angle}): {e}', exc_info=True)
            return None
