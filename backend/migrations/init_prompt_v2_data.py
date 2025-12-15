#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化三模块提示词系统默认数据
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from models import SessionLocal
import json


def init_default_data():
    """初始化默认提示词数据"""
    session = SessionLocal()

    try:
        print('开始初始化默认数据...')

        # 1. 创建默认分析提示词
        print('\n1. 创建默认分析提示词...')

        analysis_prompts = [
            {
                'name': '科技公司深度分析',
                'code': 'tech_deep_analysis',
                'description': '适用于科技类公司的深度分析，关注技术创新、市场定位和发展潜力',
                'system_prompt': '你是一个资深的科技行业分析师，擅长分析科技公司的技术能力、市场定位和发展潜力。你的分析应该深入、客观、有数据支撑。',
                'user_template': '''请深入分析以下科技公司/产品：

公司/产品名称：{{company_name}}
描述信息：{{company_desc}}
{% if uploaded_text %}补充资料：
{{uploaded_text}}{% endif %}

请从以下维度进行分析：
1. 技术创新点和核心竞争力
2. 目标用户群体和市场定位
3. 行业地位和发展前景
4. 潜在挑战和风险
5. 推荐营销角度

请提供结构化、专业的分析报告。''',
                'variables': json.dumps(['company_name', 'company_desc', 'uploaded_text']),
                'temperature': 0.7,
                'max_tokens': 2000,
                'industry_tags': json.dumps(['tech', 'ai', 'saas']),
                'status': 'active',
                'is_default': True
            },
            {
                'name': '通用企业分析',
                'code': 'general_business_analysis',
                'description': '适用于各类企业的通用分析模板',
                'system_prompt': '你是一位经验丰富的商业分析师，能够从多个角度分析企业的商业价值和市场机会。',
                'user_template': '''请分析以下企业：

企业名称：{{company_name}}
企业描述：{{company_desc}}
{% if uploaded_text %}详细信息：
{{uploaded_text}}{% endif %}

分析维度：
1. 业务模式和核心价值
2. 目标客户群体
3. 市场竞争优势
4. 发展机遇和挑战

请提供清晰、实用的分析结果。''',
                'variables': json.dumps(['company_name', 'company_desc', 'uploaded_text']),
                'temperature': 0.7,
                'max_tokens': 2000,
                'industry_tags': json.dumps(['general']),
                'status': 'active',
                'is_default': False
            }
        ]

        for prompt in analysis_prompts:
            # 检查是否已存在
            result = session.execute(
                text("SELECT id FROM analysis_prompts WHERE code = :code"),
                {'code': prompt['code']}
            )
            if result.fetchone():
                print(f"  - {prompt['name']} 已存在，跳过")
                continue

            session.execute(text("""
                INSERT INTO analysis_prompts (
                    name, code, description, system_prompt, user_template,
                    variables, temperature, max_tokens, industry_tags, status, is_default
                ) VALUES (
                    :name, :code, :description, :system_prompt, :user_template,
                    :variables, :temperature, :max_tokens, :industry_tags, :status, :is_default
                )
            """), prompt)
            print(f"  [OK] Created: {prompt['name']}")

        # 2. 创建默认文章生成提示词
        print('\n2. 创建默认文章生成提示词...')

        article_prompts = [
            {
                'name': '技术博客生成器',
                'code': 'tech_blog_generator',
                'description': '生成专业、深度的技术博客文章',
                'system_prompt': '你是一位优秀的技术博客作者，擅长将复杂的技术概念用清晰、引人入胜的方式表达出来。你的文章既有深度又有可读性。',
                'user_template': '''基于以下分析结果，撰写一篇技术博客文章：

公司名称：{{company_name}}
分析结果：{{analysis}}
文章角度：{{angle}}

要求：
1. 标题吸引人且专业
2. 内容结构清晰，使用小标题
3. 适当引用数据和案例
4. 字数1500-2500字
5. 突出技术亮点和创新价值

请生成完整的文章（包括标题和正文）。''',
                'variables': json.dumps(['company_name', 'analysis', 'angle']),
                'default_angles': json.dumps(['技术创新', '行业应用', '用户价值', '发展趋势']),
                'temperature': 0.8,
                'max_tokens': 3000,
                'industry_tags': json.dumps(['tech']),
                'style_tags': json.dumps(['专业', '深度']),
                'status': 'active',
                'is_default': True
            },
            {
                'name': '营销软文生成器',
                'code': 'marketing_article_generator',
                'description': '生成营销导向的推广文章',
                'system_prompt': '你是一位营销文案专家，擅长创作既有信息价值又有营销效果的文章。',
                'user_template': '''基于以下信息，创作一篇营销推广文章：

公司名称：{{company_name}}
分析结果：{{analysis}}
推广角度：{{angle}}

要求：
1. 标题具有吸引力
2. 突出产品/服务优势
3. 包含用户痛点和解决方案
4. 自然融入品牌信息
5. 字数1000-2000字

请生成文章。''',
                'variables': json.dumps(['company_name', 'analysis', 'angle']),
                'default_angles': json.dumps(['解决方案', '成功案例', '行业洞察']),
                'temperature': 0.8,
                'max_tokens': 3000,
                'industry_tags': json.dumps(['general']),
                'style_tags': json.dumps(['营销', '软文']),
                'status': 'active',
                'is_default': False
            }
        ]

        for prompt in article_prompts:
            result = session.execute(
                text("SELECT id FROM article_prompts WHERE code = :code"),
                {'code': prompt['code']}
            )
            if result.fetchone():
                print(f"  - {prompt['name']} 已存在，跳过")
                continue

            session.execute(text("""
                INSERT INTO article_prompts (
                    name, code, description, system_prompt, user_template,
                    variables, default_angles, temperature, max_tokens,
                    industry_tags, style_tags, status, is_default
                ) VALUES (
                    :name, :code, :description, :system_prompt, :user_template,
                    :variables, :default_angles, :temperature, :max_tokens,
                    :industry_tags, :style_tags, :status, :is_default
                )
            """), prompt)
            print(f"  [OK] Created: {prompt['name']}")

        # 3. 创建平台风格提示词
        print('\n3. 创建平台风格提示词...')

        platform_styles = [
            {
                'name': '知乎专业深度风格',
                'code': 'zhihu_professional',
                'platform': 'zhihu',
                'platform_display_name': '知乎',
                'description': '知乎用户重视专业性、逻辑性和数据支撑的深度内容',
                'system_prompt': '''你是知乎高赞回答者。知乎用户的特点：
- 重视专业性和逻辑严密性
- 喜欢有数据支撑的内容
- 欣赏深度分析和独到见解
- 反感过度营销

写作要求：
1. 使用清晰的标题结构（一级、二级标题）
2. 段落间保持适当空行
3. 适当引用数据、研究或案例
4. 保持客观理性的论述
5. 避免夸张宣传
6. 字数1500-3000字''',
                'user_template': '''请将以下文章转换为知乎专业风格：

原标题：{{title}}
原内容：{{content}}

转换要求：
1. 保持核心信息和观点
2. 增强专业性和逻辑性
3. 添加适当的数据支撑
4. 优化标题和结构
5. 使用知乎适合的表达方式

请输出转换后的文章（包括标题和正文）。''',
                'variables': json.dumps(['title', 'content', 'platform']),
                'style_features': json.dumps({
                    'tone': '专业深度',
                    'paragraph_length': '中等（3-5句）',
                    'use_data': True,
                    'use_emoji': False,
                    'typical_length': '1500-3000字'
                }),
                'temperature': 0.7,
                'max_tokens': 3000,
                'apply_stage': 'both',
                'status': 'active',
                'is_default': True
            },
            {
                'name': 'CSDN技术教程风格',
                'code': 'csdn_tutorial',
                'platform': 'csdn',
                'platform_display_name': 'CSDN',
                'description': 'CSDN用户需要清晰的技术教程和代码示例',
                'system_prompt': '''你是CSDN技术博主。CSDN用户的特点：
- 需要实用的技术教程
- 重视代码示例和步骤说明
- 关注技术细节和最佳实践

写作要求：
1. 步骤清晰，便于跟随
2. 提供代码示例（如适用）
3. 标注重点和注意事项
4. 使用Markdown格式
5. 字数800-2000字''',
                'user_template': '''请将以下文章改写为CSDN技术教程风格：

原标题：{{title}}
原内容：{{content}}

改写要求：
1. 增加步骤说明
2. 添加代码示例（如适用）
3. 标注技术要点
4. 使用清晰的小标题
5. 适合技术人员阅读

请输出改写后的文章。''',
                'variables': json.dumps(['title', 'content']),
                'style_features': json.dumps({
                    'tone': '技术教程',
                    'use_code_examples': True,
                    'step_by_step': True,
                    'typical_length': '800-2000字'
                }),
                'temperature': 0.7,
                'max_tokens': 3000,
                'apply_stage': 'both',
                'status': 'active',
                'is_default': True
            },
            {
                'name': '掘金前端技术风格',
                'code': 'juejin_frontend',
                'platform': 'juejin',
                'platform_display_name': '掘金',
                'description': '掘金用户喜欢简洁明快、技术前沿的内容',
                'system_prompt': '''你是掘金技术作者。掘金用户的特点：
- 关注前沿技术和最佳实践
- 喜欢简洁明快的表达
- 重视代码质量和性能

写作要求：
1. 简洁有力的表达
2. 突出技术亮点
3. 代码格式规范
4. 适当使用技术术语
5. 字数1000-2500字''',
                'user_template': '''请将以下文章改写为掘金技术风格：

原标题：{{title}}
原内容：{{content}}

改写要求：
1. 简化表达，去除冗余
2. 突出技术创新点
3. 优化代码示例
4. 使用技术社区惯用表达

请输出改写后的文章。''',
                'variables': json.dumps(['title', 'content']),
                'style_features': json.dumps({
                    'tone': '前端技术',
                    'concise': True,
                    'code_highlight': True,
                    'typical_length': '1000-2500字'
                }),
                'temperature': 0.7,
                'max_tokens': 3000,
                'apply_stage': 'both',
                'status': 'active',
                'is_default': True
            },
            {
                'name': '小红书种草分享风格',
                'code': 'xiaohongshu_share',
                'platform': 'xiaohongshu',
                'platform_display_name': '小红书',
                'description': '小红书用户喜欢轻松活泼、真实分享的内容',
                'system_prompt': '''你是小红书博主。小红书用户的特点：
- 喜欢轻松活泼的表达
- 重视真实体验和感受
- 喜欢使用emoji表情
- 关注实用价值

写作要求：
1. 使用emoji表情增加活力
2. 短句分段，易于阅读
3. 第一人称分享视角
4. 添加3-5个话题标签
5. 字数300-800字''',
                'user_template': '''请将以下文章改写为小红书种草笔记：

原标题：{{title}}
原内容：{{content}}

改写要求：
1. 轻松活泼的语气
2. 多使用emoji表情
3. 短句分段
4. 加入个人体验感受
5. 添加话题标签（#话题#）
6. 保持真实自然

请输出改写后的笔记（标题要简短有吸引力，20字以内）。''',
                'variables': json.dumps(['title', 'content']),
                'style_features': json.dumps({
                    'tone': '轻松种草',
                    'paragraph_length': '短（1-2句）',
                    'use_emoji': True,
                    'use_hashtags': True,
                    'typical_length': '300-800字',
                    'max_title_length': 20
                }),
                'temperature': 0.7,
                'max_tokens': 3000,
                'apply_stage': 'both',
                'status': 'active',
                'is_default': True
            }
        ]

        for style in platform_styles:
            result = session.execute(
                text("SELECT id FROM platform_style_prompts WHERE code = :code"),
                {'code': style['code']}
            )
            if result.fetchone():
                print(f"  - {style['name']} 已存在，跳过")
                continue

            session.execute(text("""
                INSERT INTO platform_style_prompts (
                    name, code, description, platform, platform_display_name,
                    system_prompt, user_template, variables, style_features,
                    temperature, max_tokens, apply_stage, status, is_default
                ) VALUES (
                    :name, :code, :description, :platform, :platform_display_name,
                    :system_prompt, :user_template, :variables, :style_features,
                    :temperature, :max_tokens, :apply_stage, :status, :is_default
                )
            """), style)
            print(f"  [OK] Created: {style['name']}")

        session.commit()
        print('\n[SUCCESS] 默认数据初始化完成')
        return True

    except Exception as e:
        session.rollback()
        print(f'\n[ERROR] 初始化失败: {e}')
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


if __name__ == '__main__':
    print('=' * 60)
    print('三模块提示词系统 - 初始化默认数据')
    print('=' * 60)
    print()

    success = init_default_data()

    if success:
        print('\n[OK] 初始化成功！')
        print('\n已创建的默认数据：')
        print('- 2个分析提示词（科技公司深度分析、通用企业分析）')
        print('- 2个文章提示词（技术博客生成器、营销软文生成器）')
        print('- 4个平台风格（知乎、CSDN、掘金、小红书）')
    else:
        print('\n[ERROR] 初始化失败，请检查错误信息')

    print('=' * 60)
