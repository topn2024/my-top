#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复知乎内容输入 - 使用JavaScript直接设置文本内容
避免input()方法的问题
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
    print("修复知乎内容输入问题 - 使用JavaScript设置文本")
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
    local_file = 'D:/work/code/TOP_N/zhihu_auto_post_fixed.py'

    sftp.get(remote_file, local_file)

    with open(local_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 定位并替换内容输入部分（第160-220行之间的内容输入和验证逻辑）
    old_input_section = '''                if editor:
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

    new_input_section = '''                if editor:
                    # 点击编辑器激活
                    editor.click()
                    time.sleep(0.5)

                    logger.info(f"开始输入正文内容，共{len(content)}字...")

                    # 方法：使用JavaScript直接设置textContent（最可靠）
                    # 知乎编辑器是contenteditable的div，直接设置文本内容
                    try:
                        # 转义JavaScript字符串中的特殊字符
                        js_content = content.replace('\\\\', '\\\\\\\\').replace("'", "\\\\'").replace('\\n', '\\\\n').replace('\\r', '\\\\r')

                        # 使用JavaScript设置文本内容
                        js_code = f"""
                        // 清空编辑器
                        this.innerHTML = '';

                        // 设置文本内容（会自动创建文本节点）
                        this.textContent = '{js_content}';

                        // 触发input事件通知编辑器内容变化
                        var event = new Event('input', {{ bubbles: true }});
                        this.dispatchEvent(event);

                        // 返回实际字符数用于验证
                        return this.textContent.length;
                        """

                        result_length = editor.run_js(js_code)
                        time.sleep(2)

                        logger.info(f"✓ JavaScript设置完成，返回长度: {result_length}")

                    except Exception as js_err:
                        error_msg = f"JavaScript设置内容失败: {js_err}"
                        logger.error(f"✗ {error_msg}")
                        return {'success': False, 'message': error_msg}

                    # 验证内容 - 多次尝试读取
                    editor_text = None
                    for attempt in range(3):
                        time.sleep(0.5)
                        try:
                            editor_text = editor.text
                            if editor_text and len(editor_text) > 100:
                                break
                        except:
                            logger.warning(f"第{attempt+1}次读取编辑器内容失败，重试...")

                    if editor_text:
                        content_text = content.replace('\\n\\n', '').replace('\\n', '').replace('\\r', '')
                        editor_text_clean = editor_text.replace('\\n', '').replace('\\r', '')
                        similarity = len(editor_text_clean) / max(len(content_text), 1)

                        logger.info(f"✓ 正文验证: 编辑器{len(editor_text)}字 / 原文{len(content)}字 / 相似度{similarity*100:.1f}%")

                        if similarity < 0.8:  # 提高阈值到80%
                            error_msg = f"内容输入不完整: 相似度仅{similarity*100:.1f}%，编辑器{len(editor_text)}字，原文{len(content)}字"
                            logger.error(f"✗ {error_msg}")
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

    # 执行替换
    if old_input_section in content:
        content = content.replace(old_input_section, new_input_section)
        print("✓ 内容输入逻辑已替换")
    else:
        print("⚠ 未找到精确匹配，尝试使用正则替换...")
        import re
        # 使用更灵活的正则匹配
        pattern = r'(if editor:\s+# 点击编辑器激活.*?)(else:\s+logger\.error\("✗ 未找到编辑器元素"\))'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            content = content[:match.start(1)] + new_input_section + '\n                ' + content[match.start(2):]
            print("✓ 使用正则表达式替换成功")
        else:
            print("✗ 无法找到替换位置，退出")
            sys.exit(1)

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
    print("✅ 修复完成!")
    print("=" * 80)
    print("""
改进内容:

1. ✅ 使用JavaScript的textContent直接设置
   - 避免了input()方法的覆盖问题
   - 一次性设置完整内容，不分块
   - 自动处理换行符

2. ✅ JavaScript字符串转义
   - 正确转义特殊字符（引号、换行、反斜杠）
   - 确保内容完整传递

3. ✅ 改进验证机制
   - 相似度阈值提高到80%（更严格）
   - 清理换行符后再比较
   - JavaScript返回实际字符数

4. ✅ 触发input事件
   - 通知知乎编辑器内容已变化
   - 确保编辑器正确识别内容

请重新测试发布功能！
    """)

    ssh.close()

except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
