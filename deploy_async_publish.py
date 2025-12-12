#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署异步发布功能到服务器
"""
import os
import sys

def deploy():
    """部署所有修改的文件"""
    server = '39.105.12.124'
    user = 'u_topn'
    remote_dir = '/home/u_topn/TOP_N'

    print("=" * 70)
    print("部署异步发布功能（多线程改造）")
    print("=" * 70)

    # 要上传的文件列表
    files_to_upload = [
        ('backend/zhihu_auto_post_enhanced.py', f'{remote_dir}/backend/zhihu_auto_post_enhanced.py'),
        ('backend/blueprints/api.py', f'{remote_dir}/backend/blueprints/api.py'),
        ('backend/services/publish_worker.py', f'{remote_dir}/backend/services/publish_worker.py'),
        ('static/publish.js', f'{remote_dir}/static/publish.js'),
    ]

    print(f"\n准备上传 {len(files_to_upload)} 个文件到服务器...")
    print()

    success_count = 0
    failed_count = 0

    for local_file, remote_file in files_to_upload:
        print(f"上传: {local_file}")
        print(f"  -> {remote_file}")

        # 使用scp上传
        cmd = f'scp "{local_file}" {user}@{server}:{remote_file}'
        result = os.system(cmd)

        if result == 0:
            print(f"  OK\n")
            success_count += 1
        else:
            print(f"  FAILED\n")
            failed_count += 1

    print("=" * 70)
    print(f"上传完成: {success_count} 成功, {failed_count} 失败")
    print("=" * 70)

    if failed_count > 0:
        print("\n有文件上传失败，请检查后重试")
        return False

    # 重启gunicorn
    print("\n重启Gunicorn...")
    restart_cmd = f'ssh {user}@{server} "kill -HUP $(pgrep -f \\"gunicorn.*app_factory\\" | head -1)"'
    result = os.system(restart_cmd)

    if result == 0:
        print("Gunicorn重启成功")
    else:
        print("Gunicorn重启失败，请手动重启")

    print("\n" + "=" * 70)
    print("部署完成！")
    print("=" * 70)
    print("\n下一步操作：")
    print("1. 启动RQ Worker（如果未运行）")
    print("2. 确保Redis服务运行正常")
    print("3. 测试发布功能")
    print()
    print("启动RQ Worker命令:")
    print(f"  ssh {user}@{server}")
    print(f"  cd {remote_dir}")
    print("  source venv/bin/activate  # 如果使用虚拟环境")
    print("  rq worker default --with-scheduler &")
    print()

    return True

if __name__ == '__main__':
    try:
        success = deploy()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n部署失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
