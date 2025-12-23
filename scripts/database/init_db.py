#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
创建 topn_platform 数据库和所有必需的表
"""
import pymysql
import sys
import os

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',  # 服务器本地连接
    'port': 3306,
    'user': 'admin',
    'password': 'TopN@MySQL2024',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

DATABASE_NAME = 'topn_platform'

# SQL 建表语句
CREATE_TABLES_SQL = """
-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 工作流表
CREATE TABLE IF NOT EXISTS workflows (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    company_name VARCHAR(200) NOT NULL,
    company_desc TEXT,
    uploaded_text LONGTEXT,
    uploaded_filename VARCHAR(255),
    analysis LONGTEXT,
    article_count INT DEFAULT 3,
    platforms JSON,
    current_step INT DEFAULT 1,
    status VARCHAR(50) DEFAULT 'in_progress',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 文章表
CREATE TABLE IF NOT EXISTS articles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    workflow_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    content LONGTEXT NOT NULL,
    article_type VARCHAR(50),
    article_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE,
    INDEX idx_workflow_id (workflow_id),
    INDEX idx_article_order (article_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 平台账号表
CREATE TABLE IF NOT EXISTS platform_accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    platform VARCHAR(50) NOT NULL,
    username VARCHAR(100) NOT NULL,
    password_encrypted TEXT NOT NULL,
    notes TEXT,
    status VARCHAR(50) DEFAULT 'active',
    last_tested TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_platform (platform),
    UNIQUE KEY unique_user_platform_username (user_id, platform, username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 发布历史表
CREATE TABLE IF NOT EXISTS publish_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    article_id INT NOT NULL,
    user_id INT NOT NULL,
    platform VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    url TEXT,
    message TEXT,
    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_article_id (article_id),
    INDEX idx_user_id (user_id),
    INDEX idx_platform (platform),
    INDEX idx_published_at (published_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

def create_database():
    """创建数据库"""
    connection = None
    try:
        # 连接到MySQL服务器（不指定数据库）
        connection = pymysql.connect(**DB_CONFIG)

        with connection.cursor() as cursor:
            # 创建数据库
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"✓ 数据库 '{DATABASE_NAME}' 已创建/已存在")

        connection.commit()
        return True

    except Exception as e:
        print(f"✗ 创建数据库失败: {e}")
        return False

    finally:
        if connection:
            connection.close()

def create_tables():
    """创建所有表"""
    connection = None
    try:
        # 连接到创建的数据库
        config = DB_CONFIG.copy()
        config['database'] = DATABASE_NAME
        connection = pymysql.connect(**config)

        with connection.cursor() as cursor:
            # 执行建表语句
            statements = [s.strip() for s in CREATE_TABLES_SQL.split(';') if s.strip()]

            for statement in statements:
                if statement:
                    cursor.execute(statement)

            print("✓ 所有表已创建:")
            print("  - users (用户表)")
            print("  - workflows (工作流表)")
            print("  - articles (文章表)")
            print("  - platform_accounts (平台账号表)")
            print("  - publish_history (发布历史表)")

        connection.commit()
        return True

    except Exception as e:
        print(f"✗ 创建表失败: {e}")
        return False

    finally:
        if connection:
            connection.close()

def verify_tables():
    """验证表是否创建成功"""
    connection = None
    try:
        config = DB_CONFIG.copy()
        config['database'] = DATABASE_NAME
        connection = pymysql.connect(**config)

        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()

            expected_tables = ['users', 'workflows', 'articles', 'platform_accounts', 'publish_history']
            actual_tables = [list(t.values())[0] for t in tables]

            print("\n验证表结构:")
            for table_name in expected_tables:
                if table_name in actual_tables:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                    count = cursor.fetchone()['count']
                    print(f"  ✓ {table_name} (记录数: {count})")
                else:
                    print(f"  ✗ {table_name} 未找到")

        return True

    except Exception as e:
        print(f"✗ 验证失败: {e}")
        return False

    finally:
        if connection:
            connection.close()

def test_connection():
    """测试数据库连接"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        print("✓ 成功连接到 MySQL 服务器")
        connection.close()
        return True
    except Exception as e:
        print(f"✗ 连接失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("TOP_N 平台 - 数据库初始化")
    print("=" * 60)

    # 测试连接
    print("\n[步骤 1/4] 测试数据库连接...")
    if not test_connection():
        print("\n初始化失败：无法连接到数据库服务器")
        print(f"请检查以下配置:")
        print(f"  - 主机: {DB_CONFIG['host']}")
        print(f"  - 端口: {DB_CONFIG['port']}")
        print(f"  - 用户: {DB_CONFIG['user']}")
        sys.exit(1)

    # 创建数据库
    print("\n[步骤 2/4] 创建数据库...")
    if not create_database():
        print("\n初始化失败")
        sys.exit(1)

    # 创建表
    print("\n[步骤 3/4] 创建数据表...")
    if not create_tables():
        print("\n初始化失败")
        sys.exit(1)

    # 验证
    print("\n[步骤 4/4] 验证表结构...")
    if not verify_tables():
        print("\n初始化失败")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✓ 数据库初始化完成!")
    print("=" * 60)
    print("\n下一步:")
    print("  1. 运行 create_admin.py 创建管理员账号")
    print("  2. 运行 migrate_accounts.py 迁移账号数据")
    print("=" * 60)

if __name__ == '__main__':
    main()
