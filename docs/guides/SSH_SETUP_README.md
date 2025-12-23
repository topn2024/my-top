# SSH 免密登录配置完成

## 配置摘要

✅ **SSH 密钥已生成并配置**
- 本地密钥路径: `~/.ssh/id_rsa` (私钥)
- 公钥路径: `~/.ssh/id_rsa.pub`
- 服务器已添加公钥到 `~/.ssh/authorized_keys`

✅ **服务器连接信息**
- 主机: `39.105.12.124`
- 用户: `u_topn`
- 端口: `22`
- 项目目录: `/home/u_topn/TOP_N`

✅ **SSH 配置文件已创建**
- 路径: `~/.ssh/config`
- 支持别名连接: `ssh topn` 或 `ssh topn-server`

---

## 使用方法

### 1. 命令行直接连接

```bash
# 使用完整地址
ssh u_topn@39.105.12.124

# 使用配置的别名（推荐）
ssh topn

# 执行远程命令
ssh topn 'ls -la /home/u_topn/TOP_N'

# 查看服务器状态
ssh topn 'df -h && free -h'
```

### 2. 文件传输（SCP）

```bash
# 上传单个文件
scp local_file.txt topn:/home/u_topn/TOP_N/

# 下载单个文件
scp topn:/home/u_topn/TOP_N/remote_file.txt ./

# 上传整个目录
scp -r ./local_directory topn:/home/u_topn/TOP_N/

# 下载整个目录
scp -r topn:/home/u_topn/TOP_N/remote_directory ./
```

### 3. 使用 Shell 脚本

参考示例脚本: `scripts/ssh_examples.sh`

```bash
# 执行示例脚本
bash scripts/ssh_examples.sh

# 脚本中的关键用法
SERVER="topn"
ssh $SERVER 'command'
scp file.txt $SERVER:/path/to/destination/
```

### 4. 使用 Python (paramiko)

参考示例脚本: `scripts/ssh_python_example.py`

```bash
# 运行 Python 示例
python scripts/ssh_python_example.py
```

**Python 代码示例:**

```python
import paramiko
from pathlib import Path

# 连接配置
hostname = '39.105.12.124'
username = 'u_topn'
key_path = str(Path.home() / '.ssh' / 'id_rsa')

# 创建 SSH 客户端
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# 加载私钥并连接
private_key = paramiko.RSAKey.from_private_key_file(key_path)
client.connect(hostname=hostname, username=username, pkey=private_key)

# 执行命令
stdin, stdout, stderr = client.exec_command('whoami')
print(stdout.read().decode())

# 文件传输
sftp = client.open_sftp()
sftp.put('local_file.txt', '/home/u_topn/TOP_N/remote_file.txt')
sftp.get('/home/u_topn/TOP_N/remote_file.txt', 'downloaded_file.txt')
sftp.close()

# 关闭连接
client.close()
```

---

## 常用部署场景

### 场景 1: 部署代码到服务器

```bash
#!/bin/bash
# 上传 backend 代码
scp -r backend/ topn:/home/u_topn/TOP_N/

# 重启服务
ssh topn 'cd /home/u_topn/TOP_N && pkill -f gunicorn && gunicorn -c backend/gunicorn_config.py backend.app_factory:app &'
```

### 场景 2: 备份服务器数据

```bash
#!/bin/bash
# 下载数据库和日志
scp -r topn:/home/u_topn/TOP_N/data ./backup/
scp -r topn:/home/u_topn/TOP_N/logs ./backup/

# 或使用 tar 压缩后下载
ssh topn 'cd /home/u_topn && tar -czf TOP_N_backup.tar.gz TOP_N/'
scp topn:/home/u_topn/TOP_N_backup.tar.gz ./backup/
```

### 场景 3: 查看服务器日志

```bash
#!/bin/bash
# 实时查看错误日志
ssh topn 'tail -f /home/u_topn/TOP_N/logs/gunicorn_error.log'

# 查看最近 100 行日志
ssh topn 'tail -100 /home/u_topn/TOP_N/logs/gunicorn_error.log'

# 搜索特定关键词
ssh topn 'grep "ERROR" /home/u_topn/TOP_N/logs/*.log'
```

### 场景 4: 执行复杂的远程操作

