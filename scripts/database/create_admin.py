#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建管理员账号
"""
import sys
from auth import create_user


def main():
    """创建管理员账号"""
    print("=" * 60)
    print("创建管理员账号")
    print("=" * 60)

    # 默认管理员信息
    username = "admin"
    email = "admin@topn.com"
    password = "TopN@2024"
    full_name = "系统管理员"

    print(f"\n管理员信息:")
    print(f"  用户名: {username}")
    print(f"  邮箱: {email}")
    print(f"  密码: {password}")
    print(f"  姓名: {full_name}")

    print("\n正在创建管理员账号...")

    user, error = create_user(
        username=username,
        email=email,
        password=password,
        full_name=full_name
    )

    if error:
        if "已存在" in error:
            print(f"\n✓ 管理员账号已存在，无需重复创建")
            print(f"\n登录信息:")
            print(f"  用户名: {username}")
            print(f"  密码: {password}")
            return
        else:
            print(f"\n✗ 创建失败: {error}")
            sys.exit(1)

    if user:
        print(f"\n✓ 管理员账号创建成功!")
        print(f"\n登录信息:")
        print(f"  用户名: {username}")
        print(f"  密码: {password}")
        print(f"  用户ID: {user.id}")
        print("\n" + "=" * 60)
        print("警告: 请尽快修改默认密码!")
        print("=" * 60)
    else:
        print(f"\n✗ 创建失败")
        sys.exit(1)


if __name__ == '__main__':
    main()
