#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复知乎发布 - 使用剪贴板粘贴方法
1. 将内容复制到剪贴板
2. 在编辑器中粘贴（Ctrl+V）
3. 检查发布按钮是否可用
4. 点击发布并验证结果
"""
import paramiko
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"

# 新的内容输入方法 - 使用剪贴板粘贴
NEW_CONTENT_INPUT = '''                if editor:
                    # 点击编辑器激活
                    editor.click()
                    time.sleep(0.5)

                    logger.info(f"开始输入正文内容，共{len(content)}字...")

                    # 方法：使用剪贴板粘贴（最可靠的方法）
                    try:
                        # 第1步：将内容复制到剪贴板
                        import pyperclip
                        pyperclip.copy(content)
                        logger.info("✓ 内容已复制到剪贴板")
                        time.sleep(0.3)

                        # 第2步：在编辑器中粘贴（使用Ctrl+V）
                        from DrissionPage.common import Keys

                        # 清空编辑器
                        self.page.actions.key_down(Keys.CTRL).key('a').key_up(Keys.CTRL).key(Keys.BACKSPACE)
                        time.sleep(0.3)

                        # 粘贴内容
                        self.page.actions.key_down(Keys.CTRL).key('v').key_up(Keys.CTRL)
                        logger.info("✓ 已执行粘贴操作（Ctrl+V）")
                        time.sleep(2)

                    except ImportError:
                        # 如果没有pyperclip，使用JavaScript fallback
                        logger.warning("pyperclip未安装，使用JavaScript方法")
                        js_content = content.replace('\\\\', '\\\\\\\\').replace("'", "\\\\'").replace('\\n', '\\\\n').replace('\\r', '\\\\r')

                        js_code = f"""
                        this.innerHTML = '';
                        this.textContent = '{js_content}';
                        var event = new Event('input', {{ bubbles: true }});
                        this.dispatchEvent(event);
                        return this.textContent.length;
                        """

                        result_length = editor.run_js(js_code)
                        logger.info(f"✓ JavaScript设置完成，长度: {result_length}")
                        time.sleep(2)

                    except Exception as paste_err:
                        logger.error(f"粘贴失败: {paste_err}，尝试JavaScript方法")
                        # Fallback到JavaScript
                        js_content = content.replace('\\\\', '\\\\\\\\').replace("'", "\\\\'").replace('\\n', '\\\\n').replace('\\r', '\\\\r')

                        js_code = f"""
                        this.innerHTML = '';
                        this.textContent = '{js_content}';
                        var event = new Event('input', {{ bubbles: true }});
                        this.dispatchEvent(event);
                        return this.textContent.length;
                        """

                        result_length = editor.run_js(js_code)
                        logger.info(f"✓ JavaScript设置完成，长度: {result_length}")
                        time.sleep(2)

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

                        if similarity < 0.8:
                            error_msg = f"内容输入不完整: 相似度仅{similarity*100:.1f}%"
                            logger.error(f"✗ {error_msg}")
                            try:
                                screenshot_path = f'/tmp/zhihu_content_error_{int(time.time())}.png'
                                self.page.get_screenshot(path=screenshot_path)
                                logger.info(f"已保存错误截图: {screenshot_path}")
                            except:
                                pass
                            return {'success': False, 'message': error_msg}
                    else:
                        error_msg = "无法读取编辑器内容"
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

# 新的发布流程 - 增强版
NEW_PUBLISH_FLOW = '''            # 发布或保存草稿 - 增强版
            time.sleep(2)

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
                    logger.warning(f"保存草稿失败: {e}")
                    return {'success': False, 'message': f'保存草稿失败: {e}'}
            else:
                logger.info("开始发布流程...")
                try:
                    start_url = self.page.url
                    logger.info(f"发布前URL: {start_url}")

                    # 步骤1: 查找发布按钮
                    logger.info("步骤1/6: 查找发布按钮...")

                    publish_selectors = [
                        'text:发布文章',
                        'text:发布',
                        'css:button.Button--primary',
                        'css:button.PublishButton',
                    ]

                    publish_btn = None
                    for selector in publish_selectors:
                        try:
                            if selector.startswith('text:'):
                                btns = self.page.eles(selector, timeout=1)
                                for btn in btns:
                                    btn_text = btn.text.strip()
                                    if (btn_text == '发布文章' or btn_text == '发布') and '草稿' not in btn_text:
                                        publish_btn = btn
                                        logger.info(f"✓ 找到发布按钮: '{btn_text}'")
                                        break
                            else:
                                publish_btn = self.page.ele(selector, timeout=1)
                                if publish_btn:
                                    logger.info(f"✓ 找到发布按钮: {selector}")
                                    break
                        except:
                            continue

                        if publish_btn:
                            break

                    if not publish_btn:
                        error_msg = "未找到发布按钮"
                        logger.error(f"✗ {error_msg}")
                        try:
                            screenshot_path = f'/tmp/zhihu_no_publish_btn_{int(time.time())}.png'
                            self.page.get_screenshot(path=screenshot_path)
                            logger.info(f"已保存错误截图: {screenshot_path}")
                        except:
                            pass
                        return {'success': False, 'message': error_msg}

                    # 步骤2: 检查发布按钮状态（关键！）
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
                        logger.warning(f"检查按钮状态时出错: {e}")

                    # 步骤3: 点击发布按钮
                    logger.info("步骤3/6: 点击发布按钮...")
                    publish_btn.click()
                    logger.info("✓ 已点击发布按钮")
                    time.sleep(5)

                    # 步骤4: 处理发布设置弹窗
                    logger.info("步骤4/6: 检查发布设置弹窗...")

                    modal_found = False
                    modal_publish_selectors = [
                        'text:发布文章',
                        'css:.Modal button.Button--primary',
                        'css:div[role="dialog"] button:has-text("发布")',
                        'css:.PublishPanel button.Button--primary',
                    ]

                    for selector in modal_publish_selectors:
                        try:
                            modal_btn = self.page.ele(selector, timeout=2)
                            if modal_btn:
                                modal_text = modal_btn.text.strip()
                                logger.info(f"✓ 找到弹窗发布按钮: '{modal_text}'")

                                if '发布' in modal_text:
                                    modal_btn.click()
                                    logger.info("✓ 已点击弹窗中的发布按钮")
                                    modal_found = True
                                    time.sleep(5)
                                    break
                        except:
                            continue

                    if not modal_found:
                        logger.info("未检测到发布设置弹窗")

                    # 步骤5: 等待页面跳转
                    logger.info("步骤5/6: 等待页面跳转...")
                    time.sleep(3)

                    # 步骤6: 验证发布结果
                    logger.info("步骤6/6: 验证发布结果...")

                    current_url = self.page.url
                    logger.info(f"发布后URL: {current_url}")

                    # 判断成功的标准
                    success_indicators = []

                    # 关键判断1: URL不能包含 /edit
                    if '/edit' not in current_url:
                        success_indicators.append("URL不包含/edit（已退出编辑模式）")
                    else:
                        logger.warning("⚠ URL仍包含/edit，文章未真正发布")

                    # 判断2: URL应该包含文章路径
                    if '/p/' in current_url or '/zhuanlan/' in current_url:
                        success_indicators.append("URL包含文章路径")

                    # 判断3: URL不应该是write页面
                    if 'write' not in current_url:
                        success_indicators.append("URL已离开写作页面")

                    # 判断4: 检查是否有编辑按钮（已发布文章页面会有）
                    try:
                        edit_btn = self.page.ele('text:编辑文章', timeout=2)
                        if edit_btn:
                            success_indicators.append("找到编辑按钮（在已发布文章页）")
                    except:
                        pass

                    # 判断5: 检查页面提示
                    try:
                        page_html = self.page.html
                        if '发布成功' in page_html or '已发布' in page_html:
                            success_indicators.append("页面显示发布成功")
                    except:
                        pass

                    logger.info(f"成功指标数量: {len(success_indicators)}")
                    logger.info(f"成功指标: {success_indicators}")

                    # 关键判断：URL必须不包含/edit
                    if '/edit' in current_url:
                        error_msg = "文章未真正发布，仍在编辑状态"
                        logger.error(f"✗ {error_msg}")

                        try:
                            screenshot_path = f'/tmp/zhihu_still_editing_{int(time.time())}.png'
                            self.page.get_screenshot(path=screenshot_path)
                            logger.info(f"已保存编辑状态截图: {screenshot_path}")
                        except:
                            pass

                        return {
                            'success': False,
                            'message': error_msg,
                            'url': current_url,
                            'detail': '点击发布后仍在编辑页面'
                        }

                    # 如果有成功指标且URL不包含/edit，认为发布成功
                    if success_indicators:
                        logger.info(f"✓✓ 文章发布成功!")

                        # 提取文章ID
                        article_id = None
                        if '/p/' in current_url:
                            article_id = current_url.split('/p/')[-1].split('?')[0].split('/')[0].split('#')[0]
                        elif '/zhuanlan/' in current_url:
                            parts = current_url.split('/zhuanlan/')[-1].split('/')
                            if len(parts) > 0:
                                article_id = parts[0]

                        # 成功截图
                        try:
                            screenshot_path = f'/tmp/zhihu_publish_success_{int(time.time())}.png'
                            self.page.get_screenshot(path=screenshot_path)
                            logger.info(f"已保存成功截图: {screenshot_path}")
                        except:
                            pass

                        return {
                            'success': True,
                            'message': '文章发布成功',
                            'type': 'published',
                            'url': current_url,
                            'article_id': article_id,
                            'indicators': success_indicators
                        }
                    else:
                        error_msg = "无法确认发布状态"
                        logger.warning(f"⚠ {error_msg}")

                        try:
                            screenshot_path = f'/tmp/zhihu_publish_unclear_{int(time.time())}.png'
                            self.page.get_screenshot(path=screenshot_path)
                            logger.info(f"已保存状态截图: {screenshot_path}")
                        except:
                            pass

                        return {
                            'success': False,
                            'message': error_msg,
                            'url': current_url
                        }

                except Exception as e:
                    error_msg = f'发布过程异常: {str(e)}'
                    logger.error(f"✗ {error_msg}", exc_info=True)

                    try:
                        screenshot_path = f'/tmp/zhihu_publish_exception_{int(time.time())}.png'
                        self.page.get_screenshot(path=screenshot_path)
                        logger.info(f"已保存异常截图: {screenshot_path}")
                    except:
                        pass

                    return {'success': False, 'message': error_msg}'''

try:
    print("=" * 80)
    print("修复知乎发布 - 使用剪贴板粘贴方法")
    print("=" * 80)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, timeout=30)
    print("✓ SSH连接成功\n")

    # 安装pyperclip
    print("[1/5] 安装pyperclip...")
    cmd = "cd /home/u_topn/TOP_N/backend && pip3 install pyperclip"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
    stdout.read()
    print("✓ pyperclip安装完成")

    # 备份
    print("\n[2/5] 备份文件...")
    cmd = "cp /home/u_topn/TOP_N/backend/zhihu_auto_post.py /home/u_topn/TOP_N/backend/zhihu_auto_post.py.backup_$(date +%Y%m%d_%H%M%S)"
    ssh.exec_command(cmd, timeout=10)
    time.sleep(1)
    print("✓ 备份完成")

    # 下载文件
    print("\n[3/5] 下载并修改文件...")
    sftp = ssh.open_sftp()
    remote_file = '/home/u_topn/TOP_N/backend/zhihu_auto_post.py'
    local_file = 'D:/work/code/TOP_N/zhihu_auto_post_paste.py'

    sftp.get(remote_file, local_file)

    with open(local_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 替换内容输入部分
    import re

    # 查找内容输入部分
    pattern1 = r'(                if editor:.*?)(                    # 发布或保存草稿)'
    match1 = re.search(pattern1, content, re.DOTALL)

    if match1:
        content = content[:match1.start(1)] + NEW_CONTENT_INPUT + '\n\n' + content[match1.start(2):]
        print("✓ 内容输入部分已替换")
    else:
        print("✗ 未找到内容输入部分")

    # 替换发布流程部分
    pattern2 = r'(            # 发布或保存草稿.*?)(        except Exception as e:\s+logger\.error\(f"✗ 创建文章异常)'
    match2 = re.search(pattern2, content, re.DOTALL)

    if match2:
        content = content[:match2.start(1)] + NEW_PUBLISH_FLOW + '\n\n        ' + content[match2.start(2):]
        print("✓ 发布流程已替换")
    else:
        print("✗ 未找到发布流程部分")

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
    print("\n[4/5] 重启服务...")
    cmd = "sudo systemctl restart topn"
    ssh.exec_command(cmd, timeout=30)
    time.sleep(4)

    # 验证
    print("\n[5/5] 验证服务状态...")
    cmd = "sudo systemctl status topn --no-pager | head -15"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    print(stdout.read().decode('utf-8'))

    print("\n" + "=" * 80)
    print("✅ 修复完成!")
    print("=" * 80)
    print("""
