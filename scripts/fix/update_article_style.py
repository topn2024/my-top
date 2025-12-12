#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修改文章生成风格 - 采用人类互联网发帖风格,不使用Markdown
"""
import paramiko
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"

print("=" * 80)
print("修改文章生成风格 - 采用互联网发帖风格")
print("=" * 80)

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, timeout=30)
    print("✓ SSH连接成功\n")

    # 备份
    print("[1/4] 备份文件...")
    cmd = "cp /home/u_topn/TOP_N/backend/app_with_upload.py /home/u_topn/TOP_N/backend/app_with_upload.py.backup_$(date +%Y%m%d_%H%M%S)"
    ssh.exec_command(cmd, timeout=10)
    time.sleep(1)
    print("✓ 备份完成\n")

    # 下载
    print("[2/4] 下载并修改文件...")
    sftp = ssh.open_sftp()
    remote_file = '/home/u_topn/TOP_N/backend/app_with_upload.py'
    local_file = 'D:/work/code/TOP_N/app_with_upload_new_style.py'

    sftp.get(remote_file, local_file)

    with open(local_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 替换旧的prompt
    old_prompt = '''prompt = f\'\'\'
基于以下分析信息，撰写一篇关于 {company_name} 的{article_types[i]}：

{analysis}

要求：
1. 文章长度800-1200字
2. 突出公司/产品的核心优势
3. 语言专业且易懂
4. 包含具体案例或数据支撑
5. 标题要吸引人
6. 适合发布到知乎、CSDN等平台

请按以下格式返回：
标题：[文章标题]

正文：
[文章内容]
\'\'\''''

    new_prompt = '''prompt = f\'\'\'
你是一个资深的互联网内容创作者。基于以下分析信息，以人类在知乎、论坛发帖的自然风格，撰写一篇关于 {company_name} 的{article_types[i]}。

{analysis}

【创作要求】：

📝 内容要求：
- 文章长度800-1200字
- 突出公司/产品的核心亮点
- 用通俗易懂的大白话，像跟朋友聊天一样
- 可以用实际案例、数据来说明观点
- 标题要吸引眼球，让人想点进来看

✍️ 写作风格（重要！）：
- 使用自然的段落分隔，不要用Markdown标记（如 # ## ### * - 等）
- 可以用空行分段，让文章有呼吸感
- 重点内容用「」或【】标注，不要用加粗**
- 数字、专有名词直接写，不要加引号或特殊格式
- 适当使用emoji表情符号，让内容更生动
- 语气自然，像在知乎、微博发帖那样，不要太正式
- 可以用口语化表达，比如"说实话"、"这个真的"、"不得不说"等

❌ 绝对不要使用：
- Markdown标题格式：# ## ### 等
- Markdown列表：- * + 等
- Markdown加粗：** **
- Markdown代码块：``` ```
- Markdown引用：>
- 过于生硬的格式化排版

✅ 推荐使用：
- 自然的段落（用空行分隔）
- 【标题】或「重点」这样的标注
- emoji表情符号 ✨ 🎯 💡 🔥 等
- 数字序号：1、2、3、或者 一、二、三、
- 像说话一样的表达方式

【输出格式】：
标题：[一个吸引人的标题]

正文：
[用自然段落写作，就像在知乎发帖一样，不要用任何Markdown语法]

示例风格参考：

标题：月栖科技：当AI不再是冰冷的工具，而是能懂你的数字同事

说实话，当我第一次接触月栖科技的AI智能体时，感觉完全颠覆了我对人工智能的认知。

不同于市面上那些需要你反复调教、写一大堆提示词的AI工具，月栖科技做的是【类人协作】。什么意思呢？就是这个AI真的能像人一样理解你的需求，跟你配合工作。

我给大家举个例子 ✨

传统的AI助手，你得告诉它："帮我写一份市场分析报告，要包括竞品分析、用户画像、市场趋势..."，列一大串。但月栖科技的智能体不一样，你只需要说"帮我分析一下这个市场"，它就能自己去找数据、做分析、生成报告，中间有不清楚的还会主动问你。

这种感觉就像有个真人同事在帮你，而不是一个冷冰冰的工具。

【核心亮点】

1、真正的智能化协作
不是简单的问答，而是能主动理解任务、规划步骤、执行并反馈。就像给团队新招了一个特别靠谱的同事。

2、降低使用门槛
普通人也能用！不需要学什么提示词工程，就像跟人说话一样自然。

3、实际落地能力强
不是PPT上的概念，而是真正能解决问题的产品。

...

[后续内容继续以这种自然段落的方式展开，不使用任何Markdown语法]
\'\'\'
'''

    if old_prompt in content:
        content = content.replace(old_prompt, new_prompt)
        print("✓ 已更新文章生成prompt（互联网发帖风格）\n")
    else:
        print("✗ 未找到目标prompt\n")
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
    cmd = "python3 -m py_compile /home/u_topn/TOP_N/backend/app_with_upload.py"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    err = stderr.read().decode('utf-8')

    if err:
        print(f"✗ 语法错误:\n{err}")
        ssh.exec_command("ls -t /home/u_topn/TOP_N/backend/app_with_upload.py.backup_* | head -1 | xargs -I {} cp {} /home/u_topn/TOP_N/backend/app_with_upload.py", timeout=10)
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
    print("✅ 文章生成风格已更新!")
    print("=" * 80)
    print("""
新的文章风格特点:

📝 采用人类互联网发帖风格：
  ✅ 自然的段落分隔（空行）
  ✅ 使用「」【】标注重点
  ✅ 口语化表达，像聊天
  ✅ 适当使用emoji表情 ✨ 🎯 💡
  ✅ 数字序号：1、2、3、

❌ 不再使用Markdown格式：
  ✗ 不用 # ## ### 标题
  ✗ 不用 ** ** 加粗
  ✗ 不用 - * + 列表
  ✗ 不用 ``` 代码块
  ✗ 不用 > 引用

📖 风格示例：

说实话，当我第一次接触这个产品时...

【核心亮点】

1、真正的智能化
这个功能真的很厉害...

2、降低使用门槛
普通人也能用！...

不得不说，这个方向是对的 ✨

优势：
✅ 更符合知乎、微博等平台的发帖习惯
✅ 阅读体验更自然、更亲切
✅ 不会因为Markdown格式被平台转义或识别异常
✅ 更像真人写的，不像AI生成的

现在重新生成文章，风格会更自然！
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
