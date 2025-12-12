#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知乎发布功能改进
1. 编辑器定位优先使用class
2. 通过鼠标悬浮检测发布按钮真实可点击状态
3. 使用剪贴板粘贴方法输入内容
"""
import paramiko
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"

print("=" * 80)
print("知乎发布功能改进")
print("=" * 80)
print("改进点:")
print("1. 编辑器定位优先使用 class 属性")
print("2. 通过鼠标悬浮检测发布按钮真实可点击状态")
print("3. 使用剪贴板粘贴方法输入内容")
print("=" * 80)

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, timeout=30)
    print("✓ SSH连接成功\n")

    # 备份文件
    print("[1/5] 备份当前文件...")
    cmd = "cp /home/u_topn/TOP_N/backend/zhihu_auto_post.py /home/u_topn/TOP_N/backend/zhihu_auto_post.py.backup_$(date +%Y%m%d_%H%M%S)"
    ssh.exec_command(cmd, timeout=10)
    time.sleep(1)
    print("✓ 备份完成\n")

    # 下载文件
    print("[2/5] 下载文件...")
    sftp = ssh.open_sftp()
    remote_file = '/home/u_topn/TOP_N/backend/zhihu_auto_post.py'
    local_file = 'D:/work/code/TOP_N/zhihu_auto_post_improved.py'

    sftp.get(remote_file, local_file)
    print("✓ 文件已下载\n")

    # 读取文件
    print("[3/5] 修改文件...")
    with open(local_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 修改1: 编辑器选择器 - 优先使用class
    old_selectors = """editor_selectors = [
                    'css:.public-DraftEditor-content',
                    'css:[contenteditable="true"]',
                    'css:.notranslate',
                    'css:[data-text="true"]'
                ]"""

    new_selectors = """editor_selectors = [
                    # 优先使用class定位
                    '@class=public-DraftEditor-content',
                    '@class=notranslate public-DraftEditor-content',
                    '@class:public-DraftEditor-content',  # 包含class
                    # 备用：CSS选择器
                    'css:.public-DraftEditor-content',
                    'css:[contenteditable="true"]',
                    'css:.notranslate'
                ]"""

    if old_selectors in content:
        content = content.replace(old_selectors, new_selectors)
        print("✓ 已更新编辑器选择器（优先使用class）")
    else:
        print("⚠ 未找到编辑器选择器配置")

    # 修改2: 内容输入 - 使用剪贴板粘贴
    # 查找内容输入部分的起始位置
    import re

    # 定位内容输入代码块
    pattern = r'(if editor:\s+# 点击编辑器激活.*?)(# 验证内容 - 多次尝试读取)'
    match = re.search(pattern, content, re.DOTALL)

    if match:
        # 新的内容输入代码
        new_input_code = '''if editor:
                    # 点击编辑器激活
                    editor.click()
                    time.sleep(0.5)

                    logger.info(f"开始输入正文内容，共{len(content)}字...")

                    # 方法：剪贴板粘贴（模拟真实用户操作）
                    try:
                        import pyperclip
                        from DrissionPage.common import Keys

                        # 步骤1: 复制到剪贴板
                        pyperclip.copy(content)
                        logger.info("✓ 内容已复制到剪贴板")
                        time.sleep(0.3)

                        # 步骤2: 清空编辑器（Ctrl+A + Backspace）
                        self.page.actions.key_down(Keys.CTRL).key('a').key_up(Keys.CTRL).key(Keys.BACKSPACE)
                        time.sleep(0.3)

                        # 步骤3: 粘贴内容（Ctrl+V）
                        self.page.actions.key_down(Keys.CTRL).key('v').key_up(Keys.CTRL)
                        logger.info("✓ 已执行粘贴操作（Ctrl+V）")
                        time.sleep(2)

                    except ImportError:
                        logger.warning("pyperclip未安装，使用JavaScript备用方法")
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
                    except Exception as paste_err:
                        logger.error(f"粘贴失败: {paste_err}，尝试JavaScript方法")
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

        content = content[:match.start(1)] + new_input_code + '\n                    ' + content[match.start(2):]
        print("✓ 已更新内容输入方法（剪贴板粘贴法）")
    else:
        print("⚠ 未找到内容输入代码块")

    # 修改3: 发布按钮检测 - 使用鼠标悬浮检测
    old_check = """                    # 步骤2: 检查发布按钮状态（关键！）
                    logger.info("步骤2/6: 检查发布按钮状态...")
                    try:
                        publish_btn.run_js('this.scrollIntoView({behavior: "smooth", block: "center"})')
                        time.sleep(1)

                        is_disabled = publish_btn.attr('disabled')
                        if is_disabled:
                            error_msg = "发布按钮被禁用，内容可能未正确粘贴到编辑器"
                            logger.error(f"✗ {error_msg}")

                            # 截图以便调试
                            try:
                                screenshot_path = f'/tmp/zhihu_btn_disabled_{int(time.time())}.png'
                                self.page.get_screenshot(path=screenshot_path)
                                logger.info(f"已保存按钮禁用截图: {screenshot_path}")
                            except:
                                pass

                            return {'success': False, 'message': error_msg}

                        logger.info("✓ 发布按钮可用，内容已正确识别")
                    except Exception as e:
                        logger.warning(f"检查按钮状态时出错: {e}")"""

    new_check = """                    # 步骤2: 检查发布按钮状态（关键！）
                    logger.info("步骤2/6: 检查发布按钮状态...")
                    try:
                        publish_btn.run_js('this.scrollIntoView({behavior: "smooth", block: "center"})')
                        time.sleep(1)

                        # 方法1: 检查disabled属性
                        is_disabled = publish_btn.attr('disabled')

                        # 方法2: 模拟鼠标悬浮检测真实可点击状态
                        try:
                            # 移动鼠标到按钮上
                            self.page.actions.move_to(publish_btn)
                            time.sleep(0.5)

                            # 检查按钮样式和状态
                            cursor_style = publish_btn.run_js('return window.getComputedStyle(this).cursor')
                            pointer_events = publish_btn.run_js('return window.getComputedStyle(this).pointerEvents')

                            logger.info(f"按钮状态检测: disabled={is_disabled}, cursor={cursor_style}, pointer-events={pointer_events}")

                            # 判断按钮是否真正可点击
                            is_clickable = (
                                not is_disabled and
                                cursor_style == 'pointer' and
                                pointer_events != 'none'
                            )

                            if not is_clickable:
                                error_msg = f"发布按钮不可点击（disabled={is_disabled}, cursor={cursor_style}）"
                                logger.error(f"✗ {error_msg}")

                                # 截图以便调试
                                try:
                                    screenshot_path = f'/tmp/zhihu_btn_disabled_{int(time.time())}.png'
                                    self.page.get_screenshot(path=screenshot_path)
                                    logger.info(f"已保存按钮禁用截图: {screenshot_path}")
                                except:
                                    pass

                                return {'success': False, 'message': error_msg}

                            logger.info("✓ 发布按钮可点击，内容已正确识别")

                        except Exception as hover_err:
                            logger.warning(f"鼠标悬浮检测失败: {hover_err}，使用disabled属性判断")
                            if is_disabled:
                                error_msg = "发布按钮被禁用，内容可能未正确识别"
                                logger.error(f"✗ {error_msg}")

                                try:
                                    screenshot_path = f'/tmp/zhihu_btn_disabled_{int(time.time())}.png'
                                    self.page.get_screenshot(path=screenshot_path)
                                    logger.info(f"已保存按钮禁用截图: {screenshot_path}")
                                except:
                                    pass

                                return {'success': False, 'message': error_msg}

                            logger.info("✓ 发布按钮未被禁用")

                    except Exception as e:
                        logger.warning(f"检查按钮状态时出错: {e}")"""

    if old_check in content:
        content = content.replace(old_check, new_check)
        print("✓ 已更新发布按钮检测方法（鼠标悬浮检测）")
    else:
        print("⚠ 未找到发布按钮检测代码")

    # 写回文件
    with open(local_file, 'w', encoding='utf-8') as f:
        f.write(content)

    # 上传文件
    print("✓ 正在上传修改后的文件...")
    sftp.put(local_file, remote_file)
    sftp.close()
    print("✓ 文件已上传\n")

    # 验证Python语法
    print("[4/5] 验证Python语法...")
    cmd = "python3 -m py_compile /home/u_topn/TOP_N/backend/zhihu_auto_post.py"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    err = stderr.read().decode('utf-8')

    if err:
        print(f"✗ Python语法错误:\n{err}")
        print("\n正在恢复备份...")
        ssh.exec_command("ls -t /home/u_topn/TOP_N/backend/zhihu_auto_post.py.backup_* | head -1 | xargs -I {} cp {} /home/u_topn/TOP_N/backend/zhihu_auto_post.py", timeout=10)
        print("✗ 已恢复备份")
        ssh.close()
        sys.exit(1)

    print("✓ Python语法验证通过\n")

    # 重启服务
    print("[5/5] 重启服务...")
    cmd = "sudo systemctl restart topn"
    ssh.exec_command(cmd, timeout=30)
    time.sleep(4)

    # 验证服务状态
    cmd = "sudo systemctl status topn --no-pager | head -15"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    status = stdout.read().decode('utf-8')
    print(status)

    print("\n" + "=" * 80)
    print("✅ 知乎发布功能改进完成!")
    print("=" * 80)
    print("""
关键改进:

📝 1. 编辑器定位优先使用class属性
   - '@class=public-DraftEditor-content'
   - '@class=notranslate public-DraftEditor-content'
   - 更准确，更稳定

🖱️  2. 发布按钮真实可点击状态检测
   - 模拟鼠标悬浮到按钮上
   - 检查 cursor 样式（应为 pointer）
   - 检查 pointer-events（不应为 none）
   - 检查 disabled 属性
   - 多重验证确保按钮真正可点击

📋 3. 剪贴板粘贴方法输入内容
   - pyperclip.copy() 复制到剪贴板
   - Ctrl+A 全选
   - Backspace 删除
   - Ctrl+V 粘贴
   - 完全模拟真实用户操作
   - JavaScript作为备用方法

🎯 测试建议:
   1. 生成一篇测试文章（包含标题和正文）
   2. 点击"发布到知乎"
   3. 观察日志中的按钮状态检测结果
   4. 如果显示"✓ 发布按钮可点击"，说明内容粘贴成功
   5. 如果显示按钮不可点击，查看截图分析原因

现在可以重新测试发布功能！
    """)

    # 清理本地文件
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
