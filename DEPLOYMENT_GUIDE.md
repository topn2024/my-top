# TOP_N 部署指南

## 部署日期
2025-12-09

## 服务器信息
- **服务器地址**: 39.105.12.124
- **用户名**: u_topn
- **部署目录**: /home/u_topn/TOP_N
- **服务端口**: 3001

## 快速部署

### 方法一: 使用自动部署脚本 (推荐)

```bash
# 在本地 Windows 环境执行
python scripts/deploy/sync_and_deploy.py
```

脚本会自动执行以下步骤:
1. 连接到服务器
2. 备份现有代码
3. 停止当前服务
4. 上传新代码
5. 安装依赖
6. 启动服务
7. 测试基本功能

### 方法二: 手动部署

#### 1. 备份服务器代码

```bash
ssh u_topn@39.105.12.124
cd /home/u_topn
tar -czf TOP_N_backup_$(date +%Y%m%d_%H%M%S).tar.gz TOP_N/
```

#### 2. 停止当前服务

```bash
# 停止 gunicorn
pkill -f gunicorn

# 或停止 systemd 服务
sudo systemctl stop topn
```

#### 3. 上传代码

```bash
# 在本地执行
scp -r backend templates static scripts requirements.txt start.sh u_topn@39.105.12.124:/home/u_topn/TOP_N/
```

#### 4. 安装依赖

```bash
ssh u_topn@39.105.12.124
cd /home/u_topn/TOP_N
python3 -m pip install -r requirements.txt --user
```

#### 5. 启动服务

```bash
cd /home/u_topn/TOP_N
gunicorn -c backend/gunicorn_config.py 'backend.app_factory:app'
```

## 部署检查清单

### 部署前检查

- [ ] 本地代码已测试
- [ ] 数据库备份已完成
- [ ] 服务器备份已完成
- [ ] requirements.txt 已更新
- [ ] 配置文件已更新 (config.py, models.py)

### 部署后检查

- [ ] 服务进程正在运行
- [ ] 端口 3001 正在监听
- [ ] 健康检查端点正常: http://39.105.12.124:3001/api/health
- [ ] 首页可以访问: http://39.105.12.124:3001
- [ ] 数据库连接正常
- [ ] 日志文件正常输出

## 常见问题

### 1. 服务无法启动

**检查步骤:**
```bash
# 查看错误日志
tail -50 /home/u_topn/TOP_N/logs/gunicorn_error.log

# 检查端口占用
netstat -tlnp | grep 3001

# 手动启动查看详细错误
cd /home/u_topn/TOP_N
gunicorn -w 1 -b 0.0.0.0:3001 'backend.app_factory:app'
```

### 2. 数据库连接失败

**检查步骤:**
```bash
# 检查 MySQL 服务
sudo systemctl status mysql

# 测试数据库连接
cd /home/u_topn/TOP_N/backend
python3 -c "from models import engine; engine.connect(); print('OK')"
```

### 3. 依赖包缺失

**解决方法:**
```bash
cd /home/u_topn/TOP_N
python3 -m pip install -r requirements.txt --user --upgrade
```

### 4. 权限问题

**解决方法:**
```bash
# 设置正确的权限
chmod +x /home/u_topn/TOP_N/start.sh
chmod -R 755 /home/u_topn/TOP_N/backend
chmod -R 755 /home/u_topn/TOP_N/scripts
```

## 服务管理命令

### 启动服务

```bash
# 使用 gunicorn 配置文件启动
cd /home/u_topn/TOP_N
gunicorn -c backend/gunicorn_config.py 'backend.app_factory:app'

# 后台运行
nohup gunicorn -c backend/gunicorn_config.py 'backend.app_factory:app' > logs/gunicorn.log 2>&1 &
```

### 停止服务

```bash
# 优雅停止
pkill -TERM -f gunicorn

# 强制停止
pkill -KILL -f gunicorn
```

### 重启服务

```bash
# 停止
pkill -f gunicorn

# 等待进程退出
sleep 2

# 启动
cd /home/u_topn/TOP_N
nohup gunicorn -c backend/gunicorn_config.py 'backend.app_factory:app' > logs/gunicorn.log 2>&1 &
```

### 查看服务状态

```bash
# 查看进程
ps aux | grep gunicorn

# 查看端口监听
netstat -tlnp | grep 3001

# 查看日志
tail -f /home/u_topn/TOP_N/logs/gunicorn_error.log
tail -f /home/u_topn/TOP_N/logs/gunicorn_access.log
```

## 性能优化建议

### Gunicorn 配置优化

根据服务器配置调整 `backend/gunicorn_config.py`:

```python
# CPU 核心数
workers = multiprocessing.cpu_count() * 2 + 1

# 超时时间
timeout = 120

# 每个 worker 的线程数
threads = 2
```

### 数据库连接池优化

在 `backend/models.py` 中调整连接池参数:

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=10,        # 连接池大小
    max_overflow=20,     # 最大溢出连接数
    pool_recycle=3600,   # 连接回收时间
    pool_pre_ping=True   # 连接前检查
)
```

## 监控和日志

### 日志位置

- **访问日志**: `/home/u_topn/TOP_N/logs/gunicorn_access.log`
- **错误日志**: `/home/u_topn/TOP_N/logs/gunicorn_error.log`
- **应用日志**: `/home/u_topn/TOP_N/logs/app.log`

### 实时监控

```bash
# 监控错误日志
tail -f /home/u_topn/TOP_N/logs/gunicorn_error.log

# 监控访问日志
tail -f /home/u_topn/TOP_N/logs/gunicorn_access.log

# 监控系统资源
htop

# 监控网络连接
watch -n 1 'netstat -an | grep 3001'
```

## 安全建议

1. **定期更新依赖包**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

2. **设置防火墙规则**
   ```bash
   sudo ufw allow 3001/tcp
   ```

3. **使用 HTTPS** (推荐使用 Nginx 反向代理)

4. **定期备份数据库**
   ```bash
   mysqldump -u admin -p topn_platform > backup_$(date +%Y%m%d).sql
   ```

5. **限制文件上传大小** (已在 config.py 中设置)

## 版本信息

### 当前版本
- **应用版本**: 2.0 (重构版)
- **Python版本**: 3.9+
- **Flask版本**: 2.0+
- **数据库**: MySQL 8.0

### 更新日志

**2025-12-09**
- 完成代码重构,采用蓝图和服务层架构
- 添加发布历史记录功能
- 优化数据库模型和查询
- 完善 API 端点
- 改进错误处理和日志记录

## 联系方式

如有问题,请查看:
- 项目文档: `/home/u_topn/TOP_N/docs/`
- GitHub Issues: (如果有的话)
- 开发者: (联系方式)

## 附录: 目录结构

```
TOP_N/
├── backend/              # 后端代码
│   ├── app_factory.py   # 应用工厂
│   ├── config.py        # 配置文件
│   ├── models.py        # 数据模型
│   ├── gunicorn_config.py  # Gunicorn配置
│   ├── services/        # 服务层
│   └── blueprints/      # 路由蓝图
├── templates/           # HTML模板
├── static/              # 静态资源
├── logs/                # 日志文件
├── data/                # 数据文件
├── uploads/             # 上传文件
└── requirements.txt     # Python依赖
```
