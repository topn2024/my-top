#!/bin/bash
# 部署知乎自动登录功能脚本

echo "=========================================="
echo "知乎自动登录功能部署脚本"
echo "=========================================="
echo ""

# 检查必需文件是否存在
echo "检查必需文件..."

if [ ! -f "/d/work/code/TOP_N/backend/zhihu_auto_post_enhanced.py" ]; then
    echo "❌ 错误: zhihu_auto_post_enhanced.py 不存在"
    exit 1
fi
echo "✓ zhihu_auto_post_enhanced.py 存在"

if [ ! -f "/d/work/code/TOP_N/backend/login_tester.py" ]; then
    echo "❌ 错误: login_tester.py 不存在"
    exit 1
fi
echo "✓ login_tester.py 存在"

if [ ! -f "/d/work/code/TOP_N/backend/app_with_upload.py" ]; then
    echo "❌ 错误: app_with_upload.py 不存在"
    exit 1
fi
echo "✓ app_with_upload.py 存在"

echo ""
echo "检查app_with_upload.py是否已集成增强版模块..."
if grep -q "from zhihu_auto_post_enhanced import" /d/work/code/TOP_N/backend/app_with_upload.py; then
    echo "✓ 已集成 zhihu_auto_post_enhanced"
else
    echo "❌ 未集成 zhihu_auto_post_enhanced，请检查配置"
    exit 1
fi

if grep -q "password=password," /d/work/code/TOP_N/backend/app_with_upload.py; then
    echo "✓ 已添加 password 参数"
else
    echo "❌ 未添加 password 参数，请检查配置"
    exit 1
fi

echo ""
echo "=========================================="
echo "部署检查完成！"
echo "=========================================="
echo ""
echo "功能说明："
echo "1. ✓ Cookie登录：优先使用已保存的Cookie登录"
echo "2. ✓ 自动登录：Cookie失效时自动使用测试账号密码登录"
echo "3. ✓ Cookie保存：登录成功后自动保存Cookie供下次使用"
echo ""
echo "使用流程："
echo "1. 在账号管理中配置知乎账号和密码"
echo "2. 首次发布时会自动使用密码登录并保存Cookie"
echo "3. 后续发布直接使用Cookie（除非Cookie失效）"
echo ""
echo "部署完成！可以重启服务进行测试。"
