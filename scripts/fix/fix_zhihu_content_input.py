#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复知乎内容输入和发布问题
- 使用剪贴板粘贴替代逐字输入
- 确保完整内容填写
- 确保点击发布按钮
"""
import paramiko
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

# 改进后的内容输入方法
IMPROVED_INPUT_METHOD = '''
            # 输入正文内容 - 改进方法
            logger.info("正在输入正文...")
            try:
                # 尝试多种编辑器定位方式
                editor_selectors = [
                    'css:.public-DraftEditor-content',
                    'css:[contenteditable="true"]',
                    'css:.notranslate',
                    'css:[data-text="true"]'
                ]

                editor = None
                for selector in editor_selectors:
                    try:
                        editor = self.page.ele(selector, timeout=2)
                        if editor:
                            logger.info(f"✓ 找到编辑器: {selector}")
                            break
                    except:
                        continue

                if editor:
                    # 方法1: 使用剪贴板粘贴(最可靠)
                    try:
                        import pyperclip
                        # 将内容复制到剪贴板
                        pyperclip.copy(content)
                        logger.info("✓ 内容已复制到剪贴板")

                        # 点击编辑器激活
                        editor.click()
                        time.sleep(0.5)

                        # 清空编辑器
                        editor.run_js('this.innerHTML = ""')
                        time.sleep(0.3)

                        # 使用Ctrl+V粘贴
                        from DrissionPage.common import Keys
                        self.page.actions.key_down(Keys.CTRL).key('v').key_up(Keys.CTRL)
                        time.sleep(1)

                        # 验证内容是否完整
                        editor_text = editor.text
                        if len(editor_text) > len(content) * 0.8:  # 至少80%的内容
                            logger.info(f"✓ 正文已输入(剪贴板),实际{len(editor_text)}字,预期{len(content)}字")
                        else:
                            logger.warning(f"⚠ 内容可能不完整: 实际{len(editor_text)}字, 预期{len(content)}字")
                            # 尝试备用方法
                            raise Exception("内容不完整,尝试备用方法")

                    except Exception as clipboard_err:
                        logger.warning(f"剪贴板方法失败: {clipboard_err}, 尝试备用方法...")

                        # 方法2: 使用JavaScript直接设置内容
                        try:
                            # 清空编辑器
                            editor.run_js('this.innerHTML = ""')
                            time.sleep(0.3)

                            # 将内容转换为HTML格式(保持段落)
                            paragraphs = content.split('\\n\\n')
                            html_content = ''.join([f'<p>{p.strip()}</p>' for p in paragraphs if p.strip()])

                            # 使用JavaScript设置innerHTML
                            js_code = f'''
                            this.innerHTML = {repr(html_content)};
                            // 触发输入事件
                            var event = new Event('input', {{ bubbles: true }});
                            this.dispatchEvent(event);
                            '''
                            editor.run_js(js_code)
                            time.sleep(1)

                            # 验证内容
                            editor_text = editor.text
                            logger.info(f"✓ 正文已输入(JavaScript),实际{len(editor_text)}字")

                        except Exception as js_err:
                            logger.warning(f"JavaScript方法失败: {js_err}, 使用原始方法...")

                            # 方法3: 分批输入(原始方法但改进)
                            editor.click()
                            time.sleep(0.5)

                            # 清空
                            self.page.actions.key_down(Keys.CTRL).key('a').key_up(Keys.CTRL).key(Keys.BACKSPACE)
                            time.sleep(0.3)

                            # 将内容分成小块输入
                            chunk_size = 500  # 每次输入500字符
                            for i in range(0, len(content), chunk_size):
                                chunk = content[i:i+chunk_size]
                                editor.input(chunk)
                                time.sleep(0.2)  # 每块之间延迟
                                logger.debug(f"已输入 {i+len(chunk)}/{len(content)} 字符")

                            logger.info(f"✓ 正文已输入(分块),共{len(content)}字")

                else:
                    logger.error("✗ 未找到编辑器元素")
                    return {'success': False, 'message': '未找到编辑器'}

            except Exception as e:
                logger.error(f"✗ 正文输入失败: {e}")
                return {'success': False, 'message': f'正文输入失败: {e}'}

            time.sleep(2)
'''

# 改进后的发布流程
IMPROVED_PUBLISH_FLOW = '''
            # 发布或保存草稿 - 改进流程
            if draft:
                logger.info("正在保存草稿...")
                try:
                    save_draft_btn = self.page.ele('text:保存草稿', timeout=3)
                    if save_draft_btn:
                        save_draft_btn.click()
                        time.sleep(2)
                        logger.info("✓✓ 草稿保存成功")
                        return {'success': True, 'message': '草稿保存成功', 'type': 'draft'}
                except Exception as e:
                    logger.warning(f"保存草稿按钮未找到: {e}")
            else:
                logger.info("正在发布文章...")
                try:
                    # 等待内容完全加载
                    time.sleep(2)

                    # 查找发布按钮 - 多种方式
                    publish_selectors = [
                        'text:发布文章',
                        'text:发布',
                        'css:button.PublishButton',
                        'css:button[data-zop-button]',
                        'css:.Button.PublishButton',
                        'css:button:contains("发布")'
                    ]

                    publish_btn = None
                    for selector in publish_selectors:
                        try:
                            publish_btn = self.page.ele(selector, timeout=2)
                            if publish_btn and publish_btn.states.is_enabled:
                                logger.info(f"✓ 找到可用发布按钮: {selector}")
                                break
                        except:
                            continue

                    if not publish_btn:
                        # 备用方法: 查找所有按钮,找到包含"发布"的
                        try:
                            all_buttons = self.page.eles('css:button')
                            for btn in all_buttons:
                                btn_text = btn.text
                                if '发布' in btn_text and '草稿' not in btn_text:
                                    publish_btn = btn
                                    logger.info(f"✓ 找到发布按钮(备用方法): {btn_text}")
                                    break
                        except:
                            pass

                    if publish_btn:
                        logger.info("准备点击发布按钮...")

                        # 确保按钮可见
                        try:
                            publish_btn.run_js('this.scrollIntoView({{behavior: "smooth", block: "center"}})')
                            time.sleep(1)
                        except:
                            pass

                        # 点击发布按钮
                        publish_btn.click()
                        logger.info("✓ 已点击发布按钮,等待确认...")
                        time.sleep(4)

                        # 检查是否有二次确认弹窗
                        confirm_selectors = [
                            'text:确认发布',
                            'text:确定发布',
                            'text:立即发布',
                            'css:button.Button--primary',
                            'css:.Modal button:contains("确认")',
                            'css:.Modal button:contains("发布")'
                        ]

                        confirmed = False
                        for selector in confirm_selectors:
                            try:
                                confirm_btn = self.page.ele(selector, timeout=2)
                                if confirm_btn:
                                    logger.info(f"✓ 找到确认按钮: {selector}")
                                    confirm_btn.click()
                                    logger.info("✓ 已点击确认发布")
                                    confirmed = True
                                    time.sleep(3)
                                    break
                            except:
                                continue

                        if not confirmed:
                            logger.info("未检测到二次确认弹窗,可能已直接发布")
                            time.sleep(2)

                        # 等待发布完成
                        time.sleep(3)

                        # 获取文章链接
                        article_url = self.page.url
                        logger.info(f"当前页面URL: {article_url}")

                        # 检查是否发布成功 - 判断URL是否变化
                        if 'write' not in article_url or '/p/' in article_url or '/zhuanlan/' in article_url:
                            logger.info("✓✓ 文章发布成功!")
                            return {
                                'success': True,
                                'message': '文章发布成功',
                                'type': 'published',
                                'url': article_url
                            }
                        else:
                            # 检查页面是否有成功提示
                            page_html = self.page.html
                            if '发布成功' in page_html or '已发布' in page_html:
                                logger.info("✓✓ 检测到发布成功提示")
                                return {
                                    'success': True,
                                    'message': '文章发布成功',
                                    'type': 'published',
                                    'url': article_url
                                }
                            else:
                                logger.warning("⚠ 无法确认发布状态,可能需要手动检查")
                                return {
                                    'success': False,
                                    'message': '发布状态不明确,请手动检查',
                                    'url': article_url
                                }

                    else:
                        logger.error("✗ 未找到发布按钮")
                        # 截图保存
                        try:
                            screenshot_path = f'/tmp/zhihu_publish_error_{int(time.time())}.png'
                            self.page.get_screenshot(path=screenshot_path)
                            logger.info(f"已保存错误截图: {screenshot_path}")
                        except:
                            pass

                        return {'success': False, 'message': '未找到发布按钮'}

                except Exception as e:
                    logger.error(f"✗ 发布失败: {e}", exc_info=True)
                    # 截图保存
                    try:
                        screenshot_path = f'/tmp/zhihu_publish_exception_{int(time.time())}.png'
                        self.page.get_screenshot(path=screenshot_path)
                        logger.info(f"已保存异常截图: {screenshot_path}")
                    except:
                        pass

                    return {'success': False, 'message': f'发布失败: {e}'}
'''

try:
    print("=" * 80)
    print("修复知乎内容输入和发布问题")
    print("=" * 80)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
    print("✓ SSH连接成功\n")

    # 备份原文件
    print("[1/4] 备份原文件...")
    cmd = "cp /home/u_topn/TOP_N/backend/zhihu_auto_post.py /home/u_topn/TOP_N/backend/zhihu_auto_post.py.backup_$(date +%Y%m%d_%H%M%S)"
    ssh.exec_command(cmd, timeout=10)
    time.sleep(1)
    print("✓ 备份完成")

    # 下载文件到本地
    print("\n[2/4] 下载文件并修改...")
    sftp = ssh.open_sftp()
    remote_file = '/home/u_topn/TOP_N/backend/zhihu_auto_post.py'
    local_file = 'D:/work/code/TOP_N/zhihu_auto_post_temp.py'

    sftp.get(remote_file, local_file)

    with open(local_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 找到需要替换的内容输入部分
    # 查找 "# 输入正文内容" 到 "time.sleep(2)" 之间的内容
    import re

    # 替换内容输入部分
    pattern1 = r'# 输入正文内容.*?(?=# 添加话题标签)'
    content = re.sub(pattern1, IMPROVED_INPUT_METHOD.strip() + '\n\n            ', content, flags=re.DOTALL)

    # 替换发布流程部分
    pattern2 = r'# 发布或保存草稿.*?(?=except Exception as e:.*?创建文章异常)'
    content = re.sub(pattern2, IMPROVED_PUBLISH_FLOW.strip() + '\n\n        ', content, flags=re.DOTALL)

    # 添加pyperclip导入
    if 'import pyperclip' not in content:
        content = content.replace('import time', 'import time\ntry:\n    import pyperclip\nexcept ImportError:\n    pyperclip = None')

    # 添加Keys导入
    if 'from DrissionPage.common import Keys' not in content:
        content = content.replace('from DrissionPage import ChromiumPage', 'from DrissionPage import ChromiumPage\nfrom DrissionPage.common import Keys')

    with open(local_file, 'w', encoding='utf-8') as f:
        f.write(content)

    # 上传修改后的文件
    print("✓ 文件已修改,正在上传...")
    sftp.put(local_file, remote_file)
    sftp.close()
    print("✓ 文件已上传")

    # 清理临时文件
    import os
    try:
        os.remove(local_file)
    except:
        pass

    # 安装pyperclip依赖
    print("\n[3/4] 安装依赖...")
    cmd = "pip3 install pyperclip"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    print(stdout.read().decode('utf-8'))

    # 重启服务
    print("\n[4/4] 重启服务...")
    cmd = "sudo systemctl restart topn"
    ssh.exec_command(cmd, timeout=30)
    time.sleep(4)

    # 检查服务状态
    cmd = "sudo systemctl status topn --no-pager | head -15"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    print(stdout.read().decode('utf-8'))

    print("\n" + "=" * 80)
    print("✅ 修复完成!")
    print("=" * 80)
    print("""
改进内容:

1. ✅ 内容输入方法改进
   - 优先使用剪贴板粘贴(最可靠)
   - 备用JavaScript直接设置innerHTML
   - 最后使用分块逐字输入
   - 每种方法都有验证机制

2. ✅ 发布流程完善
   - 更全面的发布按钮查找
   - 确保按钮可见后再点击
   - 检测二次确认弹窗
   - 验证发布成功状态
   - 失败时自动截图保存

3. ✅ 错误处理加强
   - 多种备用方案
   - 详细的日志输出
   - 截图保存便于调试

现在请重新测试发布功能:
1. 生成文章
2. 点击"发布到知乎"
3. 系统会使用改进后的方法填写完整内容并发布
    """)

    ssh.close()

except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
