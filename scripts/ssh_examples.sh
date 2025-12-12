#!/bin/bash
# SSH 免密操作示例脚本
# 此脚本展示如何使用配置好的 SSH 免密登录进行各种操作

SERVER="topn"  # 使用 SSH 配置的别名
SERVER_FULL="u_topn@39.105.12.124"  # 完整地址（备用）
REMOTE_DIR="/home/u_topn/TOP_N"

echo "=========================================="
echo "SSH 免密操作示例"
echo "=========================================="

# 示例 1: 执行远程命令
echo -e "\n[示例 1] 执行远程命令 - 查看服务器时间"
ssh $SERVER 'date'

# 示例 2: 查看远程目录
echo -e "\n[示例 2] 查看服务器项目目录"
ssh $SERVER "ls -lh $REMOTE_DIR | head -10"

# 示例 3: 上传单个文件
echo -e "\n[示例 3] 上传文件到服务器"
# scp local_file.txt $SERVER:$REMOTE_DIR/

# 示例 4: 下载单个文件
echo -e "\n[示例 4] 从服务器下载文件"
# scp $SERVER:$REMOTE_DIR/remote_file.txt ./

# 示例 5: 上传整个目录
echo -e "\n[示例 5] 上传目录到服务器"
# scp -r ./backend $SERVER:$REMOTE_DIR/

# 示例 6: 下载整个目录
echo -e "\n[示例 6] 从服务器下载目录"
# scp -r $SERVER:$REMOTE_DIR/logs ./

# 示例 7: 执行多个命令
echo -e "\n[示例 7] 执行多个远程命令"
ssh $SERVER << 'ENDSSH'
cd /home/u_topn/TOP_N
echo "Current directory: $(pwd)"
echo "Git status:"
git status --short 2>/dev/null || echo "Not a git repository"
ENDSSH

# 示例 8: 使用管道传输数据
echo -e "\n[示例 8] 使用管道传输数据"
# echo "test data" | ssh $SERVER "cat > $REMOTE_DIR/test.txt"

# 示例 9: 远程执行 Python 脚本
echo -e "\n[示例 9] 远程执行 Python 脚本"
# ssh $SERVER "cd $REMOTE_DIR && python3 script.py"

# 示例 10: 检查服务器状态
echo -e "\n[示例 10] 检查服务器应用状态"
ssh $SERVER << 'ENDSSH'
echo "检查 gunicorn 进程:"
ps aux | grep gunicorn | grep -v grep || echo "gunicorn 未运行"

echo -e "\n检查端口 3001:"
netstat -tlnp 2>/dev/null | grep :3001 || echo "端口 3001 未监听"

echo -e "\n检查 Redis:"
redis-cli ping 2>/dev/null || echo "Redis 未运行"
ENDSSH

echo -e "\n=========================================="
echo "所有示例执行完成"
echo "=========================================="
