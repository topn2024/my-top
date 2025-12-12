#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 input.html - 添加AI模型加载功能
"""

# 读取原始文件内容(从之前已经保存的内容)
content = """// 加载AI模型列表
async function loadAIModels() {
    const select = document.getElementById('ai-model-select');

    // 定义可用的AI模型列表
    const models = [
        { value: 'qwen-plus', name: '通义千问 Plus (推荐)', isDefault: true },
        { value: 'qwen-max', name: '通义千问 Max' },
        { value: 'qwen-turbo', name: '通义千问 Turbo (快速)' }
    ];

    // 清空加载中选项
    select.innerHTML = '';

    // 添加模型选项
    models.forEach(model => {
        const option = document.createElement('option');
        option.value = model.value;
        option.textContent = model.name;
        if (model.isDefault) {
            option.selected = true;
        }
        select.appendChild(option);
    });
}"""

print(content)
print("\n\n=== 调用方式 ===")
print("在 DOMContentLoaded 中调用: loadAIModels();")
