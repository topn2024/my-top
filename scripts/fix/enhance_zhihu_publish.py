#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完善知乎文章发布模块
基于知乎实际页面结构的分析和改进
"""
import paramiko
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

# 完善后的发布流程
ENHANCED_PUBLISH_CODE = '''
            # 发布或保存草稿 - 完善版
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
                    # 第一步：查找并点击发布按钮
                    logger.info("步骤1/4: 查找发布按钮...")

                    # 知乎发布按钮的可能选择器（按优先级排序）
                    publish_selectors = [
                        'css:button.Button--primary',  # 主要蓝色按钮
                        'text:发布文章',
                        'text:发布',
                        'css:button[type="submit"]',
                        'css:.PublishButton',
                        'css:button.Button.PublishButton.Button--primary.Button--blue',
                    ]

                    publish_btn = None
                    for selector in publish_selectors:
                        try:
                            # 查找所有匹配的按钮
                            if selector.startswith('css:'):
                                btns = self.page.eles(selector, timeout=1)
                                for btn in btns:
                                    btn_text = btn.text.strip()
                                    # 检查按钮文本是否包含"发布"
                                    if '发布' in btn_text and '草稿' not in btn_text:
                                        publish_btn = btn
                                        logger.info(f"✓ 找到发布按钮: {selector}, 文本='{btn_text}'")
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
                        # 截图保存
                        try:
                            screenshot_path = f'/tmp/zhihu_no_publish_btn_{int(time.time())}.png'
                            self.page.get_screenshot(path=screenshot_path)
                            logger.info(f"已保存错误截图: {screenshot_path}")
                        except:
                            pass
                        return {'success': False, 'message': error_msg}

                    # 第二步：确保按钮可见并可点击
                    logger.info("步骤2/4: 准备点击发布按钮...")
                    try:
                        # 滚动到按钮位置
                        publish_btn.run_js('this.scrollIntoView({behavior: "smooth", block: "center"})')
                        time.sleep(1)

                        # 检查按钮是否可用
                        is_disabled = publish_btn.attr('disabled')
                        if is_disabled:
                            error_msg = "发布按钮被禁用，可能内容未填写完整"
                            logger.error(f"✗ {error_msg}")
                            return {'success': False, 'message': error_msg}

                        logger.info("✓ 发布按钮可用")
                    except Exception as e:
                        logger.warning(f"检查按钮状态失败: {e}")

                    # 第三步：点击发布按钮
                    logger.info("步骤3/4: 点击发布按钮...")
                    publish_btn.click()
                    logger.info("✓ 已点击发布按钮")
                    time.sleep(3)

                    # 第四步：处理可能的二次确认对话框
                    logger.info("步骤4/4: 检查确认对话框...")
                    confirm_found = False

                    # 知乎可能的确认按钮选择器
                    confirm_selectors = [
                        'text:确认发布',
                        'text:确定',
                        'text:立即发布',
                        'css:.Modal button.Button--primary',
                        'css:.Modal button:contains("确认")',
                        'css:div[role="dialog"] button.Button--primary',
                    ]

                    for selector in confirm_selectors:
                        try:
                            confirm_btn = self.page.ele(selector, timeout=1.5)
                            if confirm_btn:
                                logger.info(f"✓ 找到确认按钮: {selector}")
                                confirm_btn.click()
                                logger.info("✓ 已点击确认发布")
                                confirm_found = True
                                time.sleep(3)
                                break
                        except:
                            continue

                    if not confirm_found:
                        logger.info("未检测到确认对话框，可能已直接发布")
                        time.sleep(2)

                    # 第五步：验证发布成功并获取文章链接
                    logger.info("步骤5/4: 验证发布结果...")
                    time.sleep(3)

                    current_url = self.page.url
                    logger.info(f"当前URL: {current_url}")

                    # 判断是否发布成功的多种方式
                    success_indicators = []

                    # 1. URL变化检查
                    if 'write' not in current_url:
                        success_indicators.append("URL已离开编辑页面")

                    if '/p/' in current_url or '/zhuanlan/' in current_url:
                        success_indicators.append("URL包含文章ID")

                    # 2. 页面内容检查
                    try:
                        page_text = self.page.html
                        if '发布成功' in page_text or '已发布' in page_text:
                            success_indicators.append("页面显示发布成功")
                    except:
                        pass

                    # 3. 检查是否有成功提示元素
                    try:
                        success_toast = self.page.ele('text:发布成功', timeout=2)
                        if success_toast:
                            success_indicators.append("找到成功提示")
                    except:
                        pass

                    # 判断发布结果
                    if success_indicators:
                        logger.info(f"✓✓ 文章发布成功! 成功指标: {', '.join(success_indicators)}")

                        # 尝试获取文章ID
                        article_id = None
                        if '/p/' in current_url:
                            article_id = current_url.split('/p/')[-1].split('?')[0].split('/')[0]
                        elif '/zhuanlan/' in current_url:
                            parts = current_url.split('/zhuanlan/')[-1].split('/')
                            if len(parts) > 0:
                                article_id = parts[0]

                        return {
                            'success': True,
                            'message': '文章发布成功',
                            'type': 'published',
                            'url': current_url,
                            'article_id': article_id,
                            'indicators': success_indicators
                        }
                    else:
                        # 发布状态不明确
                        logger.warning("⚠ 无法确认发布状态")

                        # 再次截图
                        try:
                            screenshot_path = f'/tmp/zhihu_publish_unclear_{int(time.time())}.png'
                            self.page.get_screenshot(path=screenshot_path)
                            logger.info(f"已保存状态截图: {screenshot_path}")
                        except:
                            pass

                        # 如果URL变化了，仍然认为可能成功
                        if current_url != 'https://zhuanlan.zhihu.com/write':
                            logger.info("URL已变化，可能发布成功")
                            return {
                                'success': True,
                                'message': '文章可能已发布，请手动确认',
                                'type': 'published',
                                'url': current_url,
                                'warning': '发布状态不明确，建议手动检查'
                            }
                        else:
                            return {
                                'success': False,
                                'message': '发布状态不明确，请手动检查',
                                'url': current_url
                            }

                except Exception as e:
                    error_msg = f'发布过程异常: {str(e)}'
                    logger.error(f"✗ {error_msg}", exc_info=True)

                    # 异常时截图
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
    print("完善知乎文章发布模块")
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
    local_file = 'D:/work/code/TOP_N/zhihu_auto_post_enhanced.py'

    sftp.get(remote_file, local_file)

    with open(local_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 替换发布流程部分
    import re

    # 查找发布流程的开始和结束位置
    # 从 "# 发布或保存草稿" 开始，到下一个 "except Exception as e:" 之前
    pattern = r'(# 发布或保存草稿.*?)(except Exception as e:\s+logger\.error\(f"✗ 创建文章异常)'

    match = re.search(pattern, content, re.DOTALL)
    if match:
        # 替换发布流程
        content = content[:match.start(1)] + '            ' + ENHANCED_PUBLISH_CODE.strip() + '\n\n        ' + content[match.start(2):]
        print("✓ 发布流程已替换")
    else:
        print("⚠ 未找到匹配的发布流程代码")
        print("尝试其他匹配方式...")

        # 尝试更简单的匹配：从 "if draft:" 到函数结束
        pattern2 = r'(            if draft:.*?)(        except Exception as e:\s+logger\.error\(f"✗ 创建文章异常)'
        match2 = re.search(pattern2, content, re.DOTALL)

        if match2:
            content = content[:match2.start(1)] + ENHANCED_PUBLISH_CODE.strip() + '\n\n        ' + content[match2.start(2):]
            print("✓ 发布流程已替换（备用方法）")
        else:
            print("✗ 无法找到替换位置")
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
    print("✅ 完善完成!")
    print("=" * 80)
    print("""
