from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import openai
import os
import json
from datetime import datetime

app = Flask(__name__, template_folder='../templates', static_folder='../static')
CORS(app)

# 千问API配置 (使用旧版 API，兼容 Python 3.6 / openai<1.0)
# 注意：openai 0.8.0 会自动在 api_base 后添加 /v1/completions
# 所以这里不要包含 /v1，否则会变成 /v1/v1/completions 导致404
openai.api_key = "sk-f0a85d3e56a746509ec435af2446c67a"
openai.api_base = "https://dashscope.aliyuncs.com/compatible-mode"

# 数据目录
DATA_DIR = "../data"
os.makedirs(DATA_DIR, exist_ok=True)

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze_company():
    """分析公司/产品信息"""
    try:
        data = request.json
        company_name = data.get('company_name', '')
        company_desc = data.get('company_desc', '')

        if not company_name:
            return jsonify({'error': '请输入公司名称'}), 400

        # 使用千问分析公司信息
        prompt = f"""
请分析以下公司/产品信息：

公司/产品名称：{company_name}
描述信息：{company_desc}

请从以下维度进行分析：
1. 行业定位
2. 核心优势
3. 目标用户
4. 技术特点
5. 市场前景

请以JSON格式返回分析结果。
"""

        # 使用 Completion API (旧版本 openai 0.9.x)
        full_prompt = "你是一个专业的商业分析师，擅长分析公司和产品信息。\n\n" + prompt
        response = openai.Completion.create(
            model="qwen-plus",
            prompt=full_prompt,
            temperature=0.7,
            max_tokens=2000
        )

        analysis = response.choices[0].text.strip()

        return jsonify({
            'success': True,
            'analysis': analysis,
            'company_name': company_name
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate_articles', methods=['POST'])
def generate_articles():
    """生成推广文章"""
    try:
        data = request.json
        company_name = data.get('company_name', '')
        analysis = data.get('analysis', '')
        article_count = data.get('article_count', 3)

        if not company_name or not analysis:
            return jsonify({'error': '缺少必要参数'}), 400

        articles = []

        # 不同角度的文章类型
        article_types = [
            "技术创新角度的深度分析文章",
            "用户体验角度的评测文章",
            "行业对比角度的专业评论",
            "未来发展趋势的前瞻分析",
            "实际应用场景的案例分享"
        ]

        for i in range(min(article_count, len(article_types))):
            prompt = f"""
基于以下分析信息，撰写一篇关于 {company_name} 的{article_types[i]}：

{analysis}

要求：
1. 文章长度800-1200字
2. 突出公司/产品的核心优势
3. 语言专业且易懂
4. 包含具体案例或数据支撑
5. 标题要吸引人
6. 适合发布到知乎、CSDN等平台

请以JSON格式返回，包含title和content字段。
"""

            # 使用 Completion API (旧版本 openai 0.9.x)
            full_prompt = "你是一个专业的科技文章撰写者。\n\n" + prompt
            response = openai.Completion.create(
                model="qwen-plus",
                prompt=full_prompt,
                temperature=0.8,
                max_tokens=2000
            )

            article_text = response.choices[0].text.strip()

            # 尝试解析JSON，如果失败则使用原文
            try:
                article_data = json.loads(article_text)
                title = article_data.get('title', f'{company_name} - {article_types[i]}')
                content = article_data.get('content', article_text)
            except:
                title = f'{company_name} - {article_types[i]}'
                content = article_text

            articles.append({
                'id': i + 1,
                'title': title,
                'content': content,
                'type': article_types[i],
                'created_at': datetime.now().isoformat()
            })

        # 保存到文件
        save_articles(company_name, articles)

        return jsonify({
            'success': True,
            'articles': articles
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/platforms', methods=['GET'])
def get_platforms():
    """获取推荐发布平台"""
    platforms = [
        {
            'name': '知乎',
            'url': 'https://www.zhihu.com',
            'description': '高质量问答社区，适合深度分析文章',
            'tips': '建议以问答形式发布，增加互动性'
        },
        {
            'name': 'CSDN',
            'url': 'https://www.csdn.net',
            'description': '技术博客平台，适合技术类文章',
            'tips': '添加技术标签，便于搜索引擎收录'
        },
        {
            'name': '掘金',
            'url': 'https://juejin.cn',
            'description': '开发者社区，适合技术分享',
            'tips': '使用Markdown格式，添加代码示例'
        },
        {
            'name': '简书',
            'url': 'https://www.jianshu.com',
            'description': '综合内容平台，适合各类文章',
            'tips': '选择合适的专题投稿'
        },
        {
            'name': '今日头条',
            'url': 'https://www.toutiao.com',
            'description': '资讯平台，流量大',
            'tips': '标题要吸引眼球，增加曝光度'
        }
    ]

    return jsonify({
        'success': True,
        'platforms': platforms
    })

def save_articles(company_name, articles):
    """保存文章到文件"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{DATA_DIR}/{company_name}_{timestamp}.json"

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            'company_name': company_name,
            'timestamp': timestamp,
            'articles': articles
        }, f, ensure_ascii=False, indent=2)

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'service': 'TOP_N Platform',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
