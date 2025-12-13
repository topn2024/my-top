#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提示词模板系统初始化脚本
完整初始化数据库和预置数据
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from models import Base, engine, SessionLocal, User
from models_prompt_template import (
    PromptTemplateCategory,
    PromptTemplate,
    PromptTemplateUsageLog,
    PromptTemplateAuditLog,
    PromptExampleLibrary
)
import logging
import json
from werkzeug.security import generate_password_hash

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def init_database():
    """初始化数据库"""
    logger.info("="*60)
    logger.info("提示词模板系统 - 数据库初始化")
    logger.info("="*60)

    try:
        # 1. 创建所有基础表
        logger.info("\n[1/6] 创建基础数据表...")
        Base.metadata.create_all(bind=engine)
        logger.info("   [OK] 基础表创建完成")

        # 2. 添加新字段到现有表
        logger.info("\n[2/6] 添加新字段到现有表...")
        session = SessionLocal()

        try:
            # 添加 User.role 字段
            try:
                session.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user'"))
                session.commit()
                logger.info("   [OK] User.role 字段添加成功")
            except Exception as e:
                if "duplicate" in str(e).lower() or "already exists" in str(e).lower():
                    logger.info("   [SKIP] User.role 字段已存在")
                else:
                    raise

            # 添加 Workflow 模板相关字段
            try:
                session.execute(text("ALTER TABLE workflows ADD COLUMN template_id INTEGER"))
                session.execute(text("ALTER TABLE workflows ADD COLUMN template_selection_method VARCHAR(20)"))
                session.commit()
                logger.info("   [OK] Workflow 模板字段添加成功")
            except Exception as e:
                if "duplicate" in str(e).lower() or "already exists" in str(e).lower():
                    logger.info("   [SKIP] Workflow 模板字段已存在")
                else:
                    raise

        finally:
            session.close()

        logger.info("   [OK] 字段迁移完成")

        return True

    except Exception as e:
        logger.error(f"\n[ERROR] 数据库初始化失败: {e}")
        return False


def create_admin_user():
    """创建管理员用户"""
    logger.info("\n[3/6] 创建管理员用户...")
    session = SessionLocal()

    try:
        # 检查是否已存在管理员
        admin = session.query(User).filter_by(username='admin').first()

        if admin:
            # 更新现有管理员角色
            admin.role = 'admin'
            session.commit()
            logger.info("   [OK] 管理员用户已存在，角色已更新")
        else:
            # 创建新管理员
            admin = User(
                username='admin',
                email='admin@topn.com',
                password_hash=generate_password_hash('TopN@2024'),
                full_name='System Administrator',
                role='admin',
                is_active=True
            )
            session.add(admin)
            session.commit()
            logger.info("   [OK] 管理员用户创建成功")
            logger.info("        用户名: admin")
            logger.info("        密码: TopN@2024")

        return True

    except Exception as e:
        session.rollback()
        logger.error(f"   [ERROR] 创建管理员失败: {e}")
        return False

    finally:
        session.close()


