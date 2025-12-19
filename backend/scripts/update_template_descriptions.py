"""
更新模板描述为中文
"""
from models import SessionLocal
from models_prompt_template import PromptTemplate

def update_template_descriptions():
    """更新所有默认模板的名称和描述为中文"""
    session = SessionLocal()

    try:
        # 更新模板1: 科技公司-知乎
        template1 = session.query(PromptTemplate).filter_by(code='tech_zhihu_v1').first()
        if template1:
            template1.name = '科技公司-知乎平台专用模板'
            template1.description = '专为科技类公司在知乎平台推广设计的模板，适合分析技术创新、产品特点和行业应用，生成专业且易读的深度文章'
            print(f'✅ 已更新模板: {template1.code}')
            print(f'   新名称: {template1.name}')
            print(f'   新描述: {template1.description}')

        # 更新模板2: 金融公司-通用
        template2 = session.query(PromptTemplate).filter_by(code='finance_general_v1').first()
        if template2:
            template2.name = '金融公司-通用推广模板'
            template2.description = '适用于金融科技、保险、投资等金融类企业的通用模板，侧重合规性、安全性和专业性，可用于多个平台发布'
            print(f'✅ 已更新模板: {template2.code}')
            print(f'   新名称: {template2.name}')
            print(f'   新描述: {template2.description}')

        # 更新模板3: 教育行业-在线学习
        template3 = session.query(PromptTemplate).filter_by(code='education_online_v1').first()
        if template3:
            template3.name = '在线教育-多平台通用模板'
            template3.description = '专为在线教育、培训机构设计的模板，强调教育价值和学习效果，适合知乎、今日头条等内容平台，避免过度营销'
            print(f'✅ 已更新模板: {template3.code}')
            print(f'   新名称: {template3.name}')
            print(f'   新描述: {template3.description}')

        session.commit()
        print('\n🎉 所有模板描述已成功更新为中文！')

        # 验证更新
        print('\n📋 当前模板列表:')
        templates = session.query(PromptTemplate).all()
        for t in templates:
            print(f'\n模板 {t.id}: {t.name}')
            print(f'  代码: {t.code}')
            print(f'  描述: {t.description}')
            print(f'  状态: {t.status}')

    except Exception as e:
        session.rollback()
        print(f'❌ 更新失败: {str(e)}')
        raise
    finally:
        session.close()

if __name__ == '__main__':
    update_template_descriptions()
