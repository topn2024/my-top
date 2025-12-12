# TOP_N 脚本目录说明

本目录包含TOP_N项目的所有运维脚本，按功能分类组织。

## 目录结构

```
scripts/
├── deploy/              # 部署相关脚本
├── check/               # 检查和监控脚本
├── test/                # 测试脚本
├── install/             # 安装和配置脚本
├── fix/                 # 修复脚本
└── README.md           # 本文件
```

## 部署脚本 (deploy/)

### deploy_final_correct.py
**最新的标准部署脚本** - 用于部署知乎自动登录功能

- 功能：全自动部署知乎自动登录功能到生产服务器
- 服务器：u_topn@39.105.12.124
- 路径：/home/u_topn/TOP_N/backend
- 部署文件：
  - zhihu_auto_post_enhanced.py
  - app_with_upload.py
- 服务管理：使用Gunicorn (端口8080)
- 使用方法：
  ```bash
  cd D:\work\code\TOP_N
  python scripts/deploy/deploy_final_correct.py
  ```

### 其他部署脚本
- `auto_deploy.py` - 通用自动部署脚本
- `deploy_cookie_feature.py` - Cookie功能部署
- `deploy_login_tester.py` - 登录测试器部署
- 等...

## 检查脚本 (check/)

### verify_deployment.py
**部署验证脚本** - 验证部署是否成功

- 功能：全面检查部署状态
- 检查项目：
  - Gunicorn进程状态
  - 端口监听状态
  - 文件完整性
  - 代码集成验证
  - HTTP服务响应
- 使用方法：
  ```bash
  python scripts/check/verify_deployment.py
  ```

### check_gunicorn_setup.py
检查Gunicorn配置和启动方式

### check_start_script.py
检查启动脚本和端口占用情况

### 其他检查脚本
- `check_server_logs.py` - 查看服务器日志
- `check_topn_logs.py` - 查看TOP_N日志
- `monitor_server_logs.py` - 实时监控日志
- 等...

## 测试脚本 (test/)

- `test_api.py` - API测试
- `local_test_login.py` - 本地登录测试
- `test_enhanced_login.py` - 增强版登录测试
- 等...

## 安装脚本 (install/)

- `install_python314.py` - 安装Python 3.14
- `install_selenium_server.py` - 安装Selenium
- `install_chromedriver_*.py` - 安装ChromeDriver
- 等...

## 修复脚本 (fix/)

- `fix_deployment.py` - 修复部署问题
- `fix_api_routes.py` - 修复API路由
- `fix_login_tester_import.py` - 修复登录测试器导入
- 等...

## 最佳实践

1. **脚本位置规范**
   - 所有TOP_N相关脚本必须放在 `D:\work\code\TOP_N` 目录下
   - 按功能分类到对应的子目录
   - 临时脚本使用后应移至 `archive/temp/`

2. **运行脚本**
   - 始终从TOP_N根目录运行：`cd D:\work\code\TOP_N`
   - 使用相对路径：`python scripts/deploy/deploy_final_correct.py`

3. **创建新脚本**
   - 部署脚本 → `scripts/deploy/`
   - 检查脚本 → `scripts/check/`
   - 测试脚本 → `scripts/test/`
   - 安装脚本 → `scripts/install/`
   - 修复脚本 → `scripts/fix/`

4. **脚本命名**
   - 使用描述性名称：`deploy_zhihu_auto_login.py`
   - 避免版本号：`v1`, `v2`, `final` 等
   - 旧版本脚本移至 `archive/temp/`

## 常用命令

```bash
# 部署到服务器
cd D:\work\code\TOP_N
python scripts/deploy/deploy_final_correct.py

# 验证部署
python scripts/check/verify_deployment.py

# 查看服务器日志
python scripts/check/check_topn_logs.py

# 测试API
python scripts/test/test_api.py
```

## 服务器信息

### 生产服务器
- 地址：39.105.12.124
- 用户：u_topn
- 密码：TopN@2024
- 路径：/home/u_topn/TOP_N/backend
- 端口：8080 (Gunicorn)
- 访问：http://39.105.12.124:8080

### 管理员用户
- 用户：lihanya
- 密码：@WSX2wsx
- 权限：sudo访问

## 注意事项

1. 部署前务必备份
2. 使用 `deploy_final_correct.py` 进行标准部署
3. 部署后使用 `verify_deployment.py` 验证
4. 遇到问题查看对应的check和fix脚本
5. 所有脚本必须使用UTF-8编码
6. Windows环境需设置正确的stdout编码

## 更新记录

- 2025-12-08: 创建脚本目录结构，整理部署脚本
- 2025-12-08: 添加知乎自动登录功能部署脚本
