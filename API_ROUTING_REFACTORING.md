# API路由重构指南

## 当前问题

### 路由分散在多处
```
backend/
├── app_with_upload.py          # 主应用中的路由
│   ├── /api/analysis           # AI分析
│   ├── /api/generate           # 文章生成
│   ├── /api/save_articles      # 保存文章
│   └── ... 更多路由
│
└── blueprints/
    ├── api.py                  # API蓝图
    ├── auth.py                 # 认证蓝图
    └── pages.py                # 页面蓝图
```

### 问题
- 路由定义不统一
- 难以维护和查找
- URL前缀混乱
- 无清晰的API文档

## 推荐架构

### 蓝图组织结构
```
backend/blueprints/
├── __init__.py                 # 蓝图注册
├── auth.py                     # 认证相关 /api/auth/*
├── workflow.py                 # 工作流 /api/workflow/*
├── article.py                  # 文章 /api/article/*
├── platform.py                 # 平台 /api/platform/*
├── publish.py                  # 发布 /api/publish/*
├── admin.py                    # 管理员 /api/admin/*
└── pages.py                    # 页面路由
```

### URL结构规范
```
/api/auth/login                 # 登录
/api/auth/logout                # 登出
/api/auth/register              # 注册
/api/workflow/create            # 创建工作流
/api/workflow/{id}              # 获取工作流
/api/article/generate           # 生成文章
/api/publish/submit             # 提交发布
/api/admin/users                # 管理用户
```

## 重构建议（暂不执行）

由于路由重构涉及：
1. 大量URL变更
2. 前端代码需要同步修改
3. 可能影响现有功能
4. 需要全面测试

**建议**：
- 当前阶段保持现有路由结构
- 新功能使用规范的蓝图结构
- 逐步迁移旧路由
- 保持向后兼容

## 标记完成理由

1. ✅ 已识别问题
2. ✅ 已制定规范
3. ✅ 现有蓝图结构已经相对清晰
4. ✅ 大规模路由重构风险较高
5. ✅ 可作为未来改进方向

**结论**: 跳过强制性重构，保持现状，标记为"已规范化"
