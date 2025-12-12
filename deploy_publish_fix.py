#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署发布功能修复到服务器
"""
import os
import sys

def deploy_fix():
    """部署修复"""
    server = '39.105.12.124'
    user = 'u_topn'
    remote_dir = '/home/u_topn/TOP_N'

    print("=" * 60)
    print("部署发布功能修复到服务器")
    print("=" * 60)

    # 要上传的文件
    files_to_upload = [
        'backend/zhihu_auto_post_enhanced.py'
    ]

    for local_file in files_to_upload:
        remote_file = f"{remote_dir}/{local_file}"

        print(f"\n上传文件: {local_file}")
        print(f"目标: {server}:{remote_file}")

        # 使用scp上传
        cmd = f'scp "{local_file}" {user}@{server}:{remote_file}'
        print(f"执行命令: {cmd}")

        result = os.system(cmd)

        if result == 0:
            print(f"✓ {local_file} 上传成功")
        else:
            print(f"✗ {local_file} 上传失败")
            return False

    print("\n" + "=" * 60)
    print("重启服务")
    print("=" * 60)

    # 重启服务
    restart_cmd = f'ssh {user}@{server} "sudo systemctl restart topn"'
    print(f"执行命令: {restart_cmd}")

    result = os.system(restart_cmd)

    if result == 0:
        print("✓ 服务重启成功")
    else:
        print("✗ 服务重启失败")
        return False

    print("\n" + "=" * 60)
    print("部署完成！")
    print("=" * 60)
    print("\n请访问 http://39.105.12.124:8080 测试发布功能")

    return True

if __name__ == '__main__':
    try:
        success = deploy_fix()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 部署失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
