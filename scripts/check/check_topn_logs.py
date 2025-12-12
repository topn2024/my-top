#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查服务器上TOP_N应用的日志位置
"""
import paramiko
import sys
import io

# Set UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def check_logs():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"连接到服务器 {SERVER_HOST}...")
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("连接成功!\n")

        print("="*80)
        print("TOP_N应用日志位置检查")
        print("="*80)

        # 1. systemd服务日志说明
        print("\n1. Systemd服务日志 (推荐):")
        print("-"*80)
        print("TOP_N应用作为systemd服务运行,所有输出都记录在systemd journal中")
        print("\n常用日志查看命令:")
        print("  sudo journalctl -u topn -n 100        # 查看最近100行日志")
        print("  sudo journalctl -u topn -f            # 实时查看日志")
        print("  sudo journalctl -u topn --since today # 查看今天的日志")
        print("  sudo journalctl -u topn -p err        # 只查看错误日志")

        # 2. 检查应用目录中的日志文件
        print("\n\n2. 应用目录中的日志文件:")
        print("-"*80)
        stdin, stdout, stderr = ssh.exec_command('find /home/u_topn/TOP_N -name "*.log" 2>/dev/null')
        log_files = stdout.read().decode('utf-8', errors='ignore').strip()
        if log_files:
            print("找到以下日志文件:")
            for f in log_files.split('\n'):
                if f:
                    print(f"  {f}")
        else:
            print("应用目录中未找到.log文件")

        # 3. 检查Flask应用日志配置
        print("\n\n3. Flask应用日志配置:")
        print("-"*80)
        stdin, stdout, stderr = ssh.exec_command('grep -n "logging" /home/u_topn/TOP_N/backend/app_with_upload.py 2>/dev/null | head -10')
        logging_config = stdout.read().decode('utf-8', errors='ignore').strip()
        if logging_config:
            print("应用中的日志配置:")
            print(logging_config)
        else:
            print("应用使用默认的Flask日志配置")

        # 4. 查看systemd服务输出配置
        print("\n\n4. Systemd服务日志输出配置:")
        print("-"*80)
        stdin, stdout, stderr = ssh.exec_command('sudo systemctl show topn --property=StandardOutput,StandardError')
        output_config = stdout.read().decode('utf-8', errors='ignore').strip()
        print(output_config)
        print("\n说明: journal表示输出到systemd journal,这是推荐的方式")

        # 5. 查看最新日志示例
        print("\n\n5. 最新日志示例 (最近30行):")
        print("-"*80)
        stdin, stdout, stderr = ssh.exec_command('sudo journalctl -u topn -n 30 --no-pager')
        recent_logs = stdout.read().decode('utf-8', errors='ignore')
        if recent_logs:
            print(recent_logs)
        else:
            print("未找到日志记录")

        # 6. 创建日志查看脚本
        print("\n\n6. 创建便捷日志查看脚本:")
        print("-"*80)

        view_logs_script = '''#!/bin/bash
# TOP_N logs viewer

case "$1" in
    tail)
        echo "Real-time logs..."
        sudo journalctl -u topn -f
        ;;
    today)
        echo "Today logs..."
        sudo journalctl -u topn --since today --no-pager
        ;;
    error)
        echo "Error logs..."
        sudo journalctl -u topn -p err --no-pager -n 100
        ;;
    last)
        lines="${2:-100}"
        echo "Last $lines lines..."
        sudo journalctl -u topn -n $lines --no-pager
        ;;
    *)
        echo "TOP_N Log Viewer"
        echo ""
        echo "Usage:"
        echo "  ./view_topn_logs.sh tail       - Real-time logs"
        echo "  ./view_topn_logs.sh today      - Today logs"
        echo "  ./view_topn_logs.sh error      - Error logs only"
        echo "  ./view_topn_logs.sh last [N]   - Last N lines"
        echo ""
        echo "Examples:"
        echo "  ./view_topn_logs.sh last 50"
        echo "  ./view_topn_logs.sh tail"
        ;;
esac
'''

        # 使用sftp上传脚本
        sftp = ssh.open_sftp()
        with sftp.file('/home/u_topn/view_topn_logs.sh', 'w') as f:
            f.write(view_logs_script)
        sftp.close()

        stdin, stdout, stderr = ssh.exec_command('chmod +x /home/u_topn/view_topn_logs.sh')
        stdout.read()

        print("✓ 已创建日志查看脚本: /home/u_topn/view_topn_logs.sh")
        print("\n使用方法:")
        print("  ./view_topn_logs.sh tail       - 实时查看日志")
        print("  ./view_topn_logs.sh today      - 查看今天的日志")
        print("  ./view_topn_logs.sh error      - 查看错误日志")
        print("  ./view_topn_logs.sh last 50    - 查看最近50行")

        ssh.close()

        print("\n" + "="*80)
        print("日志位置总结")
        print("="*80)
        print("\n主要日志位置:")
        print("  1. Systemd Journal: sudo journalctl -u topn")
        print("  2. 便捷脚本: /home/u_topn/view_topn_logs.sh")
        print("\n推荐使用:")
        print("  - 实时监控: ./view_topn_logs.sh tail")
        print("  - 快速查看: ./view_topn_logs.sh last 100")
        print("  - 错误排查: ./view_topn_logs.sh error")
        print("\n" + "="*80)

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_logs()
