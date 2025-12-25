# TOP_N 项目文档索引

> 文档分类整理于 2025-12-25

## 目录结构

```
docs/
├── architecture/    # 架构设计文档 (18个文件)
├── backend/         # 后端实现文档 (7个文件)
├── backup/          # 备份记录 (5个文件)
├── business/        # 业务文档 (5个文件)
├── deployment/      # 部署指南 (20个文件)
├── features/        # 功能特性文档 (24个文件)
├── guides/          # 使用指南 (26个文件)
├── misc/            # 其他杂项文档 (20个文件)
├── platforms/       # 平台集成文档 (21个文件)
├── reports/         # 报告与总结 (56个文件)
└── temp/            # 临时文件 (2个文件)
```

---

## 分类说明

### architecture/ - 架构设计
系统架构、重构计划、代码结构设计相关文档。

| 文件 | 说明 |
|------|------|
| REFACTORING_PLAN.md | 重构计划 |
| CONCURRENT_ARCHITECTURE.md | 并发架构设计 |
| ARCHITECTURE_CLEANUP_COMPLETE_REPORT.md | 架构清理报告 |
| SERVICE_USAGE_EXAMPLES.md | 服务层使用示例 |

### backend/ - 后端实现
后端代码实现、API设计相关文档。

| 文件 | 说明 |
|------|------|
| IMPLEMENTATION_SUMMARY.md | 实现总结 |
| DEPLOYMENT_GUIDE.md | 部署指南 |
| VERIFICATION_CHECKLIST.md | 验证清单 |

### deployment/ - 部署运维
服务器部署、运维监控相关文档。

| 文件 | 说明 |
|------|------|
| DEPLOYMENT_GUIDE.md | 部署指南 |
| PRODUCTION_MONITORING_GUIDE.md | 生产环境监控指南 |
| SERVER_DEPLOYMENT_GUIDE.md | 服务器部署指南 |
| SSH免密登录配置完成.md | SSH配置说明 |

### features/ - 功能特性
各功能模块的设计与实现文档。

| 文件 | 说明 |
|------|------|
| Cookie登录功能使用说明.md | Cookie登录功能 |
| QR_LOGIN_FLOW.md | 扫码登录流程 |
| PUBLISH_HISTORY_FEATURE.md | 发布历史功能 |
| RBAC权限系统设计.md | 权限系统设计 |
| PROMPT_TEMPLATE_EXAMPLES_DESIGN.md | 提示词模板设计 |

### platforms/ - 平台集成
各内容平台(知乎、CSDN等)的集成文档。

| 文件 | 说明 |
|------|------|
| 多平台发布器架构设计.md | 多平台架构设计 |
| ZHIHU_AUTO_POST_README.md | 知乎自动发布说明 |
| CSDN发布器实现完成总结.md | CSDN发布器实现 |
| 知乎验证码自动化方案2025.md | 知乎验证码方案 |

### guides/ - 使用指南
开发、使用、配置等操作指南。

| 文件 | 说明 |
|------|------|
| SYSTEM_USER_GUIDE.md | 系统用户指南 |
| QUICK_REFERENCE.md | 快速参考 |
| DEVELOPMENT_WORKFLOW.md | 开发工作流 |
| TESTING_GUIDE.md | 测试指南 |
| 环境变量配置说明.md | 环境变量配置 |

### reports/ - 报告总结
各类修复报告、问题分析、项目总结。

| 文件 | 说明 |
|------|------|
| ADMIN_IMPLEMENTATION_COMPLETE.md | 管理后台实现完成 |
| FINAL_TESTING_REPORT.md | 最终测试报告 |
| BUG_FIX_REPORT_*.md | Bug修复报告 |
| ISSUE_REPORT_*.md | 问题报告 |

### business/ - 业务文档
产品特性、业务相关文档。

| 文件 | 说明 |
|------|------|
| 产品特性文档.md | 产品功能特性 |
| *.docx | 业务宣传资料 |

### misc/ - 其他文档
配置、状态、临时性文档。

### temp/ - 临时文件
测试文件、临时数据。

---

## 快速导航

- **新手入门**: `guides/SYSTEM_USER_GUIDE.md`
- **部署项目**: `deployment/DEPLOYMENT_GUIDE.md`
- **架构了解**: `architecture/REFACTORING_PLAN.md`
- **功能开发**: `features/` 目录
- **问题排查**: `reports/` 目录

---

## 文档维护规范

1. **新功能文档** → `features/`
2. **部署相关** → `deployment/`
3. **Bug修复报告** → `reports/`
4. **使用说明** → `guides/`
5. **平台集成** → `platforms/`
6. **临时文件** → `temp/` (定期清理)
