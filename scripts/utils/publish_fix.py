#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 读取原文件
with open('publish.js.bak', 'r', encoding='utf-8') as f:
    content = f.read()

# 添加轮询函数（在文件开头）
poll_function = '''
// 轮询任务状态直到完成
async function pollTaskStatus(taskId, maxWaitTime = 300000, pollInterval = 3000) {
    const startTime = Date.now();

    while (Date.now() - startTime < maxWaitTime) {
        try {
            const response = await fetch(`/api/tasks/${taskId}`, {
                method: 'GET',
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const result = await response.json();

            if (!result.success) {
                throw new Error(result.error || '查询任务失败');
            }

            const task = result.task;

            // 任务完成（成功或失败）
            if (task.status === 'success' || task.status === 'failed') {
                return task;
            }

            // 任务被取消
            if (task.status === 'cancelled') {
                throw new Error('任务已被取消');
            }

            // 等待后继续轮询
            await new Promise(resolve => setTimeout(resolve, pollInterval));

        } catch (error) {
            console.error('轮询任务状态出错:', error);
            throw error;
        }
    }

    throw new Error('任务执行超时');
}

'''

content = poll_function + content

# 找到并替换publishToZhihu中的成功处理逻辑
# 使用行数定位 (大约在283-289行之间)
lines = content.split('\n')
for i in range(len(lines)):
    if 'if (data.success)' in lines[i] and i < len(lines) - 5:
        # 检查下一行是否包含"发布成功"
        if i+1 < len(lines) and '发布成功' in lines[i+1]:
            # 找到了，替换这段代码 (从if到对应的})
            indent = '        '  # 保持缩进
            new_logic = [
                f'{indent}if (data.success && data.task_id) {{',
                f'{indent}    // 新的任务队列系统 - 需要轮询任务状态',
                f'{indent}    showLoading(\'任务已创建，正在发布中...\');',
                f'{indent}    ',
                f'{indent}    try {{',
                f'{indent}        const finalResult = await pollTaskStatus(data.task_id);',
                f'{indent}        hideLoading();',
                f'{indent}        ',
                f'{indent}        if (finalResult.status === \'success\') {{',
                f'{indent}            const url = finalResult.result_url || \'\';',
                f'{indent}            alert(`发布成功！\\n${{url ? \'文章链接: \' + url : \'\'}}`);',
                f'{indent}            publishHistoryManager.refresh();',
                f'{indent}        }} else if (finalResult.status === \'failed\') {{',
                f'{indent}            alert(`发布失败：${{finalResult.error_message || \'未知错误\'}}`);',
                f'{indent}        }} else {{',
                f'{indent}            alert(`发布状态异常：${{finalResult.status}}`);',
                f'{indent}        }}',
                f'{indent}    }} catch (error) {{',
                f'{indent}        hideLoading();',
                f'{indent}        alert(\'轮询任务状态失败: \' + error.message);',
                f'{indent}    }}',
                f'{indent}}} else if (data.success) {{',
                f'{indent}    // 旧系统的直接成功响应（向后兼容）',
                f'{indent}    alert(`发布成功！\\n${{data.message || \'\'}}`);',
                f'{indent}    publishHistoryManager.refresh();',
                f'{indent}}} else {{',
                f'{indent}    alert(`发布失败：${{data.message || data.error || \'未知错误\'}}`);',
                f'{indent}}}',
            ]

            # 替换原来的6行代码 (if...} else {...})
            lines[i:i+6] = new_logic
            print(f'OK - Replaced at line {i+1}')
            break

# 保存
with open('publish.js.fixed', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print('OK - publish.js.fixed generated')