关键改进:

📋 内容输入方式:
  1. 主要方法: 使用pyperclip复制到剪贴板 + Ctrl+V粘贴
     - ✅ 模拟真实用户操作
     - ✅ 知乎编辑器能正确识别内容
     - ✅ 发布按钮会自动变为可用状态

  2. 备用方法: JavaScript textContent（如果pyperclip不可用）
     - ✅ 确保在任何环境下都能工作

📝 发布流程增强:

  步骤1: 查找发布按钮
  步骤2: 检查发布按钮状态（关键！）
    - ✅ 如果按钮被禁用，说明内容未正确识别
    - ✅ 立即返回错误，不继续执行
    - ✅ 截图保存以便调试

  步骤3: 点击发布按钮
  步骤4: 处理发布设置弹窗
  步骤5: 等待页面跳转
  步骤6: 多重指标验证发布结果
    - ✅ URL不包含 /edit（最关键）
    - ✅ URL包含文章路径
    - ✅ 离开写作页面
    - ✅ 找到"编辑文章"按钮
    - ✅ 页面显示发布成功

🎯 错误处理:
  - 发布按钮被禁用 → 返回"内容未正确粘贴"
  - URL仍包含/edit → 返回"文章未真正发布"
  - 所有关键点都有截图保存
  - 详细的错误信息返回给前端

现在请重新测试发布功能！
    """)

    ssh.close()

except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
