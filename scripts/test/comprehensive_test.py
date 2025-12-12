#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面测试月栖网站和推广平台的所有功能
"""

import paramiko
import sys
import io
import json

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 服务器配置
SERVER = "39.105.12.124"
USER = "u_topn"
PASSWORD = "TopN@2024"
BASE_URL = "http://localhost:3001"

def execute(ssh, cmd):
    """执行SSH命令"""
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    return output, error

def test_page(ssh, endpoint, name):
    """测试单个页面"""
    cmd = f"curl -s -o /dev/null -w '%{{http_code}}' {BASE_URL}{endpoint}"
    out, _ = execute(ssh, cmd)
    status_code = out.strip()

    if status_code == "200":
        result = "✓"
        status = "正常"
    elif status_code == "302":
        result = "↗"
        status = "重定向"
    elif status_code == "401":
        result = "🔒"
        status = "需要认证"
    elif status_code == "404":
        result = "✗"
        status = "未找到"
    elif status_code == "500":
        result = "✗"
        status = "服务器错误"
    else:
        result = "?"
        status = f"状态码:{status_code}"

    print(f"  {result} {name:30s} {endpoint:30s} [{status}]")
    return status_code, status

def test_api(ssh, method, endpoint, name, data=None):
    """测试API端点"""
    if method == "GET":
        cmd = f"curl -s -o /dev/null -w '%{{http_code}}' {BASE_URL}{endpoint}"
    else:
        data_json = json.dumps(data) if data else '{}'
        cmd = f"curl -s -o /dev/null -w '%{{http_code}}' -X {method} -H 'Content-Type: application/json' -d '{data_json}' {BASE_URL}{endpoint}"

    out, _ = execute(ssh, cmd)
    status_code = out.strip()

    if status_code in ["200", "201"]:
        result = "✓"
        status = "正常"
    elif status_code == "400":
        result = "⚠"
        status = "请求错误"
    elif status_code == "401":
        result = "🔒"
        status = "需要认证"
    else:
        result = "✗"
        status = f"状态码:{status_code}"

    print(f"  {result} {name:30s} {method} {endpoint:25s} [{status}]")
    return status_code, status

def main():
    """主函数"""
    print("=" * 80)
    print("  月栖网站和推广平台 - 全面功能测试")
    print("=" * 80)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)
        print("\n✓ 已连接到服务器\n")

        # ========================================
        # 1. 页面可访问性测试
        # ========================================
        print("\n【1】页面可访问性测试")
        print("-" * 80)

        pages = [
            ("/", "首页"),
            ("/login", "登录页"),
            ("/platform", "平台页"),
            ("/analysis", "分析页"),
            ("/articles", "文章页"),
            ("/publish", "发布页"),
        ]

        page_results = {}
        for endpoint, name in pages:
            code, status = test_page(ssh, endpoint, name)
            page_results[endpoint] = (code, status)

        # ========================================
        # 2. API端点测试
        # ========================================
        print("\n【2】API端点测试")
        print("-" * 80)

        api_results = {}

        # 健康检查
        code, status = test_api(ssh, "GET", "/api/health", "健康检查")
        api_results["/api/health"] = (code, status)

        # 用户认证相关
        code, status = test_api(ssh, "POST", "/api/auth/register", "用户注册",
                               {"username": "test", "email": "test@test.com", "password": "test123"})
        api_results["/api/auth/register"] = (code, status)

        code, status = test_api(ssh, "POST", "/api/auth/login", "用户登录",
                               {"username": "test", "password": "test123"})
        api_results["/api/auth/login"] = (code, status)

        code, status = test_api(ssh, "GET", "/api/auth/me", "获取当前用户")
        api_results["/api/auth/me"] = (code, status)

        # 工作流相关
        code, status = test_api(ssh, "POST", "/api/analyze", "公司分析")
        api_results["/api/analyze"] = (code, status)

        code, status = test_api(ssh, "POST", "/api/generate_articles", "生成文章")
        api_results["/api/generate_articles"] = (code, status)

        code, status = test_api(ssh, "GET", "/api/workflow/current", "获取当前工作流")
        api_results["/api/workflow/current"] = (code, status)

        code, status = test_api(ssh, "GET", "/api/workflow/list", "获取工作流列表")
        api_results["/api/workflow/list"] = (code, status)

        # 账号管理
        code, status = test_api(ssh, "GET", "/api/accounts", "获取账号列表")
        api_results["/api/accounts"] = (code, status)

        # 发布相关
        code, status = test_api(ssh, "POST", "/api/publish_zhihu", "发布到知乎")
        api_results["/api/publish_zhihu"] = (code, status)

        code, status = test_api(ssh, "GET", "/api/publish_history", "获取发布历史")
        api_results["/api/publish_history"] = (code, status)

        # ========================================
        # 3. 错误日志检查
        # ========================================
        print("\n【3】检查错误日志")
        print("-" * 80)

        out, _ = execute(ssh, "tail -30 /home/u_topn/TOP_N/logs/error.log")
        error_lines = [line for line in out.split('\n') if 'ERROR' in line or 'Exception' in line or 'Traceback' in line]

        if error_lines:
            print("  发现错误日志:")
            for line in error_lines[-10:]:  # 只显示最后10条
                print(f"    {line[:100]}")
        else:
            print("  ✓ 无错误日志")

        # ========================================
        # 4. 测试结果汇总
        # ========================================
        print("\n" + "=" * 80)
        print("  测试结果汇总")
        print("=" * 80)

        # 页面测试统计
        page_ok = sum(1 for code, _ in page_results.values() if code == "200")
        page_total = len(page_results)
        print(f"\n页面可访问性: {page_ok}/{page_total} 通过")

        # 列出有问题的页面
        problem_pages = [(ep, status) for ep, (code, status) in page_results.items() if code not in ["200", "302"]]
        if problem_pages:
            print("\n需要修复的页面:")
            for endpoint, status in problem_pages:
                print(f"  ✗ {endpoint}: {status}")

        # API测试统计
        api_ok = sum(1 for code, _ in api_results.values() if code in ["200", "201"])
        api_total = len(api_results)
        print(f"\nAPI端点功能: {api_ok}/{api_total} 正常")

        # 列出有问题的API
        problem_apis = [(ep, status) for ep, (code, status) in api_results.items() if code not in ["200", "201", "401"]]
        if problem_apis:
            print("\n需要修复的API:")
            for endpoint, status in problem_apis:
                print(f"  ✗ {endpoint}: {status}")

        # 总体评分
        total_ok = page_ok + api_ok
        total_tests = page_total + api_total
        score = int((total_ok / total_tests) * 100)

        print(f"\n总体评分: {score}/100")
        print(f"通过率: {total_ok}/{total_tests}")

        # ========================================
        # 5. 获取详细错误信息
        # ========================================
        if problem_pages or problem_apis:
            print("\n" + "=" * 80)
            print("  详细错误信息")
            print("=" * 80)

            # 对于500错误的页面，获取详细信息
            for endpoint, (code, status) in page_results.items():
                if code == "500":
                    print(f"\n{endpoint} 的错误详情:")
                    cmd = f"curl -v {BASE_URL}{endpoint} 2>&1 | head -50"
                    out, _ = execute(ssh, cmd)
                    print(out[:500])

        return problem_pages, problem_apis

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None
    finally:
        ssh.close()

if __name__ == '__main__':
    problem_pages, problem_apis = main()

    # 返回退出码
    if problem_pages is None:
        sys.exit(2)  # 测试脚本错误
    elif problem_pages or problem_apis:
        sys.exit(1)  # 有问题需要修复
    else:
        sys.exit(0)  # 全部正常
