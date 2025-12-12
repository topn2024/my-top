#!/bin/bash
# SSH 免密配置验证脚本

echo "=========================================="
echo "SSH 免密配置验证"
echo "=========================================="

# 颜色定义（使用 ASCII）
OK="[OK]"
FAIL="[FAIL]"
INFO="[INFO]"

# 测试计数
TOTAL=0
PASSED=0

# 测试函数
test_item() {
    TOTAL=$((TOTAL + 1))
    echo -ne "\n[$TOTAL] $1 ... "
}

pass() {
    PASSED=$((PASSED + 1))
    echo "$OK"
}

fail() {
    echo "$FAIL - $1"
}

# 1. 检查 SSH 密钥是否存在
test_item "Check SSH private key exists"
if [ -f ~/.ssh/id_rsa ]; then
    pass
else
    fail "Private key not found at ~/.ssh/id_rsa"
fi

# 2. 检查 SSH 公钥是否存在
test_item "Check SSH public key exists"
if [ -f ~/.ssh/id_rsa.pub ]; then
    pass
else
    fail "Public key not found at ~/.ssh/id_rsa.pub"
fi

# 3. 检查密钥权限
test_item "Check private key permissions"
PERM=$(stat -c "%a" ~/.ssh/id_rsa 2>/dev/null || stat -f "%A" ~/.ssh/id_rsa 2>/dev/null)
if [ "$PERM" = "600" ] || [ "$PERM" = "400" ]; then
    pass
else
    fail "Incorrect permissions: $PERM (should be 600 or 400)"
fi

# 4. 检查 SSH 配置文件
test_item "Check SSH config file"
if [ -f ~/.ssh/config ]; then
    pass
else
    fail "Config file not found at ~/.ssh/config"
fi

# 5. 测试免密 SSH 连接
test_item "Test passwordless SSH connection"
if ssh -o BatchMode=yes -o ConnectTimeout=5 topn 'exit' 2>/dev/null; then
    pass
else
    fail "Cannot connect to server"
fi

# 6. 测试远程命令执行
test_item "Test remote command execution"
RESULT=$(ssh topn 'whoami' 2>/dev/null)
if [ "$RESULT" = "u_topn" ]; then
    pass
else
    fail "Command execution failed or returned unexpected result: $RESULT"
fi

# 7. 测试 SCP 上传
test_item "Test SCP upload"
echo "test" > /tmp/ssh_test_upload.txt
if scp -o BatchMode=yes /tmp/ssh_test_upload.txt topn:/tmp/ 2>/dev/null; then
    pass
    rm -f /tmp/ssh_test_upload.txt
else
    fail "File upload failed"
fi

# 8. 测试 SCP 下载
test_item "Test SCP download"
if scp -o BatchMode=yes topn:/tmp/ssh_test_upload.txt /tmp/ssh_test_download.txt 2>/dev/null; then
    pass
    rm -f /tmp/ssh_test_download.txt
else
    fail "File download failed"
fi

# 9. 清理测试文件
test_item "Cleanup test files"
if ssh topn 'rm -f /tmp/ssh_test_upload.txt' 2>/dev/null; then
    pass
else
    fail "Cleanup failed"
fi

# 10. 检查服务器项目目录
test_item "Check server project directory"
if ssh topn 'test -d /home/u_topn/TOP_N' 2>/dev/null; then
    pass
else
    fail "Project directory not found on server"
fi

# 显示结果
echo ""
echo "=========================================="
echo "Test Results: $PASSED/$TOTAL passed"
echo "=========================================="

if [ $PASSED -eq $TOTAL ]; then
    echo ""
    echo "$OK SSH passwordless authentication is fully configured!"
    echo ""
    echo "You can now use:"
    echo "  - ssh topn"
    echo "  - scp file.txt topn:/path/"
    echo "  - Python paramiko with key authentication"
    echo ""
    exit 0
else
    echo ""
    echo "$FAIL Some tests failed. Please check the errors above."
    echo ""
    exit 1
fi
