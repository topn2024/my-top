# 知乎QR登录测试后的下一步操作指南

## 当前状态 (2025-12-06)

### ✅ 已完成并部署
1. **二维码优化** - 只显示二维码图片,不显示整个网页
2. **增强状态检测** - 三层检测机制(URL/页面文本/Cookie)
3. **状态缓存** - 减少重复检测,提高效率

### ⏳ 已准备但未部署
1. **自动发帖模块** (`zhihu_auto_post.py`)
2. **部署脚本** (`deploy_auto_post.py`)
3. **完整文档** (`ZHIHU_AUTO_POST_README.md`)

---

## 测试QR登录的步骤

### 1. 访问账号配置页面
```
http://39.105.12.124:8080
```

### 2. 添加知乎账号并测试
- 点击"添加账号"
- 选择"知乎"平台
- 点击"测试"按钮
- 弹出二维码窗口(现在只显示二维码部分,不显示整个页面)

### 3. 用知乎App扫码
- 打开知乎App
- 扫描二维码
- 在手机上确认登录

### 4. 观察状态变化
服务器会每2秒检测一次登录状态:
- `waiting` - 等待扫码
- `scanned` - 已扫描,等待手机确认
- `success` - 登录成功
- `expired` - 二维码已过期

### 5. 验证Cookie保存
登录成功后,Cookie会自动保存到:
```
/home/u_topn/TOP_N/backend/cookies/zhihu_{username}.json
```

可以通过SSH检查:
```bash
ssh u_topn@39.105.12.124
ls -l /home/u_topn/TOP_N/backend/cookies/
cat /home/u_topn/TOP_N/backend/cookies/zhihu_{username}.json
```

---

## 如果测试成功,立即部署自动发帖功能

### 一键部署命令
```bash
cd D:\work\code\TOP_N
python deploy_auto_post.py
```

### 部署脚本会自动完成
1. 上传 `zhihu_auto_post.py` 到服务器
2. 在 `app_with_upload.py` 中添加3个新API:
   - `POST /api/zhihu/post` - 发布文章
   - `POST /api/zhihu/answer` - 回答问题
   - `POST /api/articles/publish_to_zhihu/<article_id>` - 发布已生成文章
3. 重启服务

---

## 部署后测试自动发帖

### 测试1: 直接发布文章
```bash
curl -X POST http://39.105.12.124:8080/api/zhihu/post \
  -H "Content-Type: application/json" \
  -d '{
    "username": "你的知乎账号",
    "title": "测试文章标题",
    "content": "这是测试内容...\n\n可以包含多个段落",
    "topics": ["测试"],
    "draft": true
  }'
```

**注意**: 第一次测试建议使用 `"draft": true` 保存为草稿,避免公开发布测试内容

### 测试2: 发布TopN生成的文章
```bash
curl -X POST http://39.105.12.124:8080/api/articles/publish_to_zhihu/1 \
  -H "Content-Type: application/json" \
  -d '{
    "username": "你的知乎账号",
    "topics": ["技术"],
    "draft": false
  }'
```

---

## 可能遇到的问题及解决方案

### Q1: QR登录测试时,状态一直是 waiting
**原因**:
- 可能网络延迟
- 二维码可能已过期

**解决**:
- 刷新页面重新获取二维码
- 检查服务器日志:
```bash
ssh u_topn@39.105.12.124
sudo journalctl -u topn -f | grep -i zhihu
```

### Q2: 扫码成功但状态检测不到
**原因**: 状态检测的关键词可能需要调整

**解决**:
- 查看实时日志,看检测到了什么文本
- 如需调整,修改 `qrcode_login.py` 中的 `status_keywords`

### Q3: Cookie保存失败
**原因**:
- 目录权限问题
- 磁盘空间不足

**解决**:
```bash
ssh u_topn@39.105.12.124
ls -ld /home/u_topn/TOP_N/backend/cookies
# 如果目录不存在或权限不对
mkdir -p /home/u_topn/TOP_N/backend/cookies
chmod 755 /home/u_topn/TOP_N/backend/cookies
```

### Q4: 自动发帖时找不到编辑器元素
**原因**: 知乎界面可能更新,选择器需要调整

**解决**:
- 查看日志中显示的错误信息
- 根据实际页面结构调整 `zhihu_auto_post.py` 中的选择器
- 可以先用 `draft=true` 模式测试

---

## 核心文件位置

### 本地 (D:\work\code\TOP_N)
- `zhihu_auto_post.py` - 自动发帖核心模块
- `deploy_auto_post.py` - 一键部署脚本
- `ZHIHU_AUTO_POST_README.md` - 完整使用文档
- `upload_enhanced_qr.py` - QR登录部署脚本(已运行)

### 服务器 (/home/u_topn/TOP_N/backend)
- `qrcode_login.py` - QR登录模块(已部署增强版)
- `app_with_upload.py` - 主应用(待添加自动发帖API)
- `cookies/zhihu_{username}.json` - Cookie文件(登录后自动生成)
- `zhihu_auto_post.py` - 自动发帖模块(部署后)

---

## 时间线

1. **现在**: 等待测试QR登录
2. **测试成功后**: 运行 `python deploy_auto_post.py`
3. **部署成功后**: 测试自动发帖(建议先用草稿模式)
4. **测试通过后**: 集成到TopN文章生成流程

---

## 联系方式

如遇到任何问题,请提供:
1. 具体的错误信息
2. 服务器日志片段
3. 操作的具体步骤

快速查看日志:
```bash
# 实时查看
ssh u_topn@39.105.12.124
sudo journalctl -u topn -f

# 查看知乎相关日志
sudo journalctl -u topn -n 100 --no-pager | grep -i zhihu
```

---

## 预期结果

### QR登录测试成功后应该看到:
1. 前端显示"登录成功"
2. Cookie文件已保存到服务器
3. 可以通过SSH查看Cookie文件内容

### 自动发帖部署成功后应该有:
1. 3个新的API endpoint可用
2. 可以通过API发布文章到知乎
3. 可以一键发布TopN生成的文章

---

**准备就绪! 请开始测试QR登录功能 🚀**
