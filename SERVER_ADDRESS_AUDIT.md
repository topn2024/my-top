# 服务器地址审计报告

## 审计时间
2025-12-14

## 审计结果
✅ 系统中所有服务器地址配置正确

## 正确的服务器地址
**39.105.12.124**

## 审计详情

### 已修复的错误地址
- ❌ 47.76.148.25 (错误地址，已全部清除)
- ✅ 所有引用已更新为 39.105.12.124

### 已检查的文件
1. **DEPLOYMENT_INSTRUCTIONS.md** - ✅ 已更新所有7处引用
2. **backend/DEPLOYMENT_GUIDE.md** - ✅ 使用正确地址
3. **backend/deploy_auto_login_ssh.sh** - ✅ 使用正确地址
4. **backend/deploy_auto_login_to_server.sh** - ✅ 使用正确地址
5. **backend/deploy_to_server.sh** - ✅ 使用正确地址
6. **backend/部署完成确认单.md** - ✅ 使用正确地址
7. **backend/简易部署说明.txt** - ✅ 使用正确地址

### 网络配置检查
以下配置均正确：
- `0.0.0.0:8080` - Gunicorn监听所有接口（正确）
- `0.0.0.0:3001` - 备用端口配置（正确）
- User-Agent字符串中的版本号（如 Chrome/143.0.0.0）- 这些是浏览器版本，非IP地址

## 服务器连接测试
```bash
# 测试SSH连接
ssh u_topn@39.105.12.124  # ✅ 连接成功

# 测试Gunicorn状态
ps aux | grep gunicorn  # ✅ 4个worker正常运行

# 测试API
curl http://localhost:8080/api/analyze  # ✅ 正常响应
```

## 搜索命令记录
```bash
# 检查错误地址
grep -r "47\.76\.148\.25" D:\code\TOP_N  # ✅ 无匹配

# 检查所有IP地址
grep -rE "\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}" D:\code\TOP_N\backend  # ✅ 仅正确地址
```

## 结论
系统中不存在错误的服务器地址引用，所有配置文件和脚本都使用正确的服务器地址 **39.105.12.124**。