```bash
#!/bin/bash
ssh topn << 'ENDSSH'
cd /home/u_topn/TOP_N

# 停止服务
pkill -f gunicorn

# 备份数据库
cp data/topn.db data/topn_backup_$(date +%Y%m%d).db

# 更新依赖
pip3 install -r requirements.txt --user

# 启动服务
gunicorn -c backend/gunicorn_config.py backend.app_factory:app > /dev/null 2>&1 &

# 验证服务
sleep 3
curl -s http://localhost:3001/api/health || echo "Service failed to start"
ENDSSH
```

---

## SSH 配置详情

`~/.ssh/config` 文件内容:

```
Host topn-server
    HostName 39.105.12.124
    User u_topn
    Port 22
    IdentityFile ~/.ssh/id_rsa
    ServerAliveInterval 60
    ServerAliveCountMax 3
    StrictHostKeyChecking no
    UserKnownHostsFile ~/.ssh/known_hosts
    BatchMode yes

Host topn
    HostName 39.105.12.124
    User u_topn
    Port 22
    IdentityFile ~/.ssh/id_rsa
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

**配置说明:**
- `ServerAliveInterval 60`: 每 60 秒发送心跳包保持连接
- `ServerAliveCountMax 3`: 最多 3 次心跳失败后断开
- `StrictHostKeyChecking no`: 不严格检查主机密钥（自动接受新主机）
- `BatchMode yes`: 批处理模式，不提示输入密码

---

## 验证配置

```bash
# 测试 SSH 连接
ssh topn 'echo "SSH connection successful!"'

# 测试 SCP 上传
echo "test" > /tmp/test.txt
scp /tmp/test.txt topn:/tmp/
ssh topn 'cat /tmp/test.txt'

# 测试 SCP 下载
ssh topn 'echo "download test" > /tmp/download_test.txt'
scp topn:/tmp/download_test.txt /tmp/
cat /tmp/download_test.txt

# 清理测试文件
rm /tmp/test.txt /tmp/download_test.txt
ssh topn 'rm /tmp/test.txt /tmp/download_test.txt'
```

---

## 安全建议

1. **私钥保护**: 确保私钥权限为 600
   ```bash
   chmod 600 ~/.ssh/id_rsa
   ```

2. **定期更换密钥**: 建议每 6-12 个月更换一次 SSH 密钥

3. **禁用密码登录**: 在服务器上禁用密码认证（仅使用密钥）
   ```bash
   # 编辑 /etc/ssh/sshd_config
   PasswordAuthentication no
   ```

4. **使用 SSH Agent**: 避免重复输入密钥密码
   ```bash
   eval $(ssh-agent)
   ssh-add ~/.ssh/id_rsa
   ```

---

## 故障排查

### 问题 1: 连接被拒绝

```bash
# 检查服务器 SSH 服务状态
ssh topn 'systemctl status sshd'

# 检查防火墙
ssh topn 'sudo firewall-cmd --list-all'
```

### 问题 2: 权限被拒绝

```bash
# 检查本地密钥权限
ls -la ~/.ssh/id_rsa

# 检查服务器 authorized_keys 权限
ssh topn 'ls -la ~/.ssh/authorized_keys'

# 正确权限应该是:
# 私钥: 600 (-rw-------)
# authorized_keys: 600 或 644
```

### 问题 3: 连接超时

```bash
# 检查网络连通性
ping 39.105.12.124

# 使用 verbose 模式查看详细信息
ssh -vvv topn
```

---

## 快速命令参考

| 操作 | 命令 |
|------|------|
| 连接服务器 | `ssh topn` |
| 执行远程命令 | `ssh topn 'command'` |
| 上传文件 | `scp file.txt topn:/path/` |
| 下载文件 | `scp topn:/path/file.txt ./` |
| 上传目录 | `scp -r dir/ topn:/path/` |
| 下载目录 | `scp -r topn:/path/dir/ ./` |
| 查看日志 | `ssh topn 'tail -f /path/to/log'` |
| 重启服务 | `ssh topn 'systemctl restart service'` |

---

## 示例脚本位置

- Bash 示例: `scripts/ssh_examples.sh`
- Python 示例: `scripts/ssh_python_example.py`

---

**配置完成时间**: 2025-12-12
**配置状态**: ✅ 免密 SSH 已启用并测试成功
