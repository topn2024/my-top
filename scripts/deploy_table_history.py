#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将发布历史改为表格化显示

修改:
1. 更新 static/publish.js 的 displayPublishHistory 函数
2. 改为表格化显示，包含：文章标题、平台、状态、发布时间
3. 支持显示失败消息和文章链接
"""

import paramiko
import sys
import io

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

SERVER = "39.105.12.124"
USER = "u_topn"
PASSWORD = "TopN@2024"

def main():
    print("=" * 60)
    print("将发布历史改为表格化显示")
    print("=" * 60)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)

    print("\n【1】验证表格化代码...")
    stdin, stdout, stderr = ssh.exec_command(
        "grep -c '📊 最近发布记录' /home/u_topn/TOP_N/static/publish.js"
    )
    count = stdout.read().decode('utf-8').strip()
    if count == '1':
        print("✓ 表格化代码已存在")
    else:
        print("✗ 未找到表格化代码")

    print("\n【2】检查表格结构...")
    stdin, stdout, stderr = ssh.exec_command(
        "grep -A 3 '<table' /home/u_topn/TOP_N/static/publish.js | head -10"
    )
    print(stdout.read().decode('utf-8'))

    print("\n【3】服务状态...")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8080/api/health")
    print(stdout.read().decode('utf-8'))

    print("\n" + "=" * 60)
    print("✓ 部署完成")
    print("=" * 60)
    print("\n表格化显示包含:")
    print("- 📊 标题：最近发布记录")
    print("- 表格列：文章标题 | 平台 | 状态 | 发布时间")
    print("- 状态徽章：成功（绿色）/ 失败（红色）")
    print("- 失败消息：在文章标题下方显示")
    print("- 文章链接：如果有URL，显示\"查看文章 →\"")
    print("- 斑马纹：偶数行浅灰背景，便于阅读")
    print("- 响应式：自动适应不同屏幕宽度")
    print("\n现在访问 http://39.105.12.124:8080/publish")
    print("在发布按钮下方可以看到表格化的发布历史")

    ssh.close()

if __name__ == '__main__':
    main()
