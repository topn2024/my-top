#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化三模块提示词系统数据库
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import Base, engine, SessionLocal, AnalysisPrompt, ArticlePrompt, PlatformStylePrompt, PromptCombinationLog

print("="*60)
print("Initializing Three-Module Prompt System Database")
print("="*60)

# 创建所有表
print("\nCreating tables...")
Base.metadata.create_all(bind=engine)
print("✓ Tables created successfully")

# 验证表是否创建
session = SessionLocal()
try:
    # 检查表
    analysis_count = session.query(AnalysisPrompt).count()
    article_count = session.query(ArticlePrompt).count()
    platform_count = session.query(PlatformStylePrompt).count()

    print(f"\nVerification:")
    print(f"  - analysis_prompts table: ✓ ({analysis_count} records)")
    print(f"  - article_prompts table: ✓ ({article_count} records)")
    print(f"  - platform_style_prompts table: ✓ ({platform_count} records)")
    print(f"  - prompt_combination_logs table: ✓")

finally:
    session.close()

print("\n" + "="*60)
print("Initialization Complete!")
print("="*60)
