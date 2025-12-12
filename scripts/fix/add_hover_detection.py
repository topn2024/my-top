#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加鼠标悬浮检测功能到发布按钮状态检查
"""
import paramiko
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"

print("=" * 80)
print("添加发布按钮鼠标悬浮检测功能")
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
    local_file = 'D:/work/code/TOP_N/zhihu_auto_post_hover.py'

    sftp.get(remote_file, local_file)

    with open(local_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 替换步骤2的按钮检测代码
    old_code = """logger.info("步骤2/5: 检查发布按钮状态...")
                    try:
                        # 滚动到按钮
                        publish_btn.run_js('this.scrollIntoView({behavior: "smooth", block: "center"})')
                        time.sleep(1)

                        # 检查是否禁用
                        is_disabled = publish_btn.attr('disabled')
                        if is_disabled:
                            error_msg = "发布按钮被禁用，内容可能未填写完整"
                            logger.error(f"✗ {error_msg}")
                            return {'success': False, 'message': error_msg}

                        logger.info("✓ 发布按钮可用")
                    except Exception as e:
                        logger.warning(f"检查按钮状态时出错: {e}")"""

    new_code = """logger.info("步骤2/5: 检查发布按钮状态...")
                    try:
                        # 滚动到按钮
                        publish_btn.run_js('this.scrollIntoView({behavior: "smooth", block: "center"})')
                        time.sleep(1)

                        # 方法1: 检查disabled属性
                        is_disabled = publish_btn.attr('disabled')

                        # 方法2: 鼠标悬浮检测真实可点击状态
                        try:
                            # 移动鼠标到按钮上
                            self.page.actions.move_to(publish_btn)
                            time.sleep(0.5)

                            # 检查按钮样式
                            cursor_style = publish_btn.run_js('return window.getComputedStyle(this).cursor')
                            pointer_events = publish_btn.run_js('return window.getComputedStyle(this).pointerEvents')

                            logger.info(f"按钮状态: disabled={is_disabled}, cursor={cursor_style}, pointer-events={pointer_events}")

                            # 判断是否真正可点击
                            is_clickable = (
                                not is_disabled and
                                cursor_style == 'pointer' and
                                pointer_events != 'none'
                            )

                            if not is_clickable:
                                error_msg = f"发布按钮不可点击（disabled={is_disabled}, cursor={cursor_style}）"
                                logger.error(f"✗ {error_msg}")
                                try:
                                    screenshot_path = f'/tmp/zhihu_btn_not_clickable_{int(time.time())}.png'
                                    self.page.get_screenshot(path=screenshot_path)
                                    logger.info(f"已保存截图: {screenshot_path}")
                                except:
                                    pass
                                return {'success': False, 'message': error_msg}

                            logger.info("✓ 发布按钮可点击（悬浮检测通过）")

                        except Exception as hover_err:
                            logger.warning(f"鼠标悬浮检测失败: {hover_err}，使用disabled属性判断")
                            if is_disabled:
                                error_msg = "发布按钮被禁用"
                                logger.error(f"✗ {error_msg}")
                                return {'success': False, 'message': error_msg}

                            logger.info("✓ 发布按钮未禁用")

                    except Exception as e:
                        logger.warning(f"检查按钮状态时出错: {e}")"""

    if old_code in content:
        content = content.replace(old_code, new_code)
        print("✓ 已添加鼠标悬浮检测功能\n")
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
    print("✅ 鼠标悬浮检测功能添加完成!")
    print("=" * 80)
    print("""
现在发布按钮检测会：
1. 检查 disabled 属性
2. 模拟鼠标悬浮到按钮上
3. 检查 cursor 样式（应为 pointer）
4. 检查 pointer-events（不应为 none）
5. 综合判断按钮是否真正可点击

只有当按钮真正可点击时才会继续发布流程！
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