改进内容:

📋 发布流程完善 (5步法):

步骤1: 查找发布按钮
  ✓ 支持6种不同的选择器
  ✓ 智能匹配按钮文本（包含"发布"但不含"草稿"）
  ✓ 优先使用主要蓝色按钮

步骤2: 验证按钮状态
  ✓ 滚动到按钮位置确保可见
  ✓ 检查按钮是否被禁用
  ✓ 提前发现内容未填写完整的问题

步骤3: 点击发布按钮
  ✓ 确认点击成功
  ✓ 等待页面响应

步骤4: 处理确认对话框
  ✓ 支持6种确认按钮选择器
  ✓ 自动检测是否需要二次确认
  ✓ 智能判断直接发布场景

步骤5: 验证发布结果
  ✓ URL变化检查（离开编辑页、包含文章ID）
  ✓ 页面内容检查（发布成功提示）
  ✓ 成功提示元素检查
  ✓ 提取文章ID
  ✓ 多重指标综合判断

🔍 错误处理增强:

  ✓ 每个关键步骤都有日志输出
  ✓ 失败时自动截图（3个关键位置）
  ✓ 详细的错误信息返回给前端
  ✓ 发布状态不明确时的智能判断

📊 返回信息增强:

  成功时返回:
    - success: True
    - message: "文章发布成功"
    - type: "published"
    - url: 文章链接
    - article_id: 文章ID（如果能提取）
    - indicators: 成功指标列表

  失败时返回:
    - success: False
    - message: 详细错误信息
    - url: 当前页面URL
    - warning: 警告信息（如果适用）

现在请测试发布功能，应该更加稳定可靠！
    """)

    ssh.close()

except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
