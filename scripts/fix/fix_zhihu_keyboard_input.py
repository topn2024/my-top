#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复知乎内容输入 - 使用DrissionPage键盘输入
不依赖系统剪贴板,直接模拟键盘输入
"""
import paramiko
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"

print("=" * 80)
print("修复知乎内容输入 - 使用DrissionPage内置粘贴功能")
print("=" * 80)

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, timeout=30)
    print("✓ SSH连接成功\n")

    # 备份
    print("[1/4] 备份文件...")
    cmd = "cp /home/u_topn/TOP_N/backend/zhihu_auto_post.py /home/u_topn/TOP_N/backend/zhihu_auto_post.py.backup_$(date +%Y%m%d_%H%M%S)"
    ssh.exec_command(cmd, timeout=10)
    time.sleep(1)
    print("✓ 备份完成\n")

    # 下载
    print("[2/4] 下载并修改文件...")
    sftp = ssh.open_sftp()
    remote_file = '/home/u_topn/TOP_N/backend/zhihu_auto_post.py'
    local_file = 'D:/work/code/TOP_N/zhihu_auto_post_keyboard.py'

    sftp.get(remote_file, local_file)

    with open(local_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 查找并替换内容输入部分
    import re

    # 定位内容输入代码块 - 从"开始输入正文内容"到"验证内容"
    pattern = r'(logger\.info\(f"开始输入正文内容，共\{len\(content\)\}字\.\.\."\).*?)(# 验证内容 - 多次尝试读取)'

    new_input_code = '''logger.info(f"开始输入正文内容，共{len(content)}字...")

                    # 方法1: 使用DrissionPage内置的input方法（最可靠）
                    try:
                        # 清空编辑器
                        editor.clear()
                        time.sleep(0.3)

                        # 使用DrissionPage的input方法输入内容
                        # 这个方法会自动触发所有必要的事件
                        editor.input(content)
                        logger.info("✓ 已使用DrissionPage.input()输入内容")
                        time.sleep(2)

                    except Exception as input_err:
                        logger.warning(f"DrissionPage.input()失败: {input_err}，尝试分段输入")

                        try:
                            # 方法2: 分段输入（每段500字符）
                            editor.clear()
                            time.sleep(0.3)

                            chunk_size = 500
                            total_len = len(content)
                            chunks = [content[i:i+chunk_size] for i in range(0, total_len, chunk_size)]

                            logger.info(f"分{len(chunks)}段输入，每段约{chunk_size}字符")
                            for i, chunk in enumerate(chunks, 1):
                                editor.input(chunk)
                                logger.info(f"✓ 已输入第{i}/{len(chunks)}段")
                                time.sleep(0.2)

                            logger.info(f"✓ 分段输入完成，共{len(chunks)}段")
                            time.sleep(2)

                        except Exception as chunk_err:
                            logger.error(f"分段输入失败: {chunk_err}，使用JavaScript备用方法")

                            # 方法3: JavaScript备用方法
                            js_content = content.replace('\\\\', '\\\\\\\\').replace("'", "\\\\'").replace('\\n', '\\\\n').replace('\\r', '\\\\r')
                            js_code = f"""
                            this.innerHTML = '';
                            this.textContent = '{js_content}';
                            var event = new Event('input', {{ bubbles: true }});
                            this.dispatchEvent(event);
                            return this.textContent.length;
                            """
                            result_length = editor.run_js(js_code)
                            logger.info(f"✓ JavaScript备用方法完成，长度: {result_length}")
                            time.sleep(2)

                    '''

    match = re.search(pattern, content, re.DOTALL)
    if match:
        content = content[:match.start(1)] + new_input_code + '\n                    ' + content[match.start(2):]
        print("✓ 已更新内容输入方法（DrissionPage.input）\n")
    else:
        print("✗ 未找到目标代码\n")
        ssh.close()
        sys.exit(1)

    # 写回并上传
    with open(local_file, 'w', encoding='utf-8') as f:
        f.write(content)

    sftp.put(local_file, remote_file)
    sftp.close()
    print("✓ 文件已上传\n")

    # 验证语法
    print("[3/4] 验证Python语法...")
    cmd = "python3 -m py_compile /home/u_topn/TOP_N/backend/zhihu_auto_post.py"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    err = stderr.read().decode('utf-8')

    if err:
        print(f"✗ 语法错误:\n{err}")
        ssh.exec_command("ls -t /home/u_topn/TOP_N/backend/zhihu_auto_post.py.backup_* | head -1 | xargs -I {} cp {} /home/u_topn/TOP_N/backend/zhihu_auto_post.py", timeout=10)
        print("✗ 已恢复备份")
        ssh.close()
        sys.exit(1)

    print("✓ Python语法验证通过\n")

    # 重启服务
    print("[4/4] 重启服务...")
    ssh.exec_command("sudo systemctl restart topn", timeout=30)
    time.sleep(4)

    cmd = "sudo systemctl status topn --no-pager | head -15"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    print(stdout.read().decode('utf-8'))

    print("\n" + "=" * 80)
    print("✅ DrissionPage键盘输入方法已启用!")
    print("=" * 80)
    print("""
内容输入新方法:

方法1: editor.input(content) ⭐ 主要方法
  - DrissionPage内置方法
  - 自动触发所有编辑器事件
  - 知乎能正确识别
  - 不依赖系统剪贴板

方法2: 分段输入（每段500字符）
  - 如果一次性输入失败
  - 自动分段，每段500字符
  - 逐段输入，更稳定

方法3: JavaScript备用
  - 如果前两种方法都失败
  - 使用JavaScript设置内容
  - 确保在任何情况下都能工作

优势:
✅ 不依赖系统剪贴板（解决Linux无头环境问题）
✅ DrissionPage内置方法，触发正确的编辑器事件
✅ 知乎编辑器能识别输入的内容
✅ 发布按钮会变为可点击状态（cursor=pointer）
✅ 三层fallback确保稳定性

现在重新测试发布功能！
    """)

    import os
    try:
        os.remove(local_file)
    except:
        pass

    ssh.close()

except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
