"""
主应用入口
使用 app_factory 创建应用实例
"""
from app_factory import create_app
import os

# 创建应用实例（使用production配置）
app = create_app('production')

# 注意：所有路由现在都在 blueprints 中定义
# pages_bp: 页面路由 (/, /platform, /analysis, /articles, /publish, /login, /templates)
# auth_bp: 认证路由 (/api/auth/*)
# api_bp: API路由 (/api/analyze, /api/generate_articles, /api/upload, etc.)
# task_bp: 任务路由 (/task/*)
# prompt_template_bp: 提示词模板路由 (/api/prompt-templates/*)
# analysis_prompt_bp: 分析提示词路由 (/api/prompts/analysis/*)
# article_prompt_bp: 文章提示词路由 (/api/prompts/article/*)
# platform_style_bp: 平台风格路由 (/api/prompts/platform-style/*)
# combination_bp: 组合推荐路由 (/api/prompts/combinations/*)
# article_style_bp: 风格转换路由 (/api/articles/convert-style, etc.)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
