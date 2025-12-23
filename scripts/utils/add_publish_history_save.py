#!/usr/bin/env python3
"""
在publish_worker.py中添加保存PublishHistory的功能
"""
import sys

# 读取文件
with open('backend/services/publish_worker.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到导入部分，添加PublishHistory
for i, line in enumerate(lines):
    if 'from models import PublishTask, PlatformAccount' in line:
        lines[i] = 'from models import PublishTask, PlatformAccount, PublishHistory, get_db_session\n'
        print(f'✓ 修改第{i+1}行：添加PublishHistory导入')
        break

# 找到发布成功后的位置，添加保存历史的代码
found = False
for i, line in enumerate(lines):
    if '# 发布成功' in line and 'success = update_task_status' in lines[i+1]:
        # 在update_task_status之后添加保存历史的代码
        insert_pos = i + 9  # 跳过update_task_status调用

        history_code = '''
            # 保存到发布历史
            try:
                db = get_db_session()
                history_record = PublishHistory(
                    user_id=task_info['user_id'],
                    article_id=task_info.get('article_id'),
                    platform=task_info['platform'],
                    status='success',
                    url=result.get('url'),
                    message='发布成功'
                )
                db.add(history_record)
                db.commit()
                task_log.log("✓ 发布历史已保存")
                db.close()
            except Exception as he:
                task_log.log(f"⚠️ 保存发布历史失败: {he}", 'WARN')
                try:
                    db.rollback()
                    db.close()
                except:
                    pass

'''
        lines.insert(insert_pos, history_code)
        print(f'✓ 在第{insert_pos+1}行插入保存PublishHistory的代码')
        found = True
        break

if not found:
    print('✗ 未找到插入位置')
    sys.exit(1)

# 写回文件
with open('backend/services/publish_worker.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('\n✓ 修改完成！')
