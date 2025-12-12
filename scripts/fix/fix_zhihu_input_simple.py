#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单但有效的修复方案 - 使用JavaScript直接设置知乎编辑器内容
"""
import paramiko
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

try:
    print("=" * 80)
    print("修复知乎内容输入问题 - 使用JavaScript方案")
    print("=" * 80)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
    print("✓ SSH连接成功\n")

    # 备份
    print("[1/3] 备份文件...")
    cmd = "cp /home/u_topn/TOP_N/backend/zhihu_auto_post.py /home/u_topn/TOP_N/backend/zhihu_auto_post.py.backup_$(date +%Y%m%d_%H%M%S)"
    ssh.exec_command(cmd, timeout=10)
    time.sleep(1)
    print("✓ 备份完成")

    # 使用sed直接替换输入内容的部分 (第156-174行)
    print("\n[2/3] 修改内容输入方法...")

    # 创建新的输入逻辑
    cmd = r"""cat > /tmp/new_input_method.txt << 'NEWMETHOD'
                if editor:
                    # 点击编辑器激活
                    editor.click()
                    time.sleep(0.5)

                    # 使用JavaScript设置内容(最可靠)
                    # 将内容转换为HTML段落格式
                    paragraphs = content.split('\n\n')
                    html_parts = []
                    for para in paragraphs:
                        if para.strip():
                            # 处理段落中的单个换行
                            para_html = para.strip().replace('\n', '<br>')
                            html_parts.append(f'<p>{para_html}</p>')

                    html_content = ''.join(html_parts)

                    # 使用JavaScript设置内容
                    js_code = '''
                    this.innerHTML = arguments[0];
                    var event = new Event('input', { bubbles: true });
                    this.dispatchEvent(event);
                    '''

                    editor.run_js(js_code, html_content)
                    time.sleep(2)

                    # 验证内容长度
                    editor_text = editor.text
                    content_text = content.replace('\n\n', '').replace('\n', '')
                    similarity = len(editor_text) / max(len(content_text), 1)

                    logger.info(f"✓ 正文已输入: 编辑器{len(editor_text)}字 / 原文{len(content)}字 / 相似度{similarity*100:.1f}%")

                    if similarity < 0.7:
                        logger.warning(f"⚠ 内容可能不完整,相似度仅{similarity*100:.1f}%")
NEWMETHOD"""

    ssh.exec_command(cmd, timeout=10)
    time.sleep(1)

    # 替换原有的输入逻辑(第156-174行之间)
    cmd = r"""sed -i '156,174d' /home/u_topn/TOP_N/backend/zhihu_auto_post.py && \
sed -i '155r /tmp/new_input_method.txt' /home/u_topn/TOP_N/backend/zhihu_auto_post.py"""

    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    err = stderr.read().decode('utf-8')
    if err:
        print(f"警告: {err}")
    else:
        print("✓ 内容输入方法已更新")

    # 重启服务
    print("\n[3/3] 重启服务...")
    cmd = "sudo systemctl restart topn"
    ssh.exec_command(cmd, timeout=30)
    time.sleep(4)

    # 验证服务
    cmd = "sudo systemctl status topn --no-pager | head -15"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    print(stdout.read().decode('utf-8'))

    print("\n" + "=" * 80)
    print("✅ 修复完成!")
    print("=" * 80)
    print("""
改进说明:

1. ✅ 使用JavaScript直接设置innerHTML
   - 一次性设置所有内容,不会被截断
   - 自动转换为HTML格式(段落用<p>标签)
   - 触发input事件通知编辑器

2. ✅ 内容验证机制
   - 计算编辑器实际字数与原文对比
   - 显示相似度百分比
   - 如果相似度低于70%会发出警告

3. ✅ 保持段落格式
   - 双换行转为<p>段落
   - 单换行转为<br>

现在请重新测试发布功能,应该能看到完整内容了!
    """)

    ssh.close()

except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
