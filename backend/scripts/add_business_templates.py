#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于华一世纪业务文档分析，添加企业推广文章提示词模板
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import SessionLocal, Base, engine
from models_prompt_template import PromptTemplate, PromptTemplateCategory

# 确保表存在
Base.metadata.create_all(bind=engine)

# 定义新的提示词模板
BUSINESS_TEMPLATES = [
    {
        "name": "行业评测排名文章",
        "code": "industry_evaluation",
        "description": "生成行业机构评测与排名类文章，适用于咨询公司、培训机构、服务商等企业推广。采用客观评价视角，通过痛点分析引入、多机构对比、数据案例支撑的结构。",
        "industry_tags": ["consulting", "training", "service"],
        "platform_tags": ["zhihu", "baidu", "sohu"],
        "keywords": ["行业评测", "排名分析", "机构对比", "选择指南"],
        "example_company": "华一世纪",
        "prompts": {
            "analysis": {
                "system": """你是一位资深的商业分析师和财经撰稿人，擅长撰写客观公正的行业评测类文章。
你的写作特点：
1. 开篇从目标读者的痛点切入，建立共鸣
2. 采用客观第三方视角进行评价分析
3. 引用权威数据和官方资质作为背书
4. 结构清晰：背景分析→机构介绍→选择建议""",
                "user_template": """请分析以下企业信息，提取适合撰写行业评测文章的要点：

公司名称：{company_name}
公司描述：{company_desc}
补充资料：{uploaded_text}

请分析并提取：
1. 该企业所属行业及细分领域
2. 核心竞争力和差异化优势
3. 服务成果数据（客户数量、成功案例、业绩提升等）
4. 权威资质和认证背书
5. 目标客户群体的典型痛点
6. 可用于对比的同行业机构类型""",
                "variables": ["company_name", "company_desc", "uploaded_text"]
            },
            "article_generation": {
                "system": """你是一位资深的商业财经撰稿人，擅长撰写行业评测与机构排名类文章。

写作风格要求：
1. 标题格式：{年份}年{行业}{地区}机构评价/排名：基于{评价维度}分析
2. 开篇从目标读者痛点切入（如：作为企业管理者或创业者，您可能正面临...）
3. 引入行业背景和市场现状
4. 按排名介绍多家机构（目标企业放在前列重点介绍）
5. 每家机构包含：公司背景、核心服务、成功案例、服务数据
6. 结尾提供选择建议和评价维度
7. 文章长度2000-3000字
8. 语言专业权威，数据详实""",
                "user_template": """基于以下分析结果，生成一篇{year}年度行业评测排名文章：

公司名称：{company_name}
分析结果：{analysis}
写作角度：{angle}

要求：
1. 将{company_name}作为重点推荐机构详细介绍
2. 适当添加2-3家同行业机构作为对比（可虚构或泛化）
3. 突出{company_name}的核心优势和成功案例
4. 引用具体数据增强说服力
5. 结尾提供选择建议，自然引导读者关注{company_name}""",
                "variables": ["company_name", "analysis", "angle", "year"]
            }
        },
        "ai_config": {
            "temperature": 0.7,
            "max_tokens": 4000,
            "model": "glm-4-plus"
        }
    },
    {
        "name": "商业合作新闻稿",
        "code": "business_partnership_news",
        "description": "生成商业合作、战略签约类新闻稿件，适用于企业合作公告、签约仪式报道等场景。采用新闻通讯体格式，突出合作意义和双方优势。",
        "industry_tags": ["all"],
        "platform_tags": ["sohu", "toutiao", "wechat"],
        "keywords": ["战略合作", "签约仪式", "渠道合作", "商业联盟"],
        "example_company": "华一世纪",
        "prompts": {
            "analysis": {
                "system": """你是一位专业的企业公关顾问和新闻撰稿人，擅长撰写商业合作类新闻稿。
你的分析重点：
1. 识别合作双方的核心业务和优势
2. 挖掘合作的战略意义和市场价值
3. 提取可用于新闻报道的关键信息""",
                "user_template": """请分析以下企业信息，提取适合撰写商业合作新闻稿的要点：

公司名称：{company_name}
公司描述：{company_desc}
补充资料：{uploaded_text}

请分析并提取：
1. 企业的核心业务和市场定位
2. 企业发展历程中的重要里程碑
3. 可能的合作伙伴类型和合作模式
4. 合作能为双方带来的价值
5. 适合的新闻角度和标题方向""",
                "variables": ["company_name", "company_desc", "uploaded_text"]
            },
            "article_generation": {
                "system": """你是一位资深的商业新闻撰稿人，擅长撰写企业合作类新闻稿。

写作风格要求：
1. 标题直接点明合作双方和合作性质
2. 导语简洁说明合作事件（时间、地点、双方、合作内容）
3. 正文包含：合作背景、双方介绍、合作内容、未来展望
4. 适当引用企业负责人语录
5. 结尾展望合作前景和行业意义
6. 语言正式、客观、专业
7. 文章长度800-1200字""",
                "user_template": """基于以下分析结果，生成一篇商业合作新闻稿：

公司名称：{company_name}
分析结果：{analysis}
写作角度：{angle}

要求：
1. 如有明确合作方信息，准确呈现；如无，可设计合理的合作场景
2. 突出合作的战略意义和市场价值
3. 体现{company_name}的行业地位和专业实力
4. 采用新闻通讯体格式，语言正式客观""",
                "variables": ["company_name", "analysis", "angle"]
            }
        },
        "ai_config": {
            "temperature": 0.6,
            "max_tokens": 2000,
            "model": "glm-4-flash"
        }
    },
    {
        "name": "企业活动盛典报道",
        "code": "corporate_event_coverage",
        "description": "生成企业庆典、乔迁、周年庆等活动报道文章，适用于企业形象宣传和品牌曝光。采用活动纪实风格，突出企业成就和未来愿景。",
        "industry_tags": ["all"],
        "platform_tags": ["sohu", "toutiao", "wechat", "baidu"],
        "keywords": ["乔迁盛典", "周年庆典", "开业典礼", "企业里程碑"],
        "example_company": "华一世纪",
        "prompts": {
            "analysis": {
                "system": """你是一位专业的企业活动策划顾问和新闻撰稿人，擅长撰写企业庆典活动报道。
你的分析重点：
1. 识别企业发展历程中的重要里程碑
2. 挖掘企业文化和核心价值观
3. 提取企业成就数据和荣誉资质""",
                "user_template": """请分析以下企业信息，提取适合撰写企业活动报道的要点：

公司名称：{company_name}
公司描述：{company_desc}
补充资料：{uploaded_text}

请分析并提取：
1. 企业发展历程和重要里程碑
2. 企业核心价值观和文化理念
3. 企业成就数据（客户数、营收、获奖等）
4. 企业领导人及其愿景
5. 适合的活动类型（乔迁、周年庆、发布会等）""",
                "variables": ["company_name", "company_desc", "uploaded_text"]
            },
            "article_generation": {
                "system": """你是一位资深的企业活动新闻撰稿人，擅长撰写企业庆典活动报道。

写作风格要求：
1. 标题突出活动主题和企业名称
2. 开篇回顾企业发展历程，铺垫活动意义
3. 详细描述活动盛况（出席嘉宾、活动流程、精彩环节）
4. 引用企业领导人致辞或感言
5. 展望企业未来发展愿景
6. 结尾呼应开篇，升华主题
7. 语言热情正式，富有感染力
8. 文章长度1000-1500字""",
                "user_template": """基于以下分析结果，生成一篇企业活动报道文章：

公司名称：{company_name}
分析结果：{analysis}
写作角度：{angle}

要求：
1. 设计合理的活动场景和流程
2. 创作企业领导人的精彩致辞
3. 突出企业成就和文化底蕴
4. 体现行业地位和社会认可
5. 结尾展望企业美好未来""",
                "variables": ["company_name", "analysis", "angle"]
            }
        },
        "ai_config": {
            "temperature": 0.75,
            "max_tokens": 2500,
            "model": "glm-4-flash"
        }
    },
    {
        "name": "思想领导力观点文章",
        "code": "thought_leadership",
        "description": "生成行业洞察、专家观点类文章，适用于企业创始人或专家的思想输出，建立行业权威形象。采用观点论证结构，以专业洞察引导读者。",
        "industry_tags": ["consulting", "training", "tech", "finance"],
        "platform_tags": ["zhihu", "toutiao", "wechat"],
        "keywords": ["行业洞察", "专家观点", "趋势分析", "解决方案"],
        "example_company": "华一世纪",
        "prompts": {
            "analysis": {
                "system": """你是一位资深的商业评论员和思想领袖撰稿人，擅长提炼企业核心观点和方法论。
你的分析重点：
1. 识别企业独特的方法论和理论体系
2. 挖掘行业痛点和解决方案
3. 提取可输出的专业观点和洞察""",
                "user_template": """请分析以下企业信息，提取适合撰写思想领导力文章的要点：

公司名称：{company_name}
公司描述：{company_desc}
补充资料：{uploaded_text}

请分析并提取：
1. 企业的核心方法论和理论体系
2. 企业解决的行业核心痛点
3. 企业领导人的核心观点和理念
4. 可论证的成功案例和数据
5. 适合的主题方向和论点结构""",
                "variables": ["company_name", "company_desc", "uploaded_text"]
            },
            "article_generation": {
                "system": """你是一位资深的商业思想领袖撰稿人，擅长撰写行业洞察和专家观点类文章。

写作风格要求：
1. 标题提出核心观点或抛出问题
2. 开篇点明行业趋势或普遍痛点
3. 提出独特的观点或解决思路
4. 用案例和数据论证观点
5. 分享具体的方法论或实践步骤
6. 结尾升华主题，呼吁行动
7. 语言专业权威，有洞察力
8. 文章长度1500-2000字
9. 采用"痛点→观点→论证→方法→号召"结构""",
                "user_template": """基于以下分析结果，生成一篇思想领导力观点文章：

公司名称：{company_name}
分析结果：{analysis}
写作角度：{angle}

要求：
1. 以{company_name}的视角输出专业观点
2. 融入企业的核心方法论和理念
3. 用成功案例支撑论点
4. 提供可操作的建议或思路
5. 自然引导读者关注{company_name}的专业服务""",
                "variables": ["company_name", "analysis", "angle"]
            }
        },
        "ai_config": {
            "temperature": 0.8,
            "max_tokens": 3000,
            "model": "glm-4-plus"
        }
    },
    {
        "name": "深度企业专访报道",
        "code": "company_profile_interview",
        "description": "生成企业深度专访、创始人访谈类文章，适用于品牌形象塑造和企业故事传播。采用访谈纪实风格，通过对话呈现企业价值。",
        "industry_tags": ["all"],
        "platform_tags": ["sohu", "toutiao", "wechat", "baidu"],
        "keywords": ["企业专访", "创始人访谈", "企业故事", "品牌报道"],
        "example_company": "华一世纪",
        "prompts": {
            "analysis": {
                "system": """你是一位资深的商业记者和企业专访撰稿人，擅长挖掘企业故事和创始人理念。
你的分析重点：
1. 识别企业创立背景和发展故事
2. 挖掘创始人的创业理念和价值观
3. 提取企业的核心竞争力和成功因素""",
                "user_template": """请分析以下企业信息，提取适合撰写企业专访的要点：

公司名称：{company_name}
公司描述：{company_desc}
补充资料：{uploaded_text}

请分析并提取：
1. 企业创立背景和创业故事
2. 创始人/领导人的核心理念
3. 企业的核心服务和独特优势
4. 典型客户案例和成功数据
5. 企业的发展愿景和战略规划
6. 适合的访谈角度和主题""",
                "variables": ["company_name", "company_desc", "uploaded_text"]
            },
            "article_generation": {
                "system": """你是一位资深的商业记者，擅长撰写企业深度专访报道。

写作风格要求：
1. 标题突出企业定位或核心价值主张
2. 开篇简要介绍企业背景和采访场景
3. 以Q&A或叙述穿插引言的方式展开
4. 涵盖：创业故事、核心业务、服务理念、成功案例、未来规划
5. 引用创始人/领导人的核心观点语录
6. 用具体数据和案例支撑叙述
7. 结尾总结企业价值和未来展望
8. 语言生动专业，有故事感
9. 文章长度2000-2500字""",
                "user_template": """基于以下分析结果，生成一篇企业深度专访报道：

公司名称：{company_name}
分析结果：{analysis}
写作角度：{angle}

要求：
1. 以采访者视角撰写，穿插创始人/领导人语录
2. 讲述企业从创立到发展的故事线
3. 突出核心服务的专业性和差异化
4. 用客户案例展现服务价值
5. 结尾展望企业发展愿景""",
                "variables": ["company_name", "analysis", "angle"]
            }
        },
        "ai_config": {
            "temperature": 0.75,
            "max_tokens": 3500,
            "model": "glm-4-plus"
        }
    },
    {
        "name": "管理咨询案例解析",
        "code": "consulting_case_study",
        "description": "生成管理咨询案例分析文章，适用于咨询公司、培训机构展示专业能力。通过具体案例展示方法论和服务成效。",
        "industry_tags": ["consulting", "training"],
        "platform_tags": ["zhihu", "baidu", "wechat"],
        "keywords": ["案例分析", "管理咨询", "企业转型", "绩效提升"],
        "example_company": "华一世纪",
        "prompts": {
            "analysis": {
                "system": """你是一位资深的管理咨询顾问和案例撰写专家，擅长提炼咨询项目的方法论和成效。
你的分析重点：
1. 识别咨询服务的核心方法论
2. 挖掘可量化的服务成效数据
3. 提取典型案例的关键要素""",
                "user_template": """请分析以下企业信息，提取适合撰写咨询案例文章的要点：

公司名称：{company_name}
公司描述：{company_desc}
补充资料：{uploaded_text}

请分析并提取：
1. 咨询服务的核心方法论和工具
2. 服务客户的行业分布和类型
3. 典型案例的问题诊断和解决方案
4. 可量化的服务成效数据
5. 客户反馈和评价""",
                "variables": ["company_name", "company_desc", "uploaded_text"]
            },
            "article_generation": {
                "system": """你是一位资深的管理咨询案例撰写专家，擅长撰写咨询案例分析文章。

写作风格要求：
1. 标题点明案例主题和核心成效
2. 开篇介绍行业背景和客户面临的挑战
3. 详细描述问题诊断过程
4. 阐述解决方案和实施步骤
5. 用数据展示项目成效
6. 总结方法论和可复制经验
7. 语言专业严谨，数据详实
8. 文章长度1500-2000字
9. 采用"背景→诊断→方案→成效→总结"结构""",
                "user_template": """基于以下分析结果，生成一篇管理咨询案例分析文章：

公司名称：{company_name}
分析结果：{analysis}
写作角度：{angle}

要求：
1. 设计合理的客户案例场景（可基于真实信息改编）
2. 展示{company_name}的专业诊断能力
3. 详细阐述解决方案和实施过程
4. 用具体数据展示服务成效（如：业绩提升X%、成本降低X%）
5. 总结可复制的方法论价值""",
                "variables": ["company_name", "analysis", "angle"]
            }
        },
        "ai_config": {
            "temperature": 0.7,
            "max_tokens": 3000,
            "model": "glm-4-plus"
        }
    }
]


