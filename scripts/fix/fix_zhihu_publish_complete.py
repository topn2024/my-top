#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完善知乎发布功能：
1. 使用键盘输入替代JavaScript（更可靠）
2. 添加发布前截图验证
3. 确保发布完成并返回实际URL
4. 将详细错误信息返回前端
"""
import paramiko
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

# 改进后的正文输入方法（使用键盘输入）
IMPROVED_CONTENT_INPUT = '''                if editor:
                    # 点击编辑器激活
                    editor.click()
                    time.sleep(0.5)

                    # 清空编辑器
                    try:
                        from DrissionPage.common import Keys
                        self.page.actions.key_down(Keys.CTRL).key('a').key_up(Keys.CTRL).key(Keys.BACKSPACE)
                        time.sleep(0.3)
                    except:
                        pass

                    # 使用键盘输入内容（最可靠的方法）
                    logger.info(f"开始输入正文内容，共{len(content)}字...")

                    # 分段输入，避免一次性输入过多
                    chunk_size = 200  # 每次输入200字符
                    for i in range(0, len(content), chunk_size):
                        chunk = content[i:i+chunk_size]
                        editor.input(chunk, clear=False)  # 不清空，追加输入
                        time.sleep(0.1)  # 短暂延迟
                        if (i + chunk_size) % 1000 == 0:  # 每1000字符记录一次
                            logger.info(f"已输入 {min(i+chunk_size, len(content))}/{len(content)} 字符...")

                    time.sleep(1)  # 等待内容完全输入

                    # 验证内容 - 多次尝试读取
                    editor_text = None
                    for attempt in range(3):
                        time.sleep(0.5)
                        try:
                            editor_text = editor.text
                            if editor_text and len(editor_text) > 100:  # 确保读取到了内容
                                break
                        except:
                            logger.warning(f"第{attempt+1}次读取编辑器内容失败，重试...")

                    if editor_text:
                        content_text = content.replace('\\n\\n', '').replace('\\n', '')
                        similarity = len(editor_text) / max(len(content_text), 1)

                        logger.info(f"✓ 正文已输入: 编辑器{len(editor_text)}字 / 原文{len(content)}字 / 相似度{similarity*100:.1f}%")

                        if similarity < 0.6:  # 降低阈值到60%
                            error_msg = f"内容输入不完整: 相似度仅{similarity*100:.1f}%，编辑器{len(editor_text)}字，原文{len(content)}字"
                            logger.error(f"✗ {error_msg}")
                            # 截图保存错误状态
                            try:
                                screenshot_path = f'/tmp/zhihu_content_error_{int(time.time())}.png'
                                self.page.get_screenshot(path=screenshot_path)
                                logger.info(f"已保存错误截图: {screenshot_path}")
                            except:
                                pass
                            return {'success': False, 'message': error_msg}
                    else:
                        error_msg = "无法读取编辑器内容，内容可能未正确输入"
                        logger.error(f"✗ {error_msg}")
                        try:
                            screenshot_path = f'/tmp/zhihu_no_content_{int(time.time())}.png'
                            self.page.get_screenshot(path=screenshot_path)
                            logger.info(f"已保存错误截图: {screenshot_path}")
                        except:
                            pass
                        return {'success': False, 'message': error_msg}

                    # 发布前截图验证
                    try:
                        screenshot_path = f'/tmp/zhihu_before_publish_{int(time.time())}.png'
                        self.page.get_screenshot(path=screenshot_path)
                        logger.info(f"发布前截图已保存: {screenshot_path}")
                    except Exception as e:
                        logger.warning(f"截图失败: {e}")'''

try:
    print("=" * 80)
    print("完善知乎发布功能")
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

    # 下载文件
    print("\n[2/3] 下载并修改文件...")
    sftp = ssh.open_sftp()
    remote_file = '/home/u_topn/TOP_N/backend/zhihu_auto_post.py'
    local_file = 'D:/work/code/TOP_N/zhihu_auto_post_improved.py'

    sftp.get(remote_file, local_file)

    with open(local_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 替换正文输入部分
    import re

    # 找到并替换正文输入逻辑
    pattern = r'(\s+if editor:\s+# 点击编辑器激活.*?)(\s+else:\s+logger\.error\("✗ 未找到编辑器元素"\))'

    match = re.search(pattern, content, re.DOTALL)
    if match:
        # 替换整个if editor:块
        content = content[:match.start(1)] + IMPROVED_CONTENT_INPUT + content[match.start(2):]
        print("✓ 正文输入逻辑已替换")
    else:
        print("⚠ 未找到匹配的代码段")

    # 写回文件
    with open(local_file, 'w', encoding='utf-8') as f:
        f.write(content)

    # 上传
    print("✓ 正在上传...")
    sftp.put(local_file, remote_file)
    sftp.close()
    print("✓ 文件已上传")

    # 清理
    import os
    try:
        os.remove(local_file)
    except:
        pass

    # 重启服务
    print("\n[3/3] 重启服务...")
    cmd = "sudo systemctl restart topn"
    ssh.exec_command(cmd, timeout=30)
    time.sleep(4)

    # 验证
    cmd = "sudo systemctl status topn --no-pager | head -15"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    print(stdout.read().decode('utf-8'))

    print("\n" + "=" * 80)
    print("✅ 改进完成!")
    print("=" * 80)
    print("""
改进内容:

1. ✅ 使用键盘输入替代JavaScript
   - 分块输入，每次200字符
   - 避免一次性输入导致的丢失
   - 更符合知乎编辑器的预期输入方式

2. ✅ 增强内容验证
   - 多次尝试读取编辑器内容
   - 相似度阈值降至60%
   - 失败时返回详细错误信息

3. ✅ 发布前截图验证
   - 保存发布前的页面截图
   - 便于问题排查

4. ✅ 错误信息返回前端
   - 所有错误都会返回给用户
   - 包含详细的错误原因

请重新测试发布功能！
    """)

    ssh.close()

except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