def init_categories():
    """初始化模板分类"""
    logger.info("\n[4/6] 初始化模板分类...")
    session = SessionLocal()

    categories = [
        # 顶层分类
        {'name': '行业', 'code': 'industry', 'parent_code': None, 'description': '按行业划分的模板分类'},
        {'name': '平台', 'code': 'platform', 'parent_code': None, 'description': '按发布平台划分的模板分类'},
        {'name': '目的', 'code': 'purpose', 'parent_code': None, 'description': '按推广目的划分的模板分类'},

        # 行业子分类
        {'name': '科技', 'code': 'tech', 'parent_code': 'industry'},
        {'name': '金融', 'code': 'finance', 'parent_code': 'industry'},
        {'name': '教育', 'code': 'education', 'parent_code': 'industry'},
        {'name': '医疗', 'code': 'healthcare', 'parent_code': 'industry'},
        {'name': '电商', 'code': 'ecommerce', 'parent_code': 'industry'},

        # 平台子分类
        {'name': '知乎', 'code': 'zhihu', 'parent_code': 'platform'},
        {'name': 'CSDN', 'code': 'csdn', 'parent_code': 'platform'},
        {'name': '掘金', 'code': 'juejin', 'parent_code': 'platform'},

        # 目的子分类
        {'name': '品牌宣传', 'code': 'brand', 'parent_code': 'purpose'},
        {'name': '产品推广', 'code': 'product', 'parent_code': 'purpose'},
        {'name': '技术分享', 'code': 'tech_share', 'parent_code': 'purpose'},
    ]

    try:
        created_count = 0
        parent_map = {}

        # 先创建顶层分类
        for cat_data in categories:
            if cat_data['parent_code'] is None:
                existing = session.query(PromptTemplateCategory).filter_by(code=cat_data['code']).first()
                if not existing:
                    cat = PromptTemplateCategory(
                        name=cat_data['name'],
                        code=cat_data['code'],
                        description=cat_data.get('description', ''),
                        parent_id=None,
                        sort_order=0
                    )
                    session.add(cat)
                    session.flush()
                    parent_map[cat_data['code']] = cat.id
                    created_count += 1
                else:
                    parent_map[cat_data['code']] = existing.id

        # 再创建子分类
        for cat_data in categories:
            if cat_data['parent_code'] is not None:
                existing = session.query(PromptTemplateCategory).filter_by(code=cat_data['code']).first()
                if not existing:
                    parent_id = parent_map.get(cat_data['parent_code'])
                    cat = PromptTemplateCategory(
                        name=cat_data['name'],
                        code=cat_data['code'],
                        description=cat_data.get('description', ''),
                        parent_id=parent_id,
                        sort_order=0
                    )
                    session.add(cat)
                    created_count += 1

        session.commit()
        logger.info(f"   [OK] 创建了 {created_count} 个分类")

        return True

    except Exception as e:
        session.rollback()
        logger.error(f"   [ERROR] 初始化分类失败: {e}")
        return False

    finally:
        session.close()