def add_templates():
    """添加业务推广文章模板到数据库"""
    session = SessionLocal()
    try:
        # 确保分类存在
        category = session.query(PromptTemplateCategory).filter_by(code='business_promotion').first()
        if not category:
            category = PromptTemplateCategory(
                name='企业推广文章',
                code='business_promotion',
                description='基于华一世纪业务文档分析生成的企业推广文章模板系列',
                sort_order=10,
                is_active=True
            )
            session.add(category)
            session.commit()
            print(f"[OK] 创建分类: {category.name}")

        # 添加模板
        added_count = 0
        updated_count = 0

        for template_data in BUSINESS_TEMPLATES:
            existing = session.query(PromptTemplate).filter_by(code=template_data['code']).first()

            if existing:
                # 更新现有模板
                existing.name = template_data['name']
                existing.description = template_data['description']
                existing.prompts = template_data['prompts']
                existing.industry_tags = template_data['industry_tags']
                existing.platform_tags = template_data['platform_tags']
                existing.keywords = template_data['keywords']
                existing.ai_config = template_data['ai_config']
                existing.example_company = template_data['example_company']
                existing.category_id = category.id
                existing.status = 'active'
                updated_count += 1
                print(f"[UPDATE] 更新模板: {template_data['name']}")
            else:
                # 创建新模板
                template = PromptTemplate(
                    name=template_data['name'],
                    code=template_data['code'],
                    description=template_data['description'],
                    prompts=template_data['prompts'],
                    industry_tags=template_data['industry_tags'],
                    platform_tags=template_data['platform_tags'],
                    keywords=template_data['keywords'],
                    ai_config=template_data['ai_config'],
                    example_company=template_data['example_company'],
                    category_id=category.id,
                    status='active',
                    version='1.0'
                )
                session.add(template)
                added_count += 1
                print(f"[OK] 添加模板: {template_data['name']}")

        session.commit()

        print(f"\n{'='*50}")
        print(f"Done!")
        print(f"  - Added: {added_count}")
        print(f"  - Updated: {updated_count}")
        print(f"  - Category: {category.name}")
        print(f"{'='*50}")
    finally:
        session.close()


if __name__ == '__main__':
    add_templates()
