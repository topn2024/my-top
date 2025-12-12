#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Canvas二维码提取功能
"""

import paramiko
import sys
import io
import time

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

SERVER = "39.105.12.124"
USER = "u_topn"
PASSWORD = "TopN@2024"
DEPLOY_DIR = "/home/u_topn/TOP_N"

def main():
    print("测试Canvas二维码提取功能...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)

    test_script = '''
cd /home/u_topn/TOP_N

# 清理之前的测试文件
rm -f /tmp/canvas_test.log

# 创建测试脚本
cat > /tmp/test_canvas_qr.py << 'TESTEOF'
import sys
import os
sys.path.insert(0, '/home/u_topn/TOP_N/backend')

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/canvas_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

from zhihu_auth.zhihu_qr_login import ZhihuQRLogin

logger = logging.getLogger(__name__)

try:
    logger.info('=== 开始测试Canvas二维码提取 ===')

    qr_login = ZhihuQRLogin()
    success, qr_base64, message = qr_login.get_qr_code()

    if success:
        logger.info(f'✓ 二维码获取成功!')
        logger.info(f'消息: {message}')
        logger.info(f'Base64长度: {len(qr_base64)} 字符')
        logger.info(f'Base64前80字符: {qr_base64[:80]}...')

        # 保存到文件测试
        import base64
        qr_data = base64.b64decode(qr_base64)
        with open('/tmp/test_qr.png', 'wb') as f:
            f.write(qr_data)
        logger.info(f'✓ 二维码已保存到 /tmp/test_qr.png ({len(qr_data)} bytes)')

    else:
        logger.error(f'✗ 二维码获取失败: {message}')

    # 清理
    qr_login.close()
    logger.info('=== 测试完成 ===')

except Exception as e:
    logger.error(f'测试出错: {e}', exc_info=True)
TESTEOF

# 运行测试
echo "开始运行测试..."
python3 /tmp/test_canvas_qr.py

# 显示日志
echo ""
echo "=== 测试日志 ==="
cat /tmp/canvas_test.log

# 检查生成的二维码文件
echo ""
echo "=== 二维码文件信息 ==="
ls -lh /tmp/test_qr.png 2>&1 || echo "未生成二维码文件"
'''

    # 执行测试
    print("\n执行测试脚本...\n")
    stdin, stdout, stderr = ssh.exec_command(test_script)

    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')

    print(output)
    if error:
        print(f"\n错误输出:\n{error}")

    print("\n✓ 测试完成")
    print("\n说明:")
    print("- 如果显示'二维码获取成功'，表示Canvas选择器工作正常")
    print("- 如果有'二维码已保存到/tmp/test_qr.png'，可以下载查看实际二维码图片")
    print("- 如果仍然失败，需要检查日志中的详细错误信息")

    ssh.close()

if __name__ == '__main__':
    main()