def init_example_library():
    """初始化样例库"""
    logger.info("\n[5/6] 初始化样例库...")
    session = SessionLocal()

    examples = [
        # 行业特征样例 - 科技
        {
            'title': '科技行业特征样例',
            'code': 'industry_tech_features',
            'type': 'industry_feature',
            'industry': 'tech',
            'platform': None,
            'stage': None,
            'description': '科技行业的分析维度、关键词和提示词样例',
            'is_recommended': True,
            'tags': ['推荐', '初学者友好'],
            'content': {
                'industry': 'tech',
                'features': {
                    'analysis_dimensions': [
                        '技术创新能力',
                        '研发投入和专利',
                        '产品技术架构',
                        '行业技术地位',
                        '未来技术路线'
                    ],
                    'focus_points': [
                        '核心技术栈',
                        '技术壁垒',
                        '创新突破点',
                        '技术团队实力',
                        '开源贡献'
                    ],
                    'keywords': [
                        '云计算', '人工智能', '大数据', '物联网', '5G',
                        '区块链', '边缘计算', '容器化', '微服务', 'DevOps'
                    ],
                    'tone': '专业、技术导向、数据支撑',
                    'avoid': ['过度吹捧', '缺乏技术细节', '空洞概念']
                },
                'example_prompts': [
                    {
                        'stage': 'analysis',
                        'prompt': '请深入分析该科技公司的技术实力，重点关注：\\n1. 核心技术栈和技术架构\\n2. 技术创新点和专利情况\\n3. 在行业内的技术地位\\n4. 研发团队规模和能力\\n5. 技术生态和开源贡献\\n\\n请提供具体的技术指标和数据支撑。',
                        'explanation': '科技公司需要突出技术实力，使用具体指标而非空泛描述'
                    }
                ]
            }
        },

        # 平台风格样例 - 知乎
        {
            'title': '知乎平台写作风格指南',
            'code': 'platform_zhihu_style',
            'type': 'platform_style',
            'industry': None,
            'platform': 'zhihu',
            'stage': None,
            'description': '知乎平台的写作要求、风格特点和注意事项',
            'is_recommended': True,
            'tags': ['推荐', '热门'],
            'content': {
                'platform': 'zhihu',
                'style_guide': {
                    'tone': '专业但不失亲和力，客观理性',
                    'perspective': '第一人称或第三人称客观视角',
                    'structure': [
                        '问题导入（引起共鸣）',
                        '背景介绍（建立认知）',
                        '深度分析（专业内容）',
                        '案例支撑（增强可信度）',
                        '总结展望（升华主题）'
                    ],
                    'length': '1500-3000字为佳',
                    'format': {
                        'paragraphs': '段落分明，每段3-5行',
                        'headings': '适当使用小标题分隔',
                        'lists': '可使用列表增强可读性',
                        'emphasis': '适度使用加粗强调关键点'
                    },
                    'language': {
                        'preferred': ['干货', '实战', '深度', '见解', '分析'],
                        'avoid': ['震惊', '必看', '绝对', '最强', '颠覆']
                    }
                },
                'dos_and_donts': {
                    'do': [
                        '提供有价值的信息和见解',
                        '用数据和事实支撑观点',
                        '保持客观和理性',
                        '展现专业性和深度',
                        '尊重不同观点'
                    ],
                    'dont': [
                        '过度营销和硬广',
                        '使用标题党',
                        '情绪化表达',
                        '缺乏论据支撑',
                        '抄袭和洗稿'
                    ]
                }
            }
        },

        # 完整模板样例 - 科技+知乎
        {
            'title': '科技公司-知乎深度分析模板',
            'code': 'full_template_tech_zhihu',
            'type': 'full_template',
            'industry': 'tech',
            'platform': 'zhihu',
            'stage': 'both',
            'description': '适合科技类公司在知乎平台进行深度技术分析和品牌传播的完整模板',
            'is_recommended': True,
            'tags': ['推荐', '完整模板', '知乎'],
            'content': {
                'template_name': '科技公司-知乎深度分析模板',
                'industry': 'tech',
                'platform': 'zhihu',
                'prompts': {
                    'analysis': {
                        'system': '你是一个资深的科技行业分析师，有10年的科技公司研究经验。你擅长从技术创新、市场定位、行业影响力等多个维度深入分析科技公司，并能用专业但易懂的语言表达观点。',
                        'user_template': '请深入分析以下科技公司：\\n\\n公司名称：{{company_name}}\\n公司描述：{{company_desc}}\\n{% if uploaded_text %}补充资料：{{uploaded_text}}{% endif %}\\n\\n请从以下维度进行专业分析：\\n\\n1. **技术创新能力**\\n   - 核心技术栈和技术架构\\n   - 技术创新点和专利情况\\n   - 研发投入占比和团队规模\\n\\n2. **产品和服务**\\n   - 主要产品线和技术特点\\n   - 产品差异化优势\\n   - 技术生态建设\\n\\n3. **行业地位**\\n   - 在细分领域的市场份额\\n   - 与主要竞品的技术对比\\n   - 行业标准制定参与度\\n\\n4. **用户和市场**\\n   - 目标用户群体\\n   - 实际应用案例\\n   - 用户反馈和口碑\\n\\n5. **未来展望**\\n   - 技术发展路线\\n   - 潜在的增长空间\\n   - 面临的挑战和风险\\n\\n请提供具体的数据和案例支撑，保持客观理性的分析态度。',
                        'variables': ['company_name', 'company_desc', 'uploaded_text']
                    },
                    'article_generation': {
                        'system': '你是知乎科技领域的优秀回答者，有深厚的技术背景和丰富的行业经验。你的回答总是：1) 有深度和见解 2) 数据和案例支撑 3) 逻辑清晰易懂 4) 客观理性不偏颇 5) 避免营销化语言。',
                        'user_template': '基于以下分析结果，请撰写一篇适合知乎的高质量回答：\\n\\n公司：{{company_name}}\\n分析结果：\\n{{analysis}}\\n\\n本篇文章重点角度：{{angle}}\\n\\n写作要求：\\n\\n**开头（200字左右）**\\n- 用一个引人思考的问题或现象引入\\n- 简要说明你的分析角度和资格背景\\n\\n**正文主体（1200-1500字）**\\n- 使用2-3个小标题组织内容\\n- 每个部分都要有具体的数据或案例支撑\\n- 客观分析优势和不足\\n\\n**结尾（200字左右）**\\n- 总结核心观点\\n- 给出客观的评价或建议\\n\\n**语言风格**\\n- 第一人称或客观第三人称\\n- 专业但不生僻\\n- 避免标题党词汇\\n- 可适当使用理性表达\\n\\n请直接生成文章，格式为：\\n标题：[标题内容]\\n正文：\\n[正文内容]',
                        'variables': ['company_name', 'analysis', 'angle']
                    }
                },
                'ai_config': {
                    'temperature': 0.8,
                    'max_tokens': 3000,
                    'model': 'glm-4-flash'
                }
            }
        }
    ]

    try:
        created_count = 0

        for example_data in examples:
            existing = session.query(PromptExampleLibrary).filter_by(code=example_data['code']).first()
            if not existing:
                example = PromptExampleLibrary(
                    title=example_data['title'],
                    code=example_data['code'],
                    type=example_data['type'],
                    industry=example_data.get('industry'),
                    platform=example_data.get('platform'),
                    stage=example_data.get('stage'),
                    content=example_data['content'],
                    description=example_data.get('description'),
                    is_recommended=example_data.get('is_recommended', False),
                    tags=example_data.get('tags', []),
                    author='System',
                    display_order=0
                )
                session.add(example)
                created_count += 1

        session.commit()
        logger.info(f"   [OK] 创建了 {created_count} 个样例")

        return True

    except Exception as e:
        session.rollback()
        logger.error(f"   [ERROR] 初始化样例库失败: {e}")
        return False

    finally:
        session.close()


