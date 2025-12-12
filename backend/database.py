#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库连接和通用工具函数
"""
from contextlib import contextmanager
from models import SessionLocal, engine
from sqlalchemy import text


@contextmanager
def get_db_context():
    """
    数据库会话上下文管理器

    用法:
        with get_db_context() as db:
            user = db.query(User).filter_by(username='admin').first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def execute_query(query, params=None):
    """
    执行查询并返回结果

    Args:
        query: SQL 查询语句
        params: 查询参数（可选）

    Returns:
        查询结果列表
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        return result.fetchall()


def execute_update(query, params=None):
    """
    执行更新语句

    Args:
        query: SQL 更新语句
        params: 查询参数（可选）

    Returns:
        影响的行数
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        conn.commit()
        return result.rowcount


def test_connection():
    """测试数据库连接"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return True
    except Exception as e:
        print(f"数据库连接测试失败: {e}")
        return False


# 通用CRUD操作助手

def get_one(model, **filters):
    """
    获取单个记录

    Args:
        model: 数据模型类
        **filters: 过滤条件

    Returns:
        模型实例或None
    """
    with get_db_context() as db:
        return db.query(model).filter_by(**filters).first()


def get_all(model, **filters):
    """
    获取所有符合条件的记录

    Args:
        model: 数据模型类
        **filters: 过滤条件

    Returns:
        模型实例列表
    """
    with get_db_context() as db:
        query = db.query(model)
        if filters:
            query = query.filter_by(**filters)
        return query.all()


def create_one(model, **data):
    """
    创建单个记录

    Args:
        model: 数据模型类
        **data: 字段数据

    Returns:
        创建的模型实例
    """
    with get_db_context() as db:
        instance = model(**data)
        db.add(instance)
        db.flush()
        db.refresh(instance)
        return instance


def update_one(instance, **data):
    """
    更新记录

    Args:
        instance: 模型实例
        **data: 要更新的字段

    Returns:
        更新后的实例
    """
    with get_db_context() as db:
        for key, value in data.items():
            setattr(instance, key, value)
        db.add(instance)
        db.flush()
        db.refresh(instance)
        return instance


def delete_one(instance):
    """
    删除记录

    Args:
        instance: 模型实例

    Returns:
        True if successful
    """
    with get_db_context() as db:
        db.delete(instance)
        return True


if __name__ == '__main__':
    # 测试数据库连接
    print("测试数据库连接...")
    if test_connection():
        print("✓ 数据库连接成功")
    else:
        print("✗ 数据库连接失败")
