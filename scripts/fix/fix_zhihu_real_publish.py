#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复知乎真正发布问题
- 点击发布后，文章应该从编辑状态转为发布状态
- URL应该从 /edit 变为正式的文章页面
"""
import paramiko
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

# 修复后的发布流程 - 确保真正发布
FIXED_PUBLISH_CODE = '''
            # 发布或保存草稿 - 真正发布版本
            time.sleep(2)  # 确保内容已完全输入

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
                    # 记录当前URL
                    start_url = self.page.url
                    logger.info(f"发布前URL: {start_url}")

                    # 第一步：查找并点击发布按钮
                    logger.info("步骤1/5: 查找发布按钮...")

                    # 知乎发布按钮选择器
                    publish_selectors = [
                        'text:发布文章',
                        'text:发布',
                        'css:button.Button--primary:has-text("发布")',
                        'css:button.PublishButton',
                    ]

                    publish_btn = None
                    for selector in publish_selectors:
                        try:
                            if selector.startswith('text:'):
                                # 查找所有匹配文本的按钮
                                btns = self.page.eles(selector, timeout=1)
                                for btn in btns:
                                    btn_text = btn.text.strip()
                                    # 必须是"发布文章"或者单纯的"发布"，不能包含"草稿"
                                    if (btn_text == '发布文章' or btn_text == '发布') and '草稿' not in btn_text:
                                        publish_btn = btn
                                        logger.info(f"✓ 找到发布按钮: 文本='{btn_text}'")
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

                    # 第二步：检查按钮状态
                    logger.info("步骤2/5: 检查发布按钮状态...")
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
                        logger.warning(f"检查按钮状态时出错: {e}")

                    # 第三步：点击发布按钮
                    logger.info("步骤3/5: 点击发布按钮...")
                    publish_btn.click()
                    logger.info("✓ 已点击发布按钮，等待页面响应...")
                    time.sleep(5)  # 增加等待时间

                    # 第四步：处理发布设置弹窗（重要！）
                    logger.info("步骤4/5: 检查发布设置弹窗...")

                    # 知乎可能会弹出"发布设置"对话框，需要再次点击"发布文章"
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
                                logger.info(f"✓ 找到弹窗中的发布按钮: '{modal_text}'")

                                # 确保这是发布设置对话框中的按钮
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

                    # 第五步：验证发布结果
                    logger.info("步骤5/5: 验证发布结果...")
                    time.sleep(3)

                    current_url = self.page.url
                    logger.info(f"发布后URL: {current_url}")

                    # 判断发布成功的标准
                    success_indicators = []

                    # 1. URL必须不包含 /edit（关键！）
                    if '/edit' not in current_url:
                        success_indicators.append("URL不包含/edit（已退出编辑模式）")
                    else:
                        logger.warning("⚠ URL仍然包含/edit，文章可能未真正发布")

                    # 2. URL应该包含文章ID
                    if '/p/' in current_url or '/zhuanlan/' in current_url:
                        success_indicators.append("URL包含文章路径")

                    # 3. URL应该不是write页面
                    if 'write' not in current_url:
                        success_indicators.append("URL已离开写作页面")

                    # 4. 检查页面是否有编辑按钮（发布后的文章页会有编辑按钮）
                    try:
                        # 如果能找到"编辑文章"按钮，说明在文章查看页面
                        edit_btn = self.page.ele('text:编辑文章', timeout=2)
                        if edit_btn:
                            success_indicators.append("找到文章编辑按钮（说明在已发布文章页面）")
                    except:
                        pass

                    # 5. 检查是否有发布成功的提示
                    try:
                        page_html = self.page.html
                        if '发布成功' in page_html or '已发布' in page_html:
                            success_indicators.append("页面显示发布成功")
                    except:
                        pass

                    # 综合判断
                    logger.info(f"成功指标数量: {len(success_indicators)}")
                    logger.info(f"成功指标: {success_indicators}")

                    # 关键判断：URL不能包含/edit
                    if '/edit' in current_url:
                        error_msg = "文章未真正发布，仍在编辑状态"
                        logger.error(f"✗ {error_msg}")

                        # 截图
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
                            'detail': '点击发布后仍在编辑页面，可能是发布设置弹窗未正确处理'
                        }

                    # 如果有任何成功指标且URL不包含/edit，认为发布成功
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

                        # 最终截图
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
                        # 没有任何成功指标
                        error_msg = "无法确认发布状态，未找到成功指标"
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

                    return {'success': False, 'message': error_msg}
'''

try:
    print("=" * 80)
    print("修复知乎真正发布问题")
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
    local_file = 'D:/work/code/TOP_N/zhihu_auto_post_real_publish.py'

    sftp.get(remote_file, local_file)

    with open(local_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 替换发布流程
    import re

    pattern = r'(            # 发布或保存草稿.*?)(        except Exception as e:\s+logger\.error\(f"✗ 创建文章异常)'
    match = re.search(pattern, content, re.DOTALL)

    if match:
        content = content[:match.start(1)] + FIXED_PUBLISH_CODE.strip() + '\n\n        ' + content[match.start(2):]
        print("✓ 发布流程已替换")
    else:
        print("✗ 未找到匹配的代码段")
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
关键修复:

1. ✅ 增加发布设置弹窗检测（步骤4）
   - 知乎在点击发布后可能弹出"发布设置"对话框
   - 需要在弹窗中再次点击"发布文章"按钮
   - 这是之前缺失的关键步骤

2. ✅ 严格的URL验证
   - 发布成功的URL不能包含 /edit
   - 如果URL包含 /edit，直接判定为发布失败
   - 返回详细错误信息

3. ✅ 增加"编辑文章"按钮检测
   - 发布后的文章页面会有"编辑文章"按钮
   - 这是判断是否在已发布文章页的有效指标

4. ✅ 增加等待时间
   - 点击发布后等待5秒（原来3秒）
   - 给知乎足够时间处理发布请求

5. ✅ 详细的错误日志
   - 记录发布前后的URL对比
   - 列出所有成功指标
   - 截图保存关键状态

现在请重新测试发布功能！
    """)

    ssh.close()

except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
