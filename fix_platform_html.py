#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 platform.html - 添加用户信息显示组件
"""

# 读取原始文件
with open('platform.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 在header部分添加用户信息显示元素
# 找到 <div class="header"> ... <p>智能生成推广内容，一键发布到多个平台</p>
# 在这之后添加用户信息显示
header_addition = '''            <div style="position: absolute; top: 20px; right: 20px;">
                <div id="user-info-display"></div>
            </div>'''

# 替换header部分
content = content.replace(
    '            <p>智能生成推广内容，一键发布到多个平台</p>\n        </div>',
    f'            <p>智能生成推广内容，一键发布到多个平台</p>\n{header_addition}\n        </div>'
)

# 2. 添加user_display.js脚本
# 找到 </body> 前面添加脚本
script_tag = '    <script src="/static/user_display.js"></script>\n'

content = content.replace('</body>', f'{script_tag}</body>')

# 3. 添加CSS样式来定位user-info-display
css_addition = '''
        .header {
            position: relative;
        }

        #user-info-display {
            min-width: 120px;
        }

        /* 用户信息样式 */
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
        }

        .user-info-btn:hover {
            background: rgba(255, 255, 255, 0.3);
            border-color: rgba(255, 255, 255, 0.5);
        }

        .user-info-btn.guest {
            opacity: 0.8;
        }

        .user-icon {
            font-size: 1.2rem;
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
'''

# 在 </style> 前添加CSS
content = content.replace('    </style>', f'{css_addition}    </style>')

# 保存修改后的文件
with open('platform_fixed.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('✓ platform_fixed.html 生成成功')
print('修改内容:')
print('1. 在header右上角添加了 <div id="user-info-display"></div>')
print('2. 在</body>前添加了 <script src="/static/user_display.js"></script>')
print('3. 添加了用户信息显示的CSS样式')
