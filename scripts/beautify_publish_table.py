#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美化发布历史表格样式
"""

import re

# 读取原文件
with open('/home/u_topn/TOP_N/static/publish.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 新的美化版 displayPublishHistory 函数
new_function = r'''// 显示发布历史（美化表格版）
function displayPublishHistory(history) {
    const container = document.getElementById('history-container');

    if (!history || history.length === 0) {
        container.innerHTML = `
            <div style="margin-top: 30px; text-align: center; padding: 60px 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; color: white;">
                <div style="font-size: 48px; margin-bottom: 15px;">📝</div>
                <h3 style="margin: 0 0 10px 0; font-size: 20px;">暂无发布历史</h3>
                <p style="margin: 0; opacity: 0.9; font-size: 14px;">选择文章并点击"开始发布"，这里将显示您的发布记录</p>
            </div>
        `;
        return;
    }

    const recentHistory = history.slice(0, 10);

    // 统计数据
    const successCount = recentHistory.filter(item => item.status === 'success').length;
    const failedCount = recentHistory.filter(item => item.status === 'failed').length;
    const successRate = recentHistory.length > 0 ? Math.round((successCount / recentHistory.length) * 100) : 0;

    let tableHTML = `
        <div style="margin-top: 40px;">
            <!-- 统计卡片 -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 25px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; color: white; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);">
                    <div style="font-size: 13px; opacity: 0.9; margin-bottom: 8px;">总发布数</div>
                    <div style="font-size: 32px; font-weight: bold;">${recentHistory.length}</div>
                </div>
                <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); padding: 20px; border-radius: 12px; color: white; box-shadow: 0 4px 15px rgba(56, 239, 125, 0.4);">
                    <div style="font-size: 13px; opacity: 0.9; margin-bottom: 8px;">✓ 成功</div>
                    <div style="font-size: 32px; font-weight: bold;">${successCount}</div>
                </div>
                <div style="background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); padding: 20px; border-radius: 12px; color: white; box-shadow: 0 4px 15px rgba(235, 51, 73, 0.4);">
                    <div style="font-size: 13px; opacity: 0.9; margin-bottom: 8px;">✗ 失败</div>
                    <div style="font-size: 32px; font-weight: bold;">${failedCount}</div>
                </div>
                <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px; border-radius: 12px; color: white; box-shadow: 0 4px 15px rgba(240, 147, 251, 0.4);">
                    <div style="font-size: 13px; opacity: 0.9; margin-bottom: 8px;">成功率</div>
                    <div style="font-size: 32px; font-weight: bold;">${successRate}%</div>
                </div>
            </div>

            <!-- 表格标题 -->
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h3 style="margin: 0; color: #333; font-size: 20px; font-weight: 600;">
                    <span style="margin-right: 8px;">📊</span>最近发布记录
                </h3>
                <button onclick="loadPublishHistory()" style="padding: 8px 16px; background: #667eea; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; transition: all 0.3s; box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(102, 126, 234, 0.4)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 8px rgba(102, 126, 234, 0.3)'">
                    🔄 刷新
                </button>
            </div>

            <!-- 美化表格 -->
            <div style="background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border: 1px solid #f0f0f0;">
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background: linear-gradient(to right, #667eea, #764ba2);">
                            <th style="padding: 16px; text-align: left; color: white; font-weight: 600; font-size: 14px;">文章标题</th>
                            <th style="padding: 16px; text-align: center; color: white; font-weight: 600; font-size: 14px; width: 100px;">平台</th>
                            <th style="padding: 16px; text-align: center; color: white; font-weight: 600; font-size: 14px; width: 120px;">状态</th>
                            <th style="padding: 16px; text-align: center; color: white; font-weight: 600; font-size: 14px; width: 180px;">发布时间</th>
                        </tr>
                    </thead>
                    <tbody>
    `;

    recentHistory.forEach((item, index) => {
        const statusText = item.status === 'success' ? '✓ 成功' : '✗ 失败';
        const statusStyle = item.status === 'success'
            ? 'background: linear-gradient(135deg, #d4edda, #c3e6cb); color: #155724; box-shadow: 0 2px 8px rgba(21, 87, 36, 0.15);'
            : 'background: linear-gradient(135deg, #f8d7da, #f5c6cb); color: #721c24; box-shadow: 0 2px 8px rgba(114, 28, 36, 0.15);';
        const timeStr = item.timestamp ? new Date(item.timestamp).toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        }) : '-';
        const title = item.article_title || '(未命名)';
        const rowBg = index % 2 === 0 ? '#fafbfc' : '#ffffff';

        tableHTML += `
            <tr style="border-bottom: 1px solid #f0f0f0; background: ${rowBg}; transition: all 0.3s;" onmouseover="this.style.background='#f5f7ff'; this.style.transform='scale(1.01)'" onmouseout="this.style.background='${rowBg}'; this.style.transform='scale(1)'">
                <td style="padding: 16px;">
                    <div style="font-weight: 500; color: #2c3e50; font-size: 14px; margin-bottom: 4px;">${title}</div>
                    ${item.message ? `<div style="font-size: 12px; color: #95a5a6; margin-top: 6px; padding: 6px 10px; background: #f8f9fa; border-radius: 4px; border-left: 3px solid #e74c3c;">${item.message}</div>` : ''}
                    ${item.url ? `<a href="${item.url}" target="_blank" style="display: inline-flex; align-items: center; gap: 4px; font-size: 12px; color: #667eea; text-decoration: none; margin-top: 8px; padding: 4px 8px; border-radius: 4px; transition: all 0.3s;" onmouseover="this.style.background='#f0f3ff'" onmouseout="this.style.background='transparent'">
                        <span>🔗</span>查看文章
                    </a>` : ''}
                </td>
                <td style="padding: 16px; text-align: center;">
                    <span style="display: inline-block; padding: 6px 12px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border-radius: 6px; font-size: 12px; font-weight: 500; box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);">
                        ${item.platform}
                    </span>
                </td>
                <td style="padding: 16px; text-align: center;">
                    <span style="display: inline-block; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; ${statusStyle}">
                        ${statusText}
                    </span>
                </td>
                <td style="padding: 16px; text-align: center; color: #7f8c8d; font-size: 13px; font-family: 'Courier New', monospace;">
                    ${timeStr}
                </td>
            </tr>
        `;
    });

    tableHTML += `
                    </tbody>
                </table>
            </div>

            <!-- 底部提示 -->
            <div style="margin-top: 15px; text-align: center; color: #95a5a6; font-size: 13px;">
                <span style="margin-right: 15px;">📝 显示最近 ${recentHistory.length} 条记录</span>
                ${recentHistory.length >= 10 ? '<span>• 查看更多请访问 <a href="/publish_history" style="color: #667eea; text-decoration: none;">完整历史</a></span>' : ''}
            </div>
        </div>
    `;

    container.innerHTML = tableHTML;
}'''

# 找到并替换 displayPublishHistory 函数
pattern = r'// 显示发布历史.*?^}'
content = re.sub(pattern, new_function, content, flags=re.DOTALL | re.MULTILINE)

# 写回文件
with open('/home/u_topn/TOP_N/static/publish.js', 'w', encoding='utf-8') as f:
    f.write(content)

print('✓ publish.js 已更新为美化版表格')
