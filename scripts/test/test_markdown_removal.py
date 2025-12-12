#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 remove_markdown_and_ai_traces 函数
"""

import sys
import os

# 添加backend目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from app_with_upload import remove_markdown_and_ai_traces

def test_remove_markdown_and_ai_traces():
    """测试函数"""

    # 测试用例：包含各种Markdown格式和AI痕迹的文本
    test_text = """
### 这是一个标题

**这是粗体文本**，*这是斜体文本*

综上所述，这个产品非常优秀。值得一提的是，它的性能非常好。

- 列表项1
- 列表项2
- 列表项3

1. 有序列表1
2. 有序列表2

> 这是一个引用

与此同时，我们需要注意性能优化。因此，建议采用以下方案。

[点击这里](https://example.com)查看更多信息。

`这是行内代码`

```python
def hello():
    print("Hello World")
```

然而，这个方案也有一些缺点。总的来说，这是一个不错的选择。

---

需要注意的是，以及其他一些问题。
"""

    print("=" * 80)
    print("原始文本:")
    print("=" * 80)
    print(test_text)
    print()

    # 处理文本
    cleaned_text = remove_markdown_and_ai_traces(test_text)

    print("=" * 80)
    print("处理后的文本:")
    print("=" * 80)
    print(cleaned_text)
    print()

    # 检查结果
    checks = {
        "是否去除了 ### 标题": "###" not in cleaned_text,
        "是否去除了 ** 粗体": "**" not in cleaned_text,
        "是否去除了 * 斜体": "*这是斜体文本*" not in cleaned_text,
        "是否去除了列表标记 -": "- 列表项" not in cleaned_text,
        "是否去除了有序列表 1.": "1. 有序列表" not in cleaned_text,
        "是否去除了引用标记 >": "> 这是一个引用" not in cleaned_text,
        "是否去除了链接格式": "[点击这里]" not in cleaned_text,
        "是否去除了代码块": "```" not in cleaned_text,
        "是否去除了行内代码": "`这是行内代码`" not in cleaned_text,
        "是否去除了分割线": "---" not in cleaned_text,
        "是否去除了'综上所述'": "综上所述" not in cleaned_text,
        "是否去除了'值得一提的是'": "值得一提的是" not in cleaned_text,
        "是否去除了'总的来说'": "总的来说" not in cleaned_text,
        "是否去除了'需要注意的是'": "需要注意的是" not in cleaned_text,
        "是否替换了'与此同时'为'同时'": "与此同时" not in cleaned_text and "同时" in cleaned_text,
        "是否替换了'然而'为'但是'": "然而" not in cleaned_text and "但是" in cleaned_text,
        "是否替换了'因此'为'所以'": "因此" not in cleaned_text and "所以" in cleaned_text,
        "是否替换了'以及'为'和'": "和其他一些问题" in cleaned_text,
    }

    print("=" * 80)
    print("检查结果:")
    print("=" * 80)

    all_passed = True
    for check_name, result in checks.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} - {check_name}")
        if not result:
            all_passed = False

    print()
    if all_passed:
        print("所有测试通过!")
    else:
        print("部分测试失败，请检查!")

    return all_passed

if __name__ == '__main__':
    try:
        success = test_remove_markdown_and_ai_traces()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