def verify_installation():
    """验证安装"""
    logger.info("\n[6/6] 验证安装...")
    session = SessionLocal()

    try:
        # 统计数据
        user_count = session.query(User).count()
        admin_count = session.query(User).filter_by(role='admin').count()
        category_count = session.query(PromptTemplateCategory).count()
        example_count = session.query(PromptExampleLibrary).count()

        logger.info(f"   [OK] 用户数: {user_count} (管理员: {admin_count})")
        logger.info(f"   [OK] 模板分类: {category_count}")
        logger.info(f"   [OK] 样例库: {example_count}")

        logger.info("\n" + "="*60)
        logger.info("安装完成！")
        logger.info("="*60)
        logger.info("\n提示词模板系统已成功初始化，包括：")
        logger.info("  - 5个新数据表")
        logger.info(f"  - {category_count}个模板分类")
        logger.info(f"  - {example_count}个预置样例")
        logger.info("  - 1个管理员账号 (admin / TopN@2024)")
        logger.info("\n下一步：")
        logger.info("  1. 启动应用: python app_factory.py")
        logger.info("  2. 访问管理界面创建模板")
        logger.info("  3. 用户可以使用模板生成文章")
        logger.info("\n")

        return True

    except Exception as e:
        logger.error(f"   [ERROR] 验证失败: {e}")
        return False

    finally:
        session.close()


def main():
    """主函数"""
    steps = [
        init_database,
        create_admin_user,
        init_categories,
        init_example_library,
        verify_installation
    ]

    for step in steps:
        if not step():
            logger.error("\n初始化失败！")
            return False

    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
