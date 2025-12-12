# 知乎自动登录功能 - 手动部署指南

## 📋 部署概要

将以下文件部署到服务器 `39.105.12.124:/root/TOP_N/backend`

## 📦 需要部署的文件

1. **zhihu_auto_post_enhanced.py** (新增)
2. **app_with_upload.py** (已修改)

## 🚀 部署步骤

### 方式1：使用已有的部署脚本

如果项目中有 `scripts/deploy/` 目录下的部署脚本，可以参考使用。

### 方式2：手动部署（推荐）

#### 步骤1: 连接服务器

```bash
ssh lihanya@39.105.12.124
# 输入密码: @WSX2wsx
```

#### 步骤2: 备份当前文件

```bash
cd /root/TOP_N/backend
cp app_with_upload.py app_with_upload.py.backup_$(date +%Y%m%d_%H%M%S)
```

#### 步骤3: 上传新文件

在本地 Windows 机器上，打开另一个终端：

**上传 zhihu_auto_post_enhanced.py:**
```bash
cd D:\work\code\TOP_N\backend
# 使用 WinSCP、FTP 或其他工具上传文件到服务器
# 目标路径: /root/TOP_N/backend/zhihu_auto_post_enhanced.py
```

**上传 app_with_upload.py:**
```bash
# 目标路径: /root/TOP_N/backend/app_with_upload.py
```

#### 步骤4: 验证文件

回到SSH连接，验证文件：

```bash
cd /root/TOP_N/backend

# 检查文件是否存在
ls -lh zhihu_auto_post_enhanced.py app_with_upload.py

# 验证代码集成
grep "from zhihu_auto_post_enhanced import" app_with_upload.py
grep "password=password," app_with_upload.py
```

预期输出应包含：
- `from zhihu_auto_post_enhanced import post_article_to_zhihu`
- `password=password,`

#### 步骤5: 重启服务

```bash
# 查找Flask进程
ps aux | grep app_with_upload

# 停止旧进程（替换 <PID> 为实际进程ID）
kill <PID>

# 等待2秒
sleep 2

# 启动新服务
cd /root/TOP_N/backend
nohup python3 app_with_upload.py > logs/app.log 2>&1 &

# 记录新进程ID
echo $!
```

#### 步骤6: 验证服务

```bash
# 检查进程是否运行
ps aux | grep app_with_upload

# 检查端口
netstat -tuln | grep 3001

# 查看日志
tail -20 logs/app.log
```

预期输出：
- 进程正在运行
- 端口3001正在监听
- 日志无错误信息

## ✅ 验证清单

部署完成后，确认以下项：

- [ ] zhihu_auto_post_enhanced.py 文件已上传
- [ ] app_with_upload.py 文件已更新
- [ ] 代码集成验证通过
- [ ] 旧服务已停止
- [ ] 新服务已启动
- [ ] 进程正常运行
- [ ] 端口3001监听
- [ ] 日志无错误

## 📝 文件内容对照

### zhihu_auto_post_enhanced.py

应包含以下关键方法：
- `class ZhihuAutoPost`
- `def auto_login_with_password(self, username, password)`
- `def post_article_to_zhihu(username, title, content, password=None, ...)`

### app_with_upload.py 修改点

**第1262行：**
```python
from zhihu_auto_post_enhanced import post_article_to_zhihu
```

**第1277-1285行：**
```python
result = post_article_to_zhihu(
    username=username,
    title=title,
    content=content,
    topics=None,
    password=password,  # ← 新增
    draft=False
)
```

## 🔍 故障排查

### 问题1：服务启动失败

查看日志：
```bash
tail -50 /root/TOP_N/backend/logs/app.log
```

常见原因：
- 端口被占用
- Python依赖缺失
- 代码语法错误

### 问题2：模块导入失败

错误信息：`ImportError: cannot import name 'post_article_to_zhihu'`

解决方法：
```bash
# 确认文件存在
ls -l /root/TOP_N/backend/zhihu_auto_post_enhanced.py

# 检查文件语法
python3 -m py_compile zhihu_auto_post_enhanced.py
```

### 问题3：服务无响应

```bash
# 检查进程
ps aux | grep app_with_upload

# 检查端口
netstat -tuln | grep 3001

# 重启服务
pkill -f app_with_upload
cd /root/TOP_N/backend
nohup python3 app_with_upload.py > logs/app.log 2>&1 &
```

## 📊 部署后测试

1. 访问 http://39.105.12.124:3001
2. 登录系统
3. 进入"账号管理"
4. 添加知乎测试账号
5. 创建测试文章
6. 点击"发布到知乎"
7. 观察日志输出：
   ```bash
   tail -f /root/TOP_N/backend/logs/app.log
   ```

预期行为：
- 首次发布：自动密码登录 → 保存Cookie → 发布成功
- 后续发布：Cookie登录 → 发布成功

## 📞 支持

如遇问题，查看：
- 实现说明：`docs/知乎自动登录功能实现说明.md`
- 实现总结：`backend/IMPLEMENTATION_SUMMARY.md`
- 验证清单：`backend/VERIFICATION_CHECKLIST.md`

---

**部署文档版本：** 1.0
**更新日期：** 2025-12-08
