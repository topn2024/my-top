#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量给多个页面添加用户信息显示
"""

import os
import sys

# 需要添加用户显示的文件列表
files_to_update = ['articles.html', 'publish.html']

# CSS样式（统一样式）
user_info_css = '''    <style>
        /* 用户信息显示样式 */
        #user-info-display {
            min-width: 120px;
        }

        .user-info-container {
            position: relative;
            display: inline-block;
        }

        .user-info-btn {
            background: rgba(255, 255, 255, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.3);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.3s;
            font-size: 14px;
        }

        .user-info-btn:hover {
            background: rgba(255, 255, 255, 0.3);
            border-color: rgba(255, 255, 255, 0.5);
        }

        .user-icon {
            font-size: 1.1rem;
        }

        .user-name {
            font-weight: 600;
        }

        .dropdown-arrow {
            font-size: 0.7rem;
            margin-left: 4px;
        }

        .user-menu {
            position: absolute;
            top: 100%;
            right: 0;
            margin-top: 8px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            min-width: 200px;
            z-index: 1000;
        }

        .user-menu-item {
            padding: 12px 16px;
            display: flex;
            align-items: center;
            gap: 10px;
            color: #333;
            text-decoration: none;
            cursor: pointer;
            border: none;
            background: none;
            width: 100%;
            text-align: left;
            font-size: 0.95rem;
        }

        .user-menu-item:hover {
            background: #f8f9fa;
        }

        .user-menu-item.user-menu-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 4px;
            cursor: default;
        }

        .user-menu-item.user-menu-header:hover {
            background: none;
        }

        .user-menu-divider {
            height: 1px;
            background: #e9ecef;
            margin: 4px 0;
        }
    </style>
'''

def add_user_display(filename):
    """给指定文件添加用户显示"""
    print(f'Processing {filename}...')

    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # 备份
    with open(f'{filename}.bak_user', 'w', encoding='utf-8') as f:
        f.write(content)

    # 1. 在header中添加用户信息显示
    # 查找header标签并添加用户信息div
    if '<header>' in content:
        content = content.replace('<header>', '<header style="position: relative;">', 1)

        # 在header结束前添加用户信息
        content = content.replace(
            '</header>',
            '''            <div style="position: absolute; top: 20px; right: 20px;">
                <div id="user-info-display"></div>
            </div>
        </header>''',
            1
        )

    # 2. 添加CSS样式
    if user_info_css not in content:
        content = content.replace('</head>', f'{user_info_css}</head>', 1)

    # 3. 添加JavaScript
    script_tag = '    <script src="/static/user_display.js"></script>\n'
    if script_tag not in content:
        content = content.replace('</body>', f'{script_tag}</body>', 1)

    # 保存
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f'✓ {filename} updated')

# 主程序
for file in files_to_update:
    if os.path.exists(file):
        add_user_display(file)
    else:
        print(f'✗ {file} not found')

print('\nAll files processed!')
